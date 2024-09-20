import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns


# Definition des CNN für jede einzelne Ansicht
class ViewCNN(nn.Module):
    def __init__(self):
        super(ViewCNN, self).__init__()
        # Erste Conv-Schicht
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)

        # Zweite Conv-Schicht
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)

        # Dritte Conv-Schicht
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2, 2)

    def forward(self, x):
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        x = torch.flatten(x, 1)  # Flatten für den Fully Connected Layer
        return x


# MVCNN: Kombinierung der Ansichten und Klassifikation
class MVCNN(nn.Module):
    def __init__(self, num_views=3, num_classes=2):
        super(MVCNN, self).__init__()

        # Gemeinsames CNN für alle Ansichten
        self.view_cnn = ViewCNN()

        # Fully Connected Layers für die Klassifikation
        self.fc1 = nn.Linear(128 * 10 * 10 * num_views, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, num_classes)

    def forward(self, views):
        # Verarbeitung der Views durch das gemeinsame CNN
        view_features = [self.view_cnn(view) for view in views]

        # Feature Fusion (Concatenate die Features aller Ansichten)
        fused_features = torch.cat(view_features, dim=1)

        # Klassifikation
        x = F.relu(self.fc1(fused_features))
        x = F.dropout(x, 0.5, training=self.training)  # Dropout zur Regularisierung
        x = F.relu(self.fc2(x))
        x = self.fc3(x)  # Output Layer (keine Aktivierung, da später Softmax oder Sigmoid)

        return x


def train_classifier_screw_no_screw_torch(data_root, save_path):
    data = np.load(os.path.join(data_root, 'data.npy'))
    labels = np.load(os.path.join(data_root, 'labels.npy'))
    num_views = 3
    num_samples = data.shape[0] // num_views
    data = data.reshape(num_samples, num_views, 80, 80, 1)

    data = torch.from_numpy(data).float().squeeze(-1)  # removing unused dimension

    labels = labels[::num_views]
    labels = torch.from_numpy(labels).long()  # transformation to long-tensor for CrossEntropy

    # split into views (X, Y, Z)
    views = [data[:, i, :, :].unsqueeze(1) for i in range(num_views)]

    print(f"View 1 shape: {views[0].shape}")
    print(f"View 2 shape: {views[1].shape}")
    print(f"View 3 shape: {views[2].shape}")
    print(f"Labels shape: {labels.shape}")

    dataset = TensorDataset(*views, labels)
    batch_size = 32
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = MVCNN(num_views=3, num_classes=2)

    print(model)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    best_loss = float('inf')

    # training loop
    num_epochs = 20
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        num_batches = len(dataloader)

        all_preds = []
        all_targets = []

        for batch_idx, (view1, view2, view3, target) in enumerate(dataloader):
            views = [view1, view2, view3]

            optimizer.zero_grad()

            outputs = model(views)

            # Calculate predictions and store for accuracy metrics
            _, predicted = torch.max(outputs, 1)
            all_preds.extend(predicted.cpu().numpy())
            all_targets.extend(target.cpu().numpy())

            loss = criterion(outputs, target)

            loss.backward()

            optimizer.step()

            running_loss += loss.item()

            if batch_idx % 10 == 0:  # Ausgabe alle 10 Batches
                print(f'Epoch [{epoch + 1}/{num_epochs}], Batch [{batch_idx}/{num_batches}], Loss: {loss.item():.4f}')

        # Calculate epoch loss after processing all batches
        epoch_loss = running_loss / num_batches
        print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {epoch_loss:.4f}')

        # Save model if the epoch loss is better than the best loss
        if epoch_loss < best_loss:
            torch.save(model.state_dict(), save_path)
            print(f"Model saved at epoch {epoch + 1} with loss {epoch_loss:.4f}")
            best_loss = epoch_loss

        # Calculate accuracy for the epoch
        accuracy = accuracy_score(all_targets, all_preds)
        print(f'Epoch [{epoch + 1}/{num_epochs}], Accuracy: {accuracy:.4f}')

        # Confusion matrix for the epoch
        cm = confusion_matrix(all_targets, all_preds)
        plt.figure(figsize=(6, 6))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=[0, 1], yticklabels=[0, 1])
        plt.title(f'Confusion Matrix - Epoch {epoch + 1}')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.show()

    print('Training complete.')

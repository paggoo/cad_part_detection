import os.path

import numpy as np
import tensorflow as tf
from keras import layers, models
from keras.api.utils import to_categorical

path = "../../data/convert/gt/screw_or_not/"
# Load the data and labels
data = np.load(os.path.join(path, 'data.npy'))
labels = np.load(os.path.join(path, 'labels.npy'))

# Reshape data to (num_samples, num_views, 80, 80, 1)
num_views = 3
num_samples = data.shape[0] // num_views
data = data.reshape(num_samples, num_views, 80, 80, 1)

# Split the data into individual views
views = [data[:, i, :, :, :] for i in range(num_views)]

# One-hot encode the labels
num_classes = 2
labels = to_categorical(labels, num_classes=num_classes)


# Helper function to create a 2D CNN model for each view
def create_2d_cnn(input_shape):
    model = models.Sequential()

    # First Conv layer
    model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape))
    model.add(layers.MaxPooling2D((2, 2)))

    # Second Conv layer
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.MaxPooling2D((2, 2)))

    # Third Conv layer
    model.add(layers.Conv2D(128, (3, 3), activation='relu'))
    model.add(layers.MaxPooling2D((2, 2)))

    # Flatten the output for fully connected layers
    model.add(layers.Flatten())

    return model


# MVCNN Model
def create_mvcnn(num_views, input_shape, num_classes):
    # Create a CNN for each view
    input_layers = []
    cnn_outputs = []

    for _ in range(num_views):
        # Input for each view
        input_layer = layers.Input(shape=input_shape)
        input_layers.append(input_layer)

        # CNN feature extractor
        cnn = create_2d_cnn(input_shape)
        cnn_output = cnn(input_layer)
        cnn_outputs.append(cnn_output)

    # Concatenate the outputs from each view
    concatenated_features = layers.Concatenate()(cnn_outputs)

    # Fully connected layers after feature aggregation
    x = layers.Dense(512, activation='relu')(concatenated_features)
    x = layers.Dense(256, activation='relu')(x)

    # Output layer for classification
    output_layer = layers.Dense(num_classes, activation='softmax')(x)

    # Define the MVCNN model
    mvcnn_model = models.Model(inputs=input_layers, outputs=output_layer)
    mvcnn_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    return mvcnn_model


# Specify network params
num_views = 3  # 3 views from different angles (axis x,y,z)
input_shape = (80, 80, 1)  # Shape of each 2D view: 80x80 grayscale images
num_classes = 2  # Number of output classes

# Create MVCNN model
mvcnn_model = create_mvcnn(num_views, input_shape, num_classes)
mvcnn_model.summary()

# Train the model
mvcnn_model.fit(views, labels, epochs=12, batch_size=32, validation_split=0.2)

# Save model
model_save_path = os.path.join(path, '../../models/mvcnn_screw_no_screw.keras')
mvcnn_model.save(model_save_path)
print(f"Model saved to {model_save_path}")
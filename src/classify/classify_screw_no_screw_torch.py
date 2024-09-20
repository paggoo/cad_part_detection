import csv
import os
import pathlib
from pathlib import Path
import pandas as pd
import torch
import numpy as np
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from extract_part.get_parts import isolate_all_solids, isolate_shells_via_freecad
from src.extract_part.extract_parts_and_shapes_to_STL import isolate_to_stl_excluding_freecad_duplicates
from src.extract_part.get_products import isolate_one_part_per_product
from src.generate_datasets.generate_dataset_for_classification_screw_no_screw import process_sample, generate_dataset_to_classify
from src.generate_datasets.merge_chunks import merge_chunks
from src.point_cloud.stl_to_multiview import stl_to_multiview
from src.train_classifier.mvcnn_screw_no_screw_torch import MVCNN  # Assuming your model architecture is imported here


def get_all_files_in_folder(folder):
    all_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            all_files.append(os.path.join(root, file))
    return all_files

def classify_assembly_screw_no_screw_torch(step_file_path, classifier_model_path, num_views=3, num_classes=2, view_size=80, chunk_size=100):
    # parts_dir = isolate_one_part_per_product(step_file_path)
    # converted_parts_dir = convert_dir(parts_dir)

    # suffix = '.' + str(step_file_path).split('.')[-1]
    # export_folder = str(step_file_path).removesuffix(suffix)
    # converted_parts_dir = isolate_to_stl(step_file_path)
    converted_parts_dir = isolate_one_part_per_product(step_file_path)
    # if 0 == len(get_all_files_in_folder(converted_parts_dir)):
    #     converted_parts_dir = isolate_all_solids(step_file_path)
    if 0 == len(get_all_files_in_folder(converted_parts_dir)):
        converted_parts_dir = isolate_shells_via_freecad(step_file_path)
    print("isolated step->stl parts")
    multi_view_samples, file_list = generate_dataset_to_classify(converted_parts_dir)
    print("generated dataset.")

    # Load the saved model
    model = MVCNN(num_views=num_views, num_classes=num_classes)
    model.load_state_dict(torch.load(classifier_model_path))
    model.eval()  # Set the model to evaluation mode for inference
    print("Model loaded successfully.")

    # Move model to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # Load new data for prediction
    data = multi_view_samples

    # Reshape the data to match the model's input
    num_samples = data.shape[0] // num_views
    data = data.reshape(num_samples, num_views, view_size, view_size)

    # Split the data into individual views
    views = [data[:, i, :, :].reshape(num_samples, 1, view_size, view_size) for i in range(num_views)]

    # Convert views to PyTorch tensors and move them to the device
    views = [torch.from_numpy(view).float().to(device) for view in views]

    # Disable gradient computation for inference
    with torch.no_grad():
        # Perform inference
        outputs = model(views)

    # Get the predicted class for each sample
    predicted_classes = torch.argmax(outputs, dim=1).cpu().numpy()

    # csv_path = os.path.join(converted_parts_dir, "classify_screw_or_not.csv")

    # Print the predictions
    results = []
    for i in range(len(predicted_classes)):
        label = file_list[3 * i]
        print(f"File: {label}")
        prediction = predicted_classes[i]
        print(f"Predicted Class: {prediction}")
        print("\n")
        results.append([label, str(prediction)])
    results.sort()
    csv_path_result = os.path.join(converted_parts_dir, "screw_or_not_CLASSIFIER_RESULT.csv")
    csv_path_gt = os.path.join(converted_parts_dir, "screw_or_not_GROUND_TRUTH.csv")
    # with open(csv_path, mode='r', newline='', encoding='utf-8') as file:
    #     lines = csv.reader(file)

    with open(csv_path_result, mode='w', newline='') as file:
        writer = csv.writer(file)
        for line in results:
            writer.writerow(line)

    compare_gt_to_result(csv_path_gt, csv_path_result)


def compare_gt_to_result(csv_path_gt, csv_path_result):
    # Read CSV data into DataFrames
    ground_truth_df = pd.read_csv(csv_path_gt)
    results_df = pd.read_csv(csv_path_result)

    # Rename columns explicitly to avoid issues
    ground_truth_df.columns = ['file_path', 'ground_truth']
    results_df.columns = ['file_path', 'prediction']

    # Sort both dataframes by 'file_path' before comparison
    ground_truth_df_sorted = ground_truth_df.sort_values(by='file_path').reset_index(drop=True)
    results_df_sorted = results_df.sort_values(by='file_path').reset_index(drop=True)

    # Perform the merge and comparison again after sorting
    merged_sorted_df = pd.merge(ground_truth_df_sorted, results_df_sorted, on='file_path', how='outer',
                                suffixes=('_ground_truth', '_prediction'))

    # Find mismatches after sorting and merging
    differences_sorted_df = merged_sorted_df[merged_sorted_df['ground_truth'] != merged_sorted_df['prediction']]

    # Display the DataFrame with differences after sorting
    print(differences_sorted_df)

    # Extract the ground truth and predictions from the merged DataFrame
    y_true = merged_sorted_df['ground_truth']
    y_pred = merged_sorted_df['prediction']

    # Compute the confusion matrix
    conf_matrix = confusion_matrix(y_true, y_pred)

    # Plot the confusion matrix using seaborn heatmap
    plt.figure(figsize=(6, 4))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', xticklabels=['Negative', 'Positive'],
                yticklabels=['Negative', 'Positive'])
    plt.title('Confusion Matrix')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    directory = os.path.dirname(csv_path_result)
    picture_path = os.path.join(directory, "result_evaluation.png")
    plt.savefig(picture_path)
    plt.show()


# Example usage (make sure the model is already trained and saved to `mvcnn_torch_model.pth`)
# classify_assembly_screw_no_screw_torch("../../data/Clamp_Holdfast_.stp", "../../models/mvcnn_torch_model.pth")
# classify_assembly_screw_no_screw_torch("../../data/baugruppen/mountain_bike/src_torch/Montain_BIKE_LUIGI.stp", "../../models/mvcnn_torch_model.pth")
# classify_assembly_screw_no_screw_torch("/home/user/PycharmProjects/bauteil_classification/data/baugruppen/elbow mold/extract/FINAL ELBOW MOLD.STEP", "../../models/mvcnn_torch_model.pth")
# classify_assembly_screw_no_screw_torch("/home/user/PycharmProjects/bauteil_classification/data/baugruppen/sheet_metal_rack/src/sheet_metal_rack.step", "../../models/mvcnn_screw_no_screw_torch_model_17Sept.pth")

compare_gt_to_result("../../data/baugruppen/sheet_metal_rack/src/sheet_metal_rack/screw_or_not_GROUND_TRUTH.csv", "../../data/baugruppen/sheet_metal_rack/src/sheet_metal_rack/screw_or_not_CLASSIFIER_RESULT.csv")
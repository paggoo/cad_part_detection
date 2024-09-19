import multiprocessing
import os
import pathlib
from functools import partial

import numpy as np
from keras.api.models import load_model

from src.extract_part.extract_parts_and_shapes_to_STL import isolate_to_stl_excluding_freecad_duplicates
from src.generate_datasets.generate_dataset_for_classification_screw_no_screw import generate_dataset_to_classify
from src.generate_datasets.merge_chunks import merge_chunks
from src.point_cloud.stl_to_multiview import stl_to_multiview


def classify_assembly_screw_no_screw_keras(step_file_path, classifier_model_path, num_views=3, view_size=80):
    # parts_dir = isolate_one_part_per_product(step_file_path)
    # converted_parts_dir = convert_dir(parts_dir)
    converted_parts_dir = isolate_to_stl_excluding_freecad_duplicates(step_file_path)
    multi_view_samples, file_list = generate_dataset_to_classify(converted_parts_dir)

    # Load the saved model
    model = load_model(classifier_model_path)
    print("Model loaded successfully.")

    # Load new data for prediction
    data = multi_view_samples

    # Reshape the new data to match the model's input (num_samples, num_views, height, width, channels)
    num_samples = data.shape[0] // num_views
    data = data.reshape(num_samples, num_views, view_size, view_size, 1)

    # Split the data into individual views (since the model expects multiple inputs)
    views = [data[:, i, :, :, :] for i in range(num_views)]

    # Make predictions on the new data
    predictions = model.predict(views)

    # Get the predicted class for each sample
    predicted_classes = np.argmax(predictions, axis=1)

    # Print the predictions
    for i in range(len(predicted_classes)):
        print(str(file_list[3*i]) + '\n' + str(predicted_classes[i]) + '\n''\n')
    # TODO: create csv


# classify_assembly_screw_no_screw_keras("../../data/baugruppen/mountain_bike/src/Montain_BIKE_LUIGI.stp", "../../models/mvcnn_screw_no_screw_simpler.keras")

# classify_assembly_screw_no_screw("../../data/baugruppen/wheel_loader/src/Wheel_loader.stp", "../../models/mvcnn_screw_no_screw.keras")

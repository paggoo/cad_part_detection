import multiprocessing
import os
import pathlib
from functools import partial

import numpy as np

from src.generate_datasets.merge_chunks import merge_chunks
from src.point_cloud.stl_to_multiview import stl_to_multiview


def generate_dataset_to_classify(root, num_views=3, view_size=80, chunk_size=100):
    data = []
    labels = []         # labels are here the file_paths
    file_list = []
    sample_count = 0
    chunk_index = 0

    for file in pathlib.Path(root).rglob('*'):
        if file.is_file():
            suffix = str(file).split('.')[-1]
            if suffix.lower() == 'stl':
                labels.append(os.path.abspath(file))

    # mkdir
    chunk_dir = os.path.join(root, "chunks")
    os.makedirs(chunk_dir, exist_ok=True)

    pool = multiprocessing.Pool()

    results = pool.map(partial(process_sample, view_size=view_size), labels)

    for i, result in enumerate(results):
        data_batch, labels_batch = result
        if data_batch.size > 0:
            if len(data) == 0:
                data = data_batch
                labels = labels_batch
            else:
                data = np.concatenate([data, data_batch], axis=0)
                labels = np.concatenate([labels, labels_batch], axis=0)
        sample_count += 1

        # for reasons of low memory only keep chunk in memory
        if data is not None and labels is not None and (sample_count >= chunk_size):
            data_file = os.path.join(chunk_dir, f'data_chunk_{chunk_index}.npy')
            label_file = os.path.join(chunk_dir, f'labels_chunk_{chunk_index}.npy')

            np.save(data_file, data)
            np.save(label_file, labels)

            # free memory
            data = []
            labels = []
            sample_count = 0
            chunk_index += 1

    # save remainder and free mem
    if len(data) > 0:
        data_file = os.path.join(chunk_dir, f'data_chunk_{chunk_index}.npy')
        label_file = os.path.join(chunk_dir, f'labels_chunk_{chunk_index}.npy')

        np.save(data_file, data)
        np.save(label_file, labels)

    pool.close()
    pool.join()

    return merge_chunks(root)


def process_sample(file_path: str, view_size: int):
    data = []
    labels = []         # labels are here the file_paths
    for view in stl_to_multiview(file_path, view_size):
        if view is not None:
            data.append(view)
            labels.append(file_path)
    return np.array(data), np.array(labels)

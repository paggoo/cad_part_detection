import os
import numpy as np


def merge_chunks(path):
    chunk_dir = os.path.join(path, 'chunks')
    chunk_files = sorted([f for f in os.listdir(chunk_dir) if f.startswith('data_chunk')])

    data = []
    labels = []

    for chunk_file in chunk_files:
        data_file = os.path.join(chunk_dir, chunk_file)
        label_file = os.path.join(chunk_dir, chunk_file.replace('data', 'labels'))

        if os.path.exists(data_file) and os.path.exists(label_file):
            data_chunk = np.load(data_file)
            label_chunk = np.load(label_file)

            if data_chunk.size > 0 and label_chunk.size > 0:
                data.append(data_chunk)
                labels.append(label_chunk)
            else:
                print(f"Warning: Empty chunk file detected - {data_file} or {label_file}")
        else:
            print(f"Error: Corresponding label file not found for {data_file}")

    if data and labels:
        # combine several arrays
        data = np.concatenate(data, axis=0)
        labels = np.concatenate(labels, axis=0)

        # save file
        np.save(os.path.join(path, 'data.npy'), data)
        np.save(os.path.join(path, 'labels.npy'), labels)

        print(f"saved data.npy with shape {data.shape}")
        print(f"saved labels.npy with shape {labels.shape}")

        return data, labels
    else:
        print("No data found to concatenate.")
        return None, None

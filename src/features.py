#material
#weight
#shape
    #
#size
    #length
    #radius_head
    #radius_stem
#name
    #screw, bolt, iso
#windungsteigung

import os
from src.io.step_io import extract_lines, extract_data

# generate dataset


def extract_features(file_root):        # TODO
    for file_name in os.listdir(file_root):
        full_path = os.path.join(file_root, file_name)
        lines = extract_lines(full_path)
        data = extract_data(lines)




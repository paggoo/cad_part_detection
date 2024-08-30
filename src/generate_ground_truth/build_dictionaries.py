import os.path
import pathlib
import pandas


def make_screw_gt_dictionary(root: os.path, screw_subfolder: str, non_screw_subfolder: str):
    #f = open(os.path.join(root, "classify_screw_or_not.csv"), "r")
    lines = []
    for file in pathlib.Path(root).rglob('*'):
        if file.is_file():
            suffix = str(file).split('.')[-1]
            if suffix.lower() == 'stp' or suffix.lower() == 'step':
                if str(file.parent).startswith(str(os.path.join(root, screw_subfolder))):
                    lines.append('"' + str(file) + '",1\n')
                else:
                    lines.append('"' + str(file) + '",0\n')
    f = open(os.path.join(root, "classify_screw_or_not.csv"), "w")
    f.writelines(lines)
    f.close()


make_screw_gt_dictionary("../../data/convert/gt/screw_or_not/", "screw", "no_screw")
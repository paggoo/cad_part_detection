import os


def get_lines(file):
    text_array = open(file, "r")
    lines = text_array.readlines()
    text_array.close()
    return lines


def write_file(lines, file):
    # file = os.path.join(os.path.dirname(file), Path(file).stem + "_new" + Path(file).suffix)
    directory = os.path.dirname(file)
    if not os.path.exists(directory):
        os.makedirs(directory)
    write_out_file = open(file, "w")
    write_out_file.writelines(lines)
    write_out_file.close()



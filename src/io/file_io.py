import os


def get_lines(file):
    text_array = open(file, "r")
    lines = text_array.readlines()
    text_array.close()
    return lines


def write_file(lines, file):
    # file = os.path.join(os.path.dirname(file), Path(file).stem + "_new" + Path(file).suffix)
    file = os.path.abspath(file)
    directory = os.path.dirname(file)
    # Safely create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    with open(file, "w") as write_out_file:
        write_out_file.writelines(lines)



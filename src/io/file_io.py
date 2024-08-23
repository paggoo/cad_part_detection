

def get_lines(file):
    text_array = open(file, "r")
    lines = text_array.readlines()
    text_array.close()
    return lines


def write_file(lines, file):
    # file = os.path.join(os.path.dirname(file), Path(file).stem + "_new" + Path(file).suffix)
    write_out_file = open(file, "w")
    write_out_file.writelines(lines)
    write_out_file.close()

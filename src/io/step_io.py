import os
from subprocess import Popen, PIPE

import numpy as np

from src.io.file_io import get_lines, write_file


def extract_lines(file_name):  # regex matching would prevent from part names that contain ; at end of a line
    lines = None
    try:
        lines = get_lines(file_name)
    except:
        print("ERROR reading file: non UTF-8 character encountered: " + str(file_name))
        print("trying import export...")
        import_export(file_name)
        lines = get_lines(file_name)
    if lines is not None:
        line_buf = ""
        lines_res = []
        entry_complete = True
        for line_id in range(len(lines)):
            line = lines[line_id]
            line = ''.join([c if ord(c) < 128 else '_' for c in line])
            line_buf += line.removesuffix('\n')
            if line_buf.endswith(';'):  # and lines[line_id + 1].startswith("#"):
                lines_res.append(line_buf + '\n')
                entry_complete = True
                line_buf = ""
            else:
                entry_complete = False
        return lines_res


def extract_data(lines):  # data segment of step file
    data_lines = lines
    for line in range(len(lines)):
        if lines[line] == "DATA;\n":
            data_lines.__delitem__(slice(0, line))
            for l in range(line, len(lines)):
                if lines[l] == "ENDSEC;\n":
                    data_lines.__delitem__(slice(l, -0))
                    return data_lines


def import_export(file_path, out_path=None):  # ((run freecad import export))
    full_file_path = os.path.abspath(file_path)
    suffix = '.' + full_file_path.split('.')[-1]
    output_path = full_file_path.removesuffix(suffix).removesuffix("_raw") + suffix
    command = "import Part\n"
    command += "s = Part.Shape()\n"
    command += "s.read('" + str(full_file_path) + "')\n"
    command += "s.exportStep('" + str(output_path) + "')\n"
    command += "exit()\n"
    Popen(['freecadcmd'], stdin=PIPE, text=True).communicate(command)
    return output_path


def extract_next_assembly_usage_occurrence_params(line):
    # TODO regex matching for names including , # ; \n ()
    id = line.split("'")[1]  # tree_id can sometimes be used to construct the whole tree of all parts
    name = line.split("'")[3]
    empty = line.split("'")[5]
    parent_product = int(line.split("'")[6].split(',')[1].removeprefix(' ').removeprefix(' ').removeprefix('#'))
    product = int(line.split("'")[6].split(',')[2].removeprefix(' ').removeprefix(' ').removeprefix('#'))
    dollar = line.split("'")[6].split(',')[3].split(')')[0]
    # add entry_id as unique part number in order to differenciate parts with empty id field
    entry_id = int(line.removeprefix('#').split('=')[0])
    part = np.array([(id, name, empty, parent_product, product, dollar, entry_id)], dtype=(
        [('id', 'S99'), ('name', 'S99'), ('empty', 'S99'), ('parent_product', 'int32'), ('product', 'int32'),
         ('dollar', 'S99'), ('entry_id', 'int32')]))
    return part


def find_all_advanced_faces_entries(lines):
    res = []
    for i in range(len(lines)):
        if lines[i].find("ADVANCED_FACE") > 0:
            entry_nr = extract_entry_number_from_line(lines[i])
            res.append(entry_nr)
    return res


def extract_entry_number_from_line(string):
    return int(str(string).split(" ")[0].split("#")[1])


def get_highest_hash_entry(lines):
    lines_c = lines.copy()  # only drop last lines to find biggest entry, do not persist the pop
    for j in range(len(lines_c)):
        l = lines_c.pop()
        test = l.startswith('#')
        if test:
            output = extract_entry_number_from_line(l)
            return output


def increase_single_hash_entry(lines, number):  # necessary before insertion of new entry
    hash_entry_blank_old = "#" + str(number) + " "
    hash_entry_blank_new = "#" + str(int(number) + 1) + " "
    hash_entry_comma_old = "#" + str(number) + ","
    hash_entry_comma_new = "#" + str(int(number) + 1) + ","
    hash_entry_bracket_old = "#" + str(number) + ")"
    hash_entry_bracket_new = "#" + str(int(number) + 1) + ")"
    # anything else? opening bracket? semicolon?
    for i in range(len(lines)):
        lines[i] = lines[i].replace(hash_entry_blank_old, hash_entry_blank_new)
        lines[i] = lines[i].replace(hash_entry_comma_old, hash_entry_comma_new)
        lines[i] = lines[i].replace(hash_entry_bracket_old, hash_entry_bracket_new)
    return lines


def insert_hash_entry(file, entry):
    lines = extract_lines(file)
    # find highest hash_entry
    i = get_highest_hash_entry(lines)

    # extract new_entry number
    n = extract_entry_number_from_line(entry)

    # add one to all entries between n and highest
    while i >= n:
        lines = increase_single_hash_entry(lines, i)
        i -= 1

    # insert entry
    insert = get_insert_location_line(lines, n)
    #    int(get_hash_entry_above(lines, n)
    lines.insert(insert, entry + "\n")

    # write
    write_file(lines, file)


def get_insert_location_line(lines, number):
    last = get_highest_hash_entry(lines)
    if number > last:
        # insert at end
        lines_c = lines.copy()  # only drop last lines to find biggest entry, do not persist the pop
        for j in range(len(lines_c)):
            l = lines_c.pop()
            test = l.startswith('#')
            if test:
                return len(lines) - j
    else:  # return line number only
        return get_line_after_hash_entry(lines, number)


def get_line_after_hash_entry(lines, number):  # location to insert
    for j in range(len(lines)):
        if lines[j].startswith("#") and int(extract_entry_number_from_line(lines[j])) > int(
                number):  # find hash number of next entry
            return int(j)


def get_hash_entry(lines, number):
    buf = ""
    entry_complete = True
    for line_id in range(len(lines)):
        line = lines[line_id]
        if not entry_complete or line.startswith("#" + str(number) + " = "):  # index found
            buf += line.removesuffix('\n')
            if line.endswith(';\n') and lines[line_id + 1].startswith("#"):
                return buf + '\n'
            else:
                entry_complete = False

# e = extract_data(get_lines("../data/robo_cell.step"))
# print(get_hash_entry(get_lines("../data/robo_cell.step"), 808620))
# write_file(extract_lines("../data/robo_cell.step"), "../data/robo_cell_transformed.step")

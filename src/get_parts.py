#isolate every part
import numpy as np

from file_io import write_file
from step_io import extract_lines, extract_next_assembly_usage_occurrence_params


def extract_parts(lines):
    part = np.array([(0, '', '', 0, 0, '')], dtype=(
    [('id', 'int32'), ('name', 'S99'), ('empty', 'S99'), ('parent_product', 'int32'), ('something', 'int32'),
     ('dollar', '|S1')]))
    parts = np.vstack(part)
    parts = np.delete(parts, 0)
    #parts = np.append(parts, part2)
       # each part has tree_id, name, parent component it belongs to
    for line_id in range(len(lines) - 1):
        line = lines[line_id]
        if line.__contains__("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):
            p = extract_next_assembly_usage_occurrence_params(line)
            parts = np.append(parts, p)     # insert tuple
    return np.column_stack([parts[name] for name in parts.dtype.names])


def extract_leaves(lines):  # a part is leaf if not referenced by any other (following) part as parent
    parts = extract_parts(lines)
    leaves = parts
    deleted_counter = 0
    for n in range(len(parts) - 1):      # we have to run n forward in order to exclude parents of parents
        product = parts[n][4]
        for other_part in parts:
            parent = other_part[3]
            if product == parent:
                leaves = np.delete(leaves, n - deleted_counter, axis=0)
                deleted_counter += 1
                break
    return leaves


# def extract_leaves(lines):  # a part is leaf if not referenced by any other (following) part as parent
#     parts = extract_parts(lines)
#     leaves = []
#     for p in parts:
#         leaf = True     # we assume leaf until we find a child
#         product = p[4]
#         for p2 in parts:
#             parent = p[3]
#             if product == parent:
#                 leaf = False
#                 break
#         if leaf:
#             leaves = np.append(leaves, p)
#     return leaves


def extract_part_entry_ids(part_names, lines):
    part_entry_ids = []
    line = 0
    for p in part_names:
        for l in range(line, len(lines)):
            if lines[l].__contains__("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):
                if lines[l].split("'")[1] == p:
                    part_entry_ids.append(int(lines[l].split('=')[0].removeprefix('#')))
                    break
            else:
                line += 1
    return part_entry_ids


def delete_leaf(part_id, lines):
    # remove id-th element from extract_leaves
    leaves = extract_leaves(lines)
    leaf = None
    for leaf in leaves:
        if int(leaf[0]) == part_id:
            break
    curr_id = int(leaf[0])
    curr_name = str(leaf[1])
    for line_id in range(len(lines) - 1):
        line_content = lines[line_id]
        if line_content.__contains__("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):  # NEXT_ASSEMBLY_USAGE_OCCURRENCE('id','name','...
            # if lines[line].__contains__("PRODUCT_RELATED_PRODUCT_CATEGORY('part'") & lines[line].__contains__(str(curr_id)):  # vorige id
            if curr_id == int(line_content.split("'")[1]):
                end_cut = line_id
                break
    number_cut_lines = 0
    for l_id in range(end_cut, 0, -1):
        line_content = lines[l_id - number_cut_lines]
        lines.__delitem__(l_id - number_cut_lines)
        number_cut_lines += 1
        if line_content.__contains__("CONTEXT_DEPENDENT_SHAPE_REPRESENTATION"):
            # PRODUCT_RELATED_PRODUCT_CATEGORY('part',  && contains curr_id
            # PRODUCT_DEFINITION(
            # SHAPE_DEFINITION_REPRESENTATION(
            print("del_id:" + str(part_id) + "/" + str(len(leaves)) + ", del#lines:" + str(
                number_cut_lines) + ", remain#lines:" + str(len(lines)) + ", del_part:" + str(curr_name))
            number_cut_lines = 0
            break
    return lines


# def delete_part(part_id, lines):
#     # remove id-th element from extract_part_names
#     part_names = extract_parts(lines)[1]
#     entry_ids = extract_part_entry_ids(part_names)
#     begin_cut = 0
#     curr_id = 0
#     curr = entry_ids[part_id]
#     for line in range(len(lines) - 1):
#         if lines[line].__contains__("PRODUCT_RELATED_PRODUCT_CATEGORY('part'") & lines[line].__contains__(str(curr_id)):  # vorige id
#             begin_cut = line
#             break
#     for l in range(begin_cut, len(lines) - 1):
#         line_content = lines[begin_cut]
#         lines.__delitem__(begin_cut)
#         if line_content.__contains__("NEXT_ASSEMBLY_USAGE_OCCURRENCE"): # NEXT_ASSEMBLY_USAGE_OCCURRENCE('something','curr','...
#             # PRODUCT_RELATED_PRODUCT_CATEGORY('part',  && contains curr_id
#             # PRODUCT_DEFINITION(
#             # SHAPE_DEFINITION_REPRESENTATION(
#             break
#     return lines


def isolate_one_leaf(leaf_id, file_name):
    #remove all leaves except one
    lines = extract_lines(file_name)
    leaf_ids = extract_leaves(lines)[:, 0]
    if len(leaf_ids) == 0:
        print("no parts")
        return
    else:
        print(str(len(leaf_ids)) + " leaves in total.")
    for i in leaf_ids:
        if i != leaf_id:
            lines = delete_leaf(int(i), lines)
    suffix = '.' + file_name.split('.')[-1]
    write_file(lines, file_name.removesuffix(suffix) + str(leaf_id) + suffix)


def isolate_all_parts(file_name):
    lines = extract_lines(file_name)
    part_names = extract_parts(lines)[1]
    for p in range(len(part_names) - 1):
        isolate_one_leaf(p, file_name)


# print (extract_part_names("../data/2balls small edit.step"))

# l = delete_leaf(301, extract_lines("../data/robo_cell.step"))
# l = delete_leaf(302, l)
# l = delete_leaf(303, l)
# l = delete_leaf(304, l)
# write_file(l, "../data/r301_304.step")
l = delete_leaf(285, extract_lines("../data/robo_cell.step"))
#l = delete_leaf(287, l)
#l = delete_leaf(288, l)
#l = delete_leaf(289, l)
write_file(l, "../data/r285.step")

#isolate_one_leaf(0, "../data/robo_cell.step")

#isolate_one_part(0, "../data/2balls small.step")
#var = extract_part_names(extract_lines("../data/robo_cell.step"))
#var2 = extract_part_names(extract_lines("../data/robo_cell_transformed_rem01.step"))
#var3 = delete_leaf(256, extract_lines("../data/robo_cell.step"))
#write_file(var3, "../data/robo_cell_del_leaf_256.step")
#g = extract_leaves(extract_lines("../data/robo_cell_del_leaf_256.step"))
pass
#lines = extract_lines("../data/robo_cell.step")
#e = extract_parts(lines)[1]
#f = extract_leaves(lines)
#var = extract_part_entry_ids(e, lines)
#isolate_one_part(0, "../data/robo_cell.step")

#isolate_all_parts("../data/fusion_screw red, plain washer yellow, lock washer blue.step")

##NEXT STEP IS DELETE ALL BUT SINGLE PART

#analyse part 48,49, part 110,111
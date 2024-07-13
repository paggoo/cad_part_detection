#isolate every part
import numpy as np
import os
from file_io import write_file
from step_io import extract_lines, extract_next_assembly_usage_occurrence_params
from subprocess import PIPE, Popen, run


def extract_parts(lines):
    part = np.array([('0', '', '', 0, 0, '')], dtype=(
    [('id', 'S99'), ('name', 'S99'), ('empty', 'S99'), ('parent_product', 'int32'), ('something', 'int32'),
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


def delete_leaf(part_id: str, lines, debug=False):
    # remove id-th element from extract_leaves
    leaves = extract_leaves(lines)
    leaves_ids = leaves[:, 0]
    if part_id.encode("utf8") not in leaves_ids:
        if debug:
            print("given id is no leaf. ignoring")
        return lines
    leaf = None
    for leaves_idx in range(len(leaves)):
        leaf = leaves[leaves_idx]
        if leaf[0].decode('utf8') == str(part_id):
            break
    curr_id = leaf[0].decode('utf8')
    curr_name = leaf[1].decode('utf8')
    parent_product = int(leaf[3])
    curr_product = int(leaf[4])
    for line_id in range(len(lines) - 1):
        line_content = lines[line_id]
        if line_content.__contains__("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):  # NEXT_ASSEMBLY_USAGE_OCCURRENCE('id','name','...
            # if lines[line].__contains__("PRODUCT_RELATED_PRODUCT_CATEGORY('part'") & lines[line].__contains__(str(curr_id)):  # vorige id
            if curr_id == line_content.split("'")[1]:
                end_cut = line_id
                break
    number_cut_lines = 0
    for l_id in range(end_cut, 0, -1):   # indexes after the removal gap will be lowered, index before is unchanged
        line_content = lines[l_id]
        lines.__delitem__(l_id)
        #line_content = lines[l_id - number_cut_lines]
        #lines.__delitem__(l_id - number_cut_lines)
        number_cut_lines += 1
        if line_content.__contains__("CONTEXT_DEPENDENT_SHAPE_REPRESENTATION"):
            # PRODUCT_RELATED_PRODUCT_CATEGORY('part',  && contains curr_id
            # PRODUCT_DEFINITION(
            # SHAPE_DEFINITION_REPRESENTATION
            break
    leaves = np.delete(leaves, leaves_idx, axis=0)
    if debug:
        print("del_id:" + str(part_id) + "/" + str(len(leaves)) + ", del#lines:" + str(
            number_cut_lines) + ", remain#lines:" + str(len(lines)) + ", del_part:" + str(curr_name))

    # if no further instances of that product, delete product
    further_instances_of_product = False
    # find further instances
    for l in leaves:
        if int(l[4]) == curr_product:
            further_instances_of_product = True
            break
    if not further_instances_of_product:
        lines = delete_product(curr_product, lines)

    # if no further children of parent part, delete parent part
    further_child_under_parent = False
    # find further children
    for le in leaves:
        if int(le[3]) == parent_product:  # le is child of same parent
            further_child_under_parent = True
            break
    if not further_child_under_parent:
        leaves = extract_leaves(lines)  # parent has become leaf now
        parent_part_id = '-1'
        # find parent part_id
        for le in leaves:
            if int(le[4]) == parent_product:
                parent_part_id = str(le[0])
                break
        lines = delete_leaf(parent_part_id, lines)
        if debug:
            print("parent deleted.")
    return lines


def delete_product(entry_id: int, lines):
    for i in range(len(lines)):
        li = lines[i]
        if li.startswith("#" + str(entry_id)) and li.__contains__("PRODUCT_DEFINITION('design'"):
            lines.__delitem__(i)    # TODO delete surrounding lines
            break
    return lines


# def delete_part(part_id, lines):
#     # remove part having id == part_id
#     part_names = extract_parts(lines)[1]
# #    entry_ids = extract_part_entry_ids(part_names, lines)
#     begin_cut = 0
#     curr_id = 0
# #    curr = entry_ids[part_id]
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


def isolate_one_leaf(leaf_id: str, file_name, debug=False):
    #remove all leaves except one
    lines = extract_lines(file_name)
    leaves = extract_leaves(lines)
    if len(leaves) == 0:
        print("no parts")
        return
    else:
        if debug:
            print(str(len(leaves)) + " leaves in total.")
    i = 0
    while len(leaves) > 1:
        leaf_ids = leaves[:, 0]
        if leaf_ids[i].decode('utf8') != str(leaf_id):
            l_id = leaf_ids[i].decode('utf8')
            lines = delete_leaf(l_id, lines)
            leaves = np.delete(leaves, i, axis=0)
        else:
            leaf_name = leaves[i, 1].decode('utf8')
            i += 1
    suffix = '.' + file_name.split('.')[-1]
    name_before_import_export = file_name.removesuffix(suffix) + str(leaf_id) + "_" + str(leaf_name) + "_raw" + suffix
    write_file(lines, name_before_import_export)
    import_export(name_before_import_export)    # generate a valid minimized export
    try:
        exists = os.path.exists(name_before_import_export)
        if exists:
            os.remove(name_before_import_export)
    except:
        pass    #file not there


def import_export(file_path):  # ((run freecad import export))
    full_file_path = os.path.abspath(file_path)
    suffix = '.' + full_file_path.split('.')[-1]
    output_path = full_file_path.removesuffix("_raw"+suffix) + suffix
    command = "import Part\n"
    command += "s = Part.Shape()\n"
    command += "s.read('" + str(full_file_path) + "')\n"
    command += "s.exportStep('" + str(output_path) + "')\n"
    command += "exit()\n"
    Popen(['freecadcmd'], stdin=PIPE, text=True).communicate(command)


def isolate_all_parts(file_name):
    lines = extract_lines(file_name)
    leaf_ids = extract_leaves(lines)[:, 0]
    for l_id in leaf_ids:
        isolate_one_leaf(int(l_id), file_name)
        print("isolated leaf: " + str(l_id))


# print (extract_part_names("../data/2balls small edit.step"))
#import_export("../data/r301.step")
#import_export("../data/r301-2.step")
#import_export("../data/r301-3.step")
#import_export("../data/r301-4.step")

# l = delete_leaf(303, l)
# l = delete_leaf(304, l)
# l = delete_leaf(296, l)
# l = delete_leaf(297, l)
# l = delete_leaf(298, l)
# l = delete_leaf(299, l)
# l = delete_leaf(291, l)
# l = delete_leaf(292, l)
# l = delete_leaf(293, l)
# l = delete_leaf(294, l)
# l = delete_leaf(286, l)
# l = delete_leaf(287, l)
# l = delete_leaf(288, l)
# l = delete_leaf(289, l)
#import_export("../data/r289-304_raw.step")
#l = delete_leaf('285', extract_lines("../data/robo_cell.step"))
#l = delete_leaf(287, l)
#l = delete_leaf(288, l)
#l = delete_leaf(289, l)
#write_file(l, "../data/r285__.step")
#import_export("../data/r285__.step")
#l = delete_leaf(281, extract_lines("../data/r285__n.step"))
#l = delete_leaf(282, l)
#write_file(l, "../data/r281-2+5.step")
#isolate_one_part(0, "../data/2balls small.step")
#var = extract_part_names(extract_lines("../data/robo_cell.step"))
#var2 = extract_part_names(extract_lines("../data/robo_cell_transformed_rem01.step"))
#var3 = delete_leaf(256, extract_lines("../data/robo_cell.step"))
#write_file(var3, "../data/robo_cell_del_leaf_256.step")
#g = extract_leaves(extract_lines("../data/robo_cell_del_leaf_256.step"))
#lines = extract_lines("../data/robo_cell.step")
#e = extract_parts(lines)[1]
#f = extract_leaves(lines)
#var = extract_part_entry_ids(e, lines)

#for i in range(305):
    #l = delete_leaf(str(i), extract_lines("../data/robo_cell.step"))
    #write_file(l, str(i)+".step")
#    import_export("../data/test/"+str(i)+".step")


#isolate_all_parts("../data/fusion_screw red, plain washer yellow, lock washer blue.step")
#isolate_all_parts("../data/robo_cell.step")
#analyse part 48,49, part 110,111
#isolate every part
import glob
import pathlib
import sys
import platform
import numpy as np
import os

from src.extract_part.extract_parts_and_shapes_to_STL import retrieve_objects_from_freecad, export_object_to_stl
from src.io.file_io import write_file
from src.io.step_io import extract_lines, extract_next_assembly_usage_occurrence_params, import_export


if platform.system() == 'Windows':
    FREECADPATH = glob.glob(r"C:\Program Files\FreeCAD *\bin")
    FREECADPATH = FREECADPATH[0]
    # print(FREECADPATH) #in case needed to confirm, uncomment

elif platform.system() == 'Darwin':  # MacOS
    FREECADPATH = '/Applications/FreeCAD.app/Contents/Resources/lib/'
elif platform.system() == 'Linux':
    FREECADPATH = '/usr/lib/freecad-python3/lib/'  # path to your FreeCAD.so or FreeCAD.dll file
else:
    print("Error: No recognized system available.")
sys.path.append(FREECADPATH)
import FreeCAD as App
import Part
import Mesh
App.addImportType("STEP with colors (*.step *.stp)", "Import")


def extract_solids(lines):
    solids = []
    for l in lines:
        if l.__contains__('MANIFOLD_SOLID_BREP'):
            solids.append(l)
    return solids


def isolate_one_solid(solids, lines, output_path_and_name_WITH_EXTENSION, solid_to_isolate_string=""):
    # isolate first solid
    if solid_to_isolate_string == "":
        solid_to_isolate_string = solids.pop()
    # remove all solids but matching
    solid_id = int(solid_to_isolate_string.removeprefix('#').split('=')[0])
    for a in solids:
        if solid_to_isolate_string != a:
            num_del_lines = 0
            #remove solid a from lines
            for i in range(len(lines) - 1):
                if a == lines[i - num_del_lines]:
                    lines.__delitem__(i - num_del_lines)
                    num_del_lines += 1
    suffix = '.' + output_path_and_name_WITH_EXTENSION.split('.')[-1]
    stem = os.path.basename(output_path_and_name_WITH_EXTENSION.removesuffix(suffix))
    new_file_name = os.path.join(stem + str(solid_id) + suffix)
    # make directory for isolated parts
    isolated_parts_folder = os.path.join(os.path.dirname(output_path_and_name_WITH_EXTENSION), stem)
    os.makedirs(isolated_parts_folder, exist_ok=True)
    new_file_path_and_name = os.path.join(isolated_parts_folder, new_file_name)
    write_file(lines, new_file_path_and_name)

    import_export(new_file_path_and_name)

    App.loadFile(new_file_path_and_name)
    doc = App.activeDocument()
    objects = [o for o in doc.Objects if (hasattr(o, 'Shape') and o.Shape.Solids and not o.isDerivedFrom('PartDesign::Feature') and not hasattr(o, 'Type'))]
    solid = objects[0]
    solid.Shape.exportStl(new_file_path_and_name.removesuffix(suffix) + '.stl')
    return isolated_parts_folder


def isolate_all_solids(path_to_file):
    lines = extract_lines(path_to_file)
    solids = extract_solids(lines)
    folder = os.path.dirname(path_to_file)
    for solid_to_isolate_string in solids:
        folder = isolate_one_solid(solids, lines.copy(), path_to_file, solid_to_isolate_string)
    return folder


def extract_parts(lines):
    part = np.array([('0', '', '', 0, 0, '', 0)], dtype=(
    [('id', 'S99'), ('name', 'S99'), ('empty', 'S99'), ('parent_product', 'int32'), ('product', 'int32'),
     ('dollar', 'S99'), ('entry_id', 'int32')]))
    parts = np.vstack(part)
    parts = np.delete(parts, 0)
    #parts = np.append(parts, part2)
       # each part has tree_id, name, parent component it belongs to
    for line_id in range(len(lines)):
        line = lines[line_id]
        if line.__contains__("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):
            p = extract_next_assembly_usage_occurrence_params(line)
            parts = np.append(parts, p)     # insert tuple
    return np.column_stack([parts[name] for name in parts.dtype.names])


def extract_leaves(lines):  # a part is leaf if not referenced by any other (following) part as parent
    parts = extract_parts(lines)
    leaves = parts                              # ATTENTION: when coming here from isolate_single_product_multipro_portion parts is empty!!!!!!!!
    deleted_counter = 0
    for n in range(len(parts)):      # we have to run n forward in order to exclude parents of parents
        product = parts[n][4]
        for other_part in parts:
            parent = other_part[3]
            if product == parent:
                leaves = np.delete(leaves, n - deleted_counter, axis=0)
                deleted_counter += 1
                break
#    generate uid for each leaf repopulating the part_id field in a way that ensures uniqueness
    for i in range(len(leaves)):
        leaves[i][0] = i
    return leaves


def delete_leaf(leaf_uid: int, leaves, lines, debug=False):
    leaves_uids = leaves[:, 6].astype(int)
    if leaf_uid not in leaves_uids:
        if debug:
            print("given uid is no leaf. ignoring")
        return lines
    leaf = None
    for i in range(len(leaves)):
        if leaves_uids[i].astype(int) == leaf_uid:
            break
    leaf = leaves[i]
    curr_id = leaf[0].decode('utf8')
    curr_name = leaf[1].decode('utf8')
    parent_product = int(leaf[3])
    curr_product = int(leaf[4])
    for line_id in range(len(lines)):
        line_content = lines[line_id]
        if line_content.__contains__("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):  # NEXT_ASSEMBLY_USAGE_OCCURRENCE('id','name','...
            # if lines[line].__contains__("PRODUCT_RELATED_PRODUCT_CATEGORY('part'") & lines[line].__contains__(str(curr_id)):  # vorige id
            if curr_id == line_content.split("'")[1]:
                if leaf_uid == int(line_content.removeprefix('#').split('=')[0]):
    #                end_cut = line_id
                    lines.__delitem__(line_id)      #try removing only this line
                    number_cut_lines = 1
                    break
    # for l_id in range(end_cut, 0, -1):   # indexes after the removal gap will be lowered, index before is unchanged
    #     line_content = lines[l_id]
    #     if line_content.__contains__("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):
    #         break       # in case multi NAUOs in sequence
    #     lines.__delitem__(l_id)
    #     #line_content = lines[l_id - number_cut_lines]
    #     #lines.__delitem__(l_id - number_cut_lines)
    #     number_cut_lines += 1
    #     if line_content.__contains__("CONTEXT_DEPENDENT_SHAPE_REPRESENTATION"):
    #         # PRODUCT_RELATED_PRODUCT_CATEGORY('part',  && contains curr_id
    #         # PRODUCT_DEFINITION(
    #         # SHAPE_DEFINITION_REPRESENTATION
    #         break
    leaves = np.delete(leaves, i, axis=0)
    if debug:
        print("del_id:" + str(curr_id) + "/" + str(len(leaves)) + ", del#lines:" + str(
            number_cut_lines) + ", remain#lines:" + str(len(lines)) + ", del_part:" + str(curr_name))

    # if no further instances of that product, delete product
    further_instances_of_product = False
    # find further instances
    for le in leaves:
        if int(le[4]) == curr_product:
            further_instances_of_product = True
            matching_entry = le[0]
            break
    if not further_instances_of_product:
        lines = delete_product(curr_product, lines)
        if debug:
            print("product " + str(curr_product) + " deleted.")
    else:
        if debug:
            print("product " + str(curr_product) + " not deleted, because referenced by part " + str(matching_entry))

    # if no further children of parent part, delete parent part
    further_child_under_parent = False
    # find further children
    for le in leaves:
        if int(le[3]) == parent_product:  # le is child of same parent
            further_child_under_parent = True
            break
    if not further_child_under_parent:
        leaves = extract_leaves(lines)  # parent has become leaf now
        parent_part_uid = '-1'
        # find parent part_uid
        for le in leaves:
            if int(le[4]) == parent_product:
                parent_part_uid = str(le[6])
                break
        lines = delete_leaf(parent_part_uid, leaves, lines)
        if debug:
            print("parent deleted.")
    return lines


def isolate_first_leaf_or_solid(lines, leaves):
    if len(leaves) != 0:
        leaf = leaves[0]
        leaf_uid = leaf[6].astype(int)
        deleted_lines = 0
        for i in range(len(lines)):
            li = str(lines[i - deleted_lines])
            if li.__contains__('='):
                entry_id = int(li.split('=')[0].removeprefix('#'))
                linekey = li.split('=')[1].replace(' ', '')
                if linekey.startswith("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):  # NEXT_ASSEMBLY_USAGE_OCCURRENCE('id','name','...
                    # if lines[line].__contains__("PRODUCT_RELATED_PRODUCT_CATEGORY('part'") & lines[line].__contains__(str(curr_id)):  # vorige id
                    if leaf_uid != entry_id:
                        lines.__delitem__(i - deleted_lines)
                        deleted_lines += 1
    else:
        solids = extract_solids(lines)
        abspath = os.path.abspath("temp.step")
        write_file(lines, abspath)
        isolate_one_solid(solids, lines, abspath, solids[0])

    return lines


def has_parent(part, parts):
    products = parts[:, 4]
    if part is None:
        return None
    for i in range(len(products)):
        if products[i] == part[3]:
            return parts[i]
    return None


def isolate_single_product(product_id: int, lines, keep_all_parts_from_product=True):
    # we want to return only one part
    parts = extract_parts(lines)
    part = None                                # first part of the product
    part_products = [part[4].astype(int) for part in parts]
    for i in range(len(part_products)):
        if product_id == part_products[i]:
            part = parts[i]
            break
    bloodline = []                                          # from child every parent until root
    oldest_ancester = part
    bloodline.append(oldest_ancester[4].astype(int))
    while has_parent(oldest_ancester, parts) is not None:
        if oldest_ancester[3] != b'':
            bloodline.append(oldest_ancester[3].astype(int))
            oldest_ancester = has_parent(oldest_ancester, parts)
    if oldest_ancester[3] != b'':                           # does oldest ancestor have parent
        bloodline.append(oldest_ancester[3].astype(int))
    deleted_lines = 0
    for i in range(len(lines)):
        li = str(lines[i - deleted_lines])
        if li.__contains__('='):
            entry_id = int(li.split('=')[0].removeprefix('#'))
            linekey = li.split('=')[1].replace(' ', '')
            if linekey.startswith("PRODUCT_DEFINITION('"):
                if entry_id not in bloodline:           # parent parts can be removed but products in bloodline can not!
                    lines.__delitem__(i - deleted_lines)                # remove products that are no parents of part
                    deleted_lines += 1
            else:
                if linekey.startswith("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):  # NEXT_ASSEMBLY_USAGE_OCCURRENCE('id','name','...
                    # if lines[line].__contains__("PRODUCT_RELATED_PRODUCT_CATEGORY('part'") & lines[line].__contains__(str(curr_id)):  # vorige id
                    if entry_id != part[6].astype(int):
                        lines.__delitem__(i - deleted_lines)            # remove all parts except part
                        deleted_lines += 1
    # for p in product_representatives_ids:
    #     if not product_id == p:
    #         lines = delete_product(p, lines)
    return lines


# def delete_all_leaves_from_product(product_id: int, lines):
#     deleted_lines = 0
#     for i in range(len(lines)):
#         line_content = lines[i - deleted_lines]
#         if line_content.__contains__("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):  # NEXT_ASSEMBLY_USAGE_OCCURRENCE('id','name','...
#             if product_id == int(line_content.split(",")[4].removeprefix(' ').removeprefix('#')):
#                 lines.__delitem__(i - deleted_lines)
#                 deleted_lines += 1
#     return lines


def extract_first_shape_to_stl_freecad(lines):      # due to inconsistent export settings better dont mix extraction methods
    file_name = "DELETE_ME_TEMPORARY_FILE.STEP"
    abs_path = os.path.abspath(file_name)
    write_file(lines, abs_path)
    objects = retrieve_objects_from_freecad(file_name)
    export_object_to_stl(objects[0], abs_path)


def isolate_shells_via_freecad(path_to_file):
    abs_path = os.path.abspath(path_to_file)
    objects = retrieve_objects_from_freecad(path_to_file)
    for obj in objects:
        if hasattr(obj.Shape, 'ShapeType') and obj.Shape.ShapeType == 'Shell':
            sanitized_label = ''.join(e for e in obj.Label if e.isalnum() or e in ['_', '-'])
            filename = os.path.join(os.path.dirname(abs_path), pathlib.Path(abs_path).stem, sanitized_label + ".stl")
            # export_object_to_stl(obj, filename, True)
            obj.Shape.exportStl(filename)
    return os.path.join(os.path.dirname(abs_path), pathlib.Path(abs_path).stem)


def delete_product(entry_id: int, lines):
    for i in range(len(lines)):
        li = lines[i]
        prefix = "#" + str(entry_id)
        if li.startswith(prefix):
            linekey = li.replace(' ', '').removeprefix(prefix+'=')
            if linekey.startswith("PRODUCT_DEFINITION('"):
                lines.__delitem__(i)
                break
    return lines


# def delete_part(part_id, lines):
#     # remove part having id == part_id
#     part_names = extract_parts(lines)[1]
# #    entry_ids = extract_part_entry_ids(part_names, lines)
#     begin_cut = 0
#     curr_id = 0
# #    curr = entry_ids[part_id]
#     for line in range(len(lines)):
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


#deprecated
# def isolate_one_leaf(leaf_uid: int, file_name, debug=False):
#     #remove all leaves except one
#     lines = extract_lines(file_name)
#     leaves = extract_leaves(lines)
#     if len(leaves) == 0:
#         print("no parts.")
#         return
#     else:
#         if debug:
#             print(str(len(leaves)) + " leaves in total.")
#             print("attempting to isolate part: " + str(leaf_uid))
#     # delete all except the relevant leaf
#     while len(leaves) >= 1:
#         if leaf_uid != int(leaves[0, 6]):  # index does not have to increase because deletion
#             lines = delete_leaf(int(leaves[0, 6]), leaves, lines)
#             leaves = np.delete(leaves, 0, axis=0)
#         else:
#             leaf_id = leaves[0, 0].decode('utf8')
#             leaf_name = leaves[0, 1].decode('utf8')
#             leaf_product = leaves[0, 4].decode('utf8')
#             leaves = np.delete(leaves, 0, axis=0)
#     suffix = '.' + file_name.split('.')[-1]
#     # make directory for isolated parts
#     parts_dir = os.path.join(os.path.dirname(file_name), os.path.basename(file_name.removesuffix(suffix)))
#     os.makedirs(parts_dir, exist_ok=True)
#     try:
#         leaf_name
#     except NameError:   # 'leaf_name' not associated with a value
#         leaf_name = leaves[0, 1].decode('utf8')
#     if leaf_name is None:
#         print("check if leaves is empty")
#         return
#     else:
#         # product is always populated and should be used to prevent files being overwritten if leaf_name = ''
#         leaf_id = str(leaf_id).replace('/', '_').replace('\\', "_")  # file name must not contain folder seperators
#         leaf_name = str(leaf_name).replace('/', '_').replace('\\', "_")  # file name must not contain folder seperators
#         if str(leaf_id) == str(leaf_name):
#             name_before_import_export = os.path.basename(file_name.removesuffix(suffix) + "_" + str(leaf_uid) + '_' + leaf_name + '_' + leaf_product + "_raw" + suffix)
#         else:
#             name_before_import_export = os.path.basename(file_name.removesuffix(suffix) + "_" + str(leaf_uid) + '_' + leaf_id + "_" + leaf_name + '_' + leaf_product + "_raw" + suffix)
#         path_and_name_before_import_export = os.path.join(parts_dir, name_before_import_export)
#         write_file(lines, path_and_name_before_import_export)
#         isolated_parts_file = import_export(path_and_name_before_import_export)    # generate a valid minimized export
#         try:
#             exists = os.path.exists(path_and_name_before_import_export)
#             if exists:
#                 pass
#                 os.remove(path_and_name_before_import_export)
#         except:
#             pass    #file not there
#     return parts_dir, isolated_parts_file


# def isolate_all_parts(file_name):
#     lines = extract_lines(file_name)
#     leaves = extract_leaves(lines)
#     if 0 != len(leaves):
#         leaf_ids = leaves[:, 0]
#         for l_id in leaf_ids:
#             isolate_one_leaf(int(l_id), file_name)
#             print("isolated leaf: " + str(l_id))
#     else:
#         solids = extract_solids(lines)
#         for s in solids:
#             isolate_one_solid(s, lines, file_name)



# # isolate_all_solids("/home/user/PycharmProjects/bauteil_classification/data/baugruppen/Gepard Turm/0_GepardTurm_175822.STEP")
# lines = extract_lines("../../data/baugruppen/3d_printer/src/3D_Printer_Enclosure_DanielDesigns.step")
# out_lines = isolate_single_product(103426, lines)
# write_file(out_lines, "test.step")
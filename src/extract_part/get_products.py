# in an assembly there might be parts from the same product
# such as multiple screws of same type at different locations
# these might be defined by a common product thus saving storage
import multiprocessing
import os
import pathlib
from functools import partial

import numpy as np

from src.extract_part.extract_parts_and_shapes_to_STL import isolate_to_stl_excluding_freecad_duplicates, retrieve_objects_from_freecad
from src.extract_part.get_parts import extract_leaves, isolate_one_leaf, extract_solids, isolate_one_solid, \
    isolate_single_product, delete_leaf, isolate_first_leaf, import_export, isolate_all_solids
from src.io.file_io import write_file
from src.io.step_io import extract_lines


def get_products(lines, leaves):
    leaves_products = leaves[:, 4]
    product_ids = set()
    for le in leaves_products:       # collect unique ids
        product_ids.add(int(le))
    return product_ids


def find_product_label(product_id: int, lines):
    for line in lines:
        if str(line).startswith('#' + str(product_id)):
            content = str(line).split("'")[1].removeprefix(' ')
            if content == 'UNKNOWN' or content == 'ANY' or content == '':
                line_id = int(str(line).split(",")[2].removeprefix(' ').removeprefix('#'))
                return find_product_label(line_id, lines)
            else:
                sanitized_label = ''.join(e for e in content if e.isalnum() or e in ['_', '-'])
                return sanitized_label


# lines = extract_lines("/home/user/PycharmProjects/bauteil_classification/data/baugruppen/Gepard Turm.STEP")
# leaves = extract_leaves(lines)
# pr_ids = get_products(lines, leaves)
# print(find_product_label(list(pr_ids)[0], lines))


def isolate_single_product_multiprocessor_portion(p_id, lines, leaves_product_ids, product_label, path_to_file, suffix):
    out_lines = isolate_single_product(p_id, lines.copy())
    out_lines = isolate_first_leaf(out_lines, extract_leaves(out_lines))
    label = find_product_label(p_id, out_lines)
    out_file = os.path.join(path_to_file.removesuffix(suffix), product_label + '_' + label + '_' + str(p_id) + suffix)
    write_file(out_lines, out_file)
    import_export(out_file)
    return out_file


def isolate_one_part_per_product(path_to_file: str):
    lines = extract_lines(path_to_file)
    leaves = extract_leaves(lines)
    leaves_product_ids = [l.astype(int) for l in leaves[:, 4]]
    product_ids = list(get_products(lines, leaves))
    product_labels = [str(leaves_product_ids.index(p)) for p in product_ids]

    # Prepare for multiprocessing
    suffix = '.' + path_to_file.split('.')[-1]
    pool = multiprocessing.Pool()  # Automatically uses the number of available CPUs

    # Map product_ids to the processing function along with other static arguments
    files = pool.starmap(
        isolate_single_product_multiprocessor_portion,
        zip(product_ids,
            [lines] * len(product_ids),  # Static argument for lines
            [leaves_product_ids] * len(product_ids),  # Static argument for leaves_product_ids
            product_labels,  # Dynamic argument product_label
            [path_to_file] * len(product_ids),  # Static argument for path_to_file
            [suffix] * len(product_ids))  # Static argument for suffix
    )

    # Close and join the pool to clean up
    pool.close()
    pool.join()

    folder = os.path.join(path_to_file.removesuffix(suffix))
    # go through folder and isolate solids from each file
    with multiprocessing.Pool() as pool:
        pool.map(isolate_to_stl_excluding_freecad_duplicates, files, chunksize=1)        # alternatively: isolate_all_solids
    return os.path.join(path_to_file.removesuffix(suffix))


# def isolate_one_part_per_product_single_processor(path_to_file: str):
#     lines = extract_lines(path_to_file)
#     leaves = extract_leaves(lines)
#     leaves_product_ids = [l.astype(int) for l in leaves[:, 4]]
#     product_ids = list(get_products(lines, leaves))
#     product_labels = [str(leaves_product_ids.index(p)) for p in product_ids]
#     for i in range(len(product_ids)):
#         p_id = product_ids[i]
#         out_lines = isolate_single_product(p_id, lines.copy())
#         out_lines = isolate_first_leaf(out_lines, extract_leaves(out_lines))
#         suffix = '.' + path_to_file.split('.')[-1]
#         out_file = os.path.join(path_to_file.removesuffix(suffix), product_labels[i] + str(p_id) + suffix)
#         write_file(out_lines, out_file)
#         import_export(out_file)


# deprecated. functionality now covered by src.extract_part.extract_parts_and_shapes_to_STL.isolate()
def isolate_one_part_per_product_deprecated(file_name, solids_only=False, isolate_solids_inside_leafs=True):
    objects = retrieve_objects_from_freecad(file_name)
    shapes = [o.Shape for o in objects]
    #labels = [o.Label for o in objects]
    lines = extract_lines(file_name)
    leaves = extract_leaves(lines)
    isolated_parts_folder = None
    if 0 == len(leaves):            #nauos dont exist
        solids = extract_solids(lines)
        if 0 == len(solids):
            print("could not find parts or solids in file: " + str(file_name))
            print("extraction via freecad. this might take long time. please be patient or choose assembly that is formatted according to standard")
            isolate_to_stl_excluding_freecad_duplicates(file_name)
        else:
            for s in solids:
                lines_copy = lines.copy()      # do not reuse lines, each isolation needs to start fresh
                isolated_parts_folder = isolate_one_solid(solids, lines_copy, file_name, s)
    else:
        leaves_products = leaves[:, 4]
        product_ids = get_products(lines, leaves)
        product_representatives_leaves_uids = set()  # this must be a set since we want a single part representing each product
        for leaf in leaves:
            if int(leaf[4]) in product_ids:
                product_representatives_leaves_uids.add(int(leaf[6]))
                product_ids.discard(int(leaf[4]))
                pass
        print(str(len(product_representatives_leaves_uids)) + " product_representatives in total.")
        i = 1
        for leaf_uid in product_representatives_leaves_uids:
            print("isolating product_representative " + str(i) + "/" + str(len(product_representatives_leaves_uids)))  # progress
            isolated_parts_folder, isolated_parts_file = isolate_one_leaf(leaf_uid, file_name, debug=False)           # toggle debug
            if isolate_solids_inside_leafs:
                isolate_one_part_per_product_deprecated(isolated_parts_file, solids_only=True)       # second run for isolating solids inside of parts
            i += 1
        print("successfully isolated " + str(len(product_representatives_leaves_uids)) + " leaves.")
    return isolated_parts_folder


def find_product_representative(product_id: int, leaves):
    for le in leaves:
        if product_id == le[4].decode('utf8'):
            return le


def isolate_products_from_folder(path):
    for file in pathlib.Path(path).rglob('*'):
        if file.is_file():
            suffix = str(file).split('.')[-1]
            if suffix.lower() == 'stp' or suffix.lower() == 'step':
                isolate_to_stl_excluding_freecad_duplicates(str(file))
                #isolate_one_part_per_product(str(file))


#get_products(extract_lines("../data/robo_cell.step"))
#isolate_one_part_per_product("../data/robo_cell.step")
#isolate_one_part_per_product("../data/3D_Printer_Enclosure_DanielDesigns.step")
#isolate_one_part_per_product("../data/Montain_BIKE_LUIGI.stp")
#isolate_one_part_per_product("../data/high_speed_gantry_auto_screw_asm.stp")
# isolate_one_part_per_product("../data/Electric_motor.stp")
# print("-------------------------------------------------------------------------------------------------------------------------------------------------")
# isolate_one_part_per_product("../data/9304_3_8_.stp")
# print("-------------------------------------------------------------------------------------------------------------------------------------------------")
# isolate_one_part_per_product("../data/255_v2.stp")
# print("-------------------------------------------------------------------------------------------------------------------------------------------------")
# isolate_one_part_per_product("../data/bycicle.stp")
# print("-------------------------------------------------------------------------------------------------------------------------------------------------")
# isolate_one_part_per_product("../data/vesp.stp")
# print("-------------------------------------------------------------------------------------------------------------------------------------------------")
# isolate_one_part_per_product("../data/STEEL_PLATFORM_HAND_TRUCK.stp")
# print("-------------------------------------------------------------------------------------------------------------------------------------------------")
# isolate_one_part_per_product("../data/Eurokastenwagen.stp")
# print("-------------------------------------------------------------------------------------------------------------------------------------------------")
# isolate_one_part_per_product("../data/Caliper_True_Dimension_Configurator.stp")
# print("-------------------------------------------------------------------------------------------------------------------------------------------------")
#isolate_one_part_per_product("../../data/baugruppen/wheel_loader/src/Wheel_loader.stp")
#isolate_one_part_per_product("../../data/1-ASME B18.2.1 STUD BOLT ASME B18.2.2 HEX NUTS/01- 1 4 - 20 UNC/1 4 - 20 UNC.stp")
#isolate_one_leaf('NAUO3', "../data/Montain_BIKE_LUIGI.stp", debug=True)


# isolate_products_from_folder("../../data/convert/gt/screw_or_not/no_screw/other/")
# isolate_one_part_per_product("../../data/baugruppen/fail/no_screws/326025873/326025873_29232__ _9220.STEP")

# isolate_one_part_per_product('../../data/baugruppen/Gepard Turm.STEP')
# # delete_all_leaves_from_product(136081, extract_leaves(l), l)
# leaves = extract_leaves(l)
# # pr_ids = get_products(l, leaves)
# lines = isolate_single_product(136081, l)
#
# # folder = isolate_one_solid(extract_solids(lines), lines, "/home/user/PycharmProjects/bauteil_classification/data/baugruppen/Gepard Turm.STEP")
# lili = isolate_first_leaf(lines, extract_leaves(lines))
#
# # a, b = isolate_one_leaf(leaves[0][6].astype(int), "extr_136081.STEP")
# write_file(lili, "extr_136081_.STEP")
# l = isolate_one_part_per_product("/home/user/PycharmProjects/bauteil_classification/data/baugruppen/Gepard Turm.STEP")
# print(l)
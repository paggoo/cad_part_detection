# in an assembly there might be parts from the same product
# such as multiple screws of same type at different locations
# these might be defined by a common product thus saving storage
import pathlib

from get_parts import extract_leaves, isolate_one_leaf
from src.io.step_io import extract_lines


def get_products(lines, leaves):
    leaves_products = leaves[:, 4]
    product_ids = set()
    for le in leaves_products:       # collect unique ids
        product_ids.add(int(le))
    return product_ids


def isolate_one_part_per_product(file_name):
    lines = extract_lines(file_name)
    leaves = extract_leaves(lines)
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
        isolate_one_leaf(leaf_uid, file_name, debug=False)           # toggle debug
        i += 1
    print("successfully isolated " + str(len(product_representatives_leaves_uids)) + " leaves.")


def find_product_representative(product_id: int, leaves):
    for le in leaves:
        if product_id == le[4].decode('utf8'):
            return le


def isolate_products_from_folder(path):
    for file in pathlib.Path(path).rglob('*'):
        if file.is_file() and str(file).endswith('.stp'):
            isolate_one_part_per_product(str(file))


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

isolate_one_part_per_product("../../data/1-ASME B18.2.1 STUD BOLT ASME B18.2.2 HEX NUTS/01- 1 4 - 20 UNC/1 4 - 20 UNC.stp")


#p = "../../data/1-ASME B18.2.1 STUD BOLT ASME B18.2.2 HEX NUTS"
#isolate_products_from_folder(p)




#isolate_one_leaf('NAUO3', "../data/Montain_BIKE_LUIGI.stp", debug=True)
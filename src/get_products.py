# in an assembly there might be parts from the same product
# such as multiple screws of same type at different locations
# these might be defined by a common product thus saving storage

from get_parts import extract_leaves, isolate_one_leaf
from step_io import extract_lines


def get_products(lines, leaves):
    leaves_products = leaves[:, 4]
    product_ids = set()
    for l in leaves_products:       # collect unique ids
        product_ids.add(int(l))
    return product_ids


def isolate_one_part_per_product(file_name):
    lines = extract_lines(file_name)
    leaves = extract_leaves(lines)
    leaves_products = leaves[:, 4]
    product_ids = get_products(lines, leaves)
    leaves_ids = set()
    for leaf in leaves:
        if int(leaf[4]) in product_ids:
            leaves_ids.add((leaf[0]).decode('utf8'))
            product_ids.discard(int(leaf[4]))
            pass
    for l_id in leaves_ids:
        isolate_one_leaf(l_id, file_name, debug=True)            #remove debug
    print("successfully isolated " + str(len(leaves_ids)) + " leaves.")


#get_products(extract_lines("../data/robo_cell.step"))
#isolate_one_part_per_product("../data/robo_cell.step")
#isolate_one_part_per_product("../data/3D_Printer_Enclosure_DanielDesigns.step")
#isolate_one_part_per_product("../data/Montain_BIKE_LUIGI.stp")
#isolate_one_part_per_product("../data/high_speed_gantry_auto_screw_asm.stp")
isolate_one_part_per_product("../data/Electric_motor.stp")
print("-------------------------------------------------------------------------------------------------------------------------------------------------")
isolate_one_part_per_product("../data/9304_3_8_.stp")
print("-------------------------------------------------------------------------------------------------------------------------------------------------")
isolate_one_part_per_product("../data/255_v2.stp")
print("-------------------------------------------------------------------------------------------------------------------------------------------------")
isolate_one_part_per_product("../data/bycicle.stp")
print("-------------------------------------------------------------------------------------------------------------------------------------------------")
isolate_one_part_per_product("../data/vesp.stp")
print("-------------------------------------------------------------------------------------------------------------------------------------------------")
isolate_one_part_per_product("../data/STEEL_PLATFORM_HAND_TRUCK.stp")
print("-------------------------------------------------------------------------------------------------------------------------------------------------")
isolate_one_part_per_product("../data/Eurokastenwagen.stp")
print("-------------------------------------------------------------------------------------------------------------------------------------------------")
isolate_one_part_per_product("../data/Caliper_True_Dimension_Configurator.stp")
print("-------------------------------------------------------------------------------------------------------------------------------------------------")
isolate_one_part_per_product("../data/sheet_metal_rack.STEP")





#isolate_one_leaf('NAUO3', "../data/Montain_BIKE_LUIGI.stp", debug=True)
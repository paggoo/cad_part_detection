# to flag parts semi-manually as in or out in order to build ground-truth

from __future__ import print_function
import os
import os.path
from time import sleep
from view_stp import view_stp, close_stp_viewer
from pynput.keyboard import Key, Listener


def flag_parts(path):
    # manual differenciation if this part belongs to the classified class (fastener) or not
    full_path = os.path.abspath(path)
    for file_name in os.listdir(path):        #toggle manually selecting parts
        full_path_to_file = os.path.join(full_path, file_name)

        def on_release(key):  # definition might be better outside loop if functional
            try:
                if key.char == 'n':
                    # deselect current part
                    flag_part(full_path_to_file, False)
                    # Stop listener
                    return False
                if key.char == 'y':
                    # select current part
                    flag_part(full_path_to_file, True)
                    # Stop listener
                    return False
            except:
                pass  # special key pressed

        viewer_process = view_stp(full_path_to_file)
        sleep(1)
        print("does this part belong to the desired class?: press y or n \n")
        with Listener(on_release=on_release) as listener:
            listener.join()
    close_stp_viewer(viewer_process)


def flag_part(full_path_to_file, is_standard_component):
    if is_standard_component:
        new_name = "#STD#" + str(os.path.basename(full_path_to_file))
    else:
        new_name = "#nonSTD#" + str(os.path.basename(full_path_to_file))
    full_path_to_dir = os.path.dirname(full_path_to_file)
    full_path_and_new_name = os.path.join(full_path_to_dir, new_name)
    os.rename(full_path_to_file, full_path_and_new_name)


flag_parts("../data/baugruppen/high_speed_gantry/products_string")
#full = os.path.abspath("../data/baugruppen/high_speed_gantry/products_string/high_speed_gantry_auto_screw_asm0_Next assembly relationship.stp")
#flag_part(full, True)


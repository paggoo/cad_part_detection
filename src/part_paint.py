
from __future__ import print_function
import os
import platform
from pathlib import Path
from time import sleep
from file_io import write_file
from step_io import insert_hash_entry, find_all_advanced_faces_entries, get_highest_hash_entry, extract_lines
import os.path
from view_stp import view_stp, close_stp_viewer
from pynput.keyboard import Key, Listener
import numpy

#category: normbauteile: fasteners

#flange fastener, flange nut


#color entire "MANIFOLD_SOLID_BREP" of fastener?


def color_nth_advanced_face(file, entry_number, color):
    lines = extract_lines(file)
    af = find_all_advanced_faces_entries(lines)[entry_number]
    last = get_highest_hash_entry(lines)
    add_override_to_MDGPR(file, last+1)
    insert_hash_entry(file, "#" + str(last+1) + " = OVER_RIDING_STYLED_ITEM('overriding color',(#" + str(last+2) + "),#" + str(af) + ",'');")
    insert_hash_entry(file, "#" + str(last+2) + " = PRESENTATION_STYLE_ASSIGNMENT((#" + str(last+3) + "));")
    insert_hash_entry(file, "#" + str(last+3) + " = SURFACE_STYLE_USAGE(.BOTH.,#" + str(last+4) + ");")
    insert_hash_entry(file, "#" + str(last+4) + " = SURFACE_SIDE_STYLE('',(#" + str(last+5) + "));")
    insert_hash_entry(file, "#" + str(last+5) + " = SURFACE_STYLE_FILL_AREA(#" + str(last+6) + ");")
    insert_hash_entry(file, "#" + str(last+6) + " = FILL_AREA_STYLE('',(#" + str(last+7) + "));")
    insert_hash_entry(file, "#" + str(last+7) + " = FILL_AREA_STYLE_COLOUR('',#" + str(last+8) + ");")
    insert_hash_entry(file, "#" + str(last+8) + " = DRAUGHTING_PRE_DEFINED_COLOUR('" + color + "');")
    #alternative like = COLOUR_RGB('',0.,0.,1.);


def add_override_to_MDGPR(file, n):
    lines = extract_lines(file)
    for i in range(len(lines)):
        if lines[i].find("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION") > 0:
            lines[i] = lines[i].split(")")[0] + ", #" + str(n) + ")" + lines[i].split(")")[1] + ")" + lines[i].split(")")[2]
    write_file(lines, file)


def color_multiple_faces(file):
    lines = extract_lines(file)
    faces = find_all_advanced_faces_entries(lines)
    for f in faces:
        color_nth_advanced_face(file, f, "blue")
        #datei anzeigen mit freecad?
        #bestätigen y/n

#color_nth_advanced_face("../data/Control_levers_n.stp", 3, "green")
#add_override_to_MDGPR("../data/Control_levers.stp", 0)


def toggle_faces_color(path):
    # manual differenciation whether this face belongs to the classified class (fastener) or not
    selected = "red"
    uncolored = "yellow"
    colored = "blue"
    full_path = os.path.abspath(path)
    lines = extract_lines(path)
    num_faces = len(find_all_advanced_faces_entries(lines))
    # all uncolored first
    for i in range(num_faces):
        color_nth_advanced_face(path, i, uncolored)
    #print("no face colored")
    #view_stp(full_path)
    print("select surfaces belonging to desired class. " + colored + "=in, " + uncolored + "=out.\n")
    for i in range(num_faces):      #toggle manually selecting face
        def on_release(key):
            try:
                if key.char == 'n':
                    # deselect current face
                    print("n pressed. deselecting surface " + str(i))
                    color_nth_advanced_face(path, i, uncolored)
                    # Stop listener
                    return False
                if key.char == 'y':
                    # select current face
                    print("y pressed. selecting surface " + str(i))
                    color_nth_advanced_face(path, i, colored)
                    # Stop listener
                    return False
            except:
                pass  # special key pressed
        color_nth_advanced_face(path, i, selected)
        viewer_process = view_stp(full_path)
        sleep(1)
        print("does " + selected + " surface belong to the desired class?: press y or n \n")
        with Listener(on_release=on_release) as listener:
            listener.join()
    viewer_process = view_stp(full_path)
    sleep(1)
    print("(optional) final result. you can close viewer or press enter to close it.")

    # def on_release(key):
    #     if key == Key.enter:
    #         # deselect current face
    #         print("Enter pressed. closing viewer ")
    #         close_stp_viewer(viewer_process)
    #         # Stop listener
    #         return False


#baugruppe bestehend aus mehreren shapes
#je shape "SHAPE_DEFINITION_REPRESENTATION"
#was indiziert NEXT_ASSEMBLY_USAGE_OCCURRENCE
#PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE
p = "../data/Wheelbarrow.stp"
p = "../data/Control_levers_n.stp"
#print(get_highest_hash_entry(extract_lines(p)))
toggle_faces_color(p)


# zuerst mal "Innenzylinder" färben um so Löcher für Schrauben und Nieten zu ermitteln?


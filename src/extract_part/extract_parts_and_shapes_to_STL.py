# based on https://github.com/marcofariasmx/STP-STEP-to-STL-Python-Converter/forks
import pathlib
import time
from functools import partial
from itertools import combinations

import numpy as np
import multiprocessing
import concurrent.futures
import threading
import os.path
import datetime
import os
import platform
import sys
import glob
from os import listdir
from os.path import isfile, join
import numpy


accept_mirrored_parts = True


def near(a, b):
    if accept_mirrored_parts:
        precision = 0.005
    else:
        precision = 0.00001
    return abs(a - b) < precision * a


def compare_length(a, b):
    if accept_mirrored_parts:
        precision = 0.0005
    else:
        precision = 0.0000001
    return abs(len(a) - len(b)) < precision*len(a)


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

#
# Export Root Bodies and Objects Inside Root Groups to STL
#
# This is a FreeCAD script to export all visible root bodies and objects inside root groups in STL mesh format.
# Files will be stored inside an "exported_YYYY-MM-DD_HH-mm-ss" subfolder and named as "documentname_groupname_bodylabel.stl" or "documentname_bodylabel.stl".
#


def export_shape(file_path, shape):
    suffix = '.' + str(file_path).split('.')[-1]
    without_suffix = str(file_path).removesuffix(suffix)
    new_name = without_suffix + "_" + str(shape.Name) + ".stl"
    shape.exportStl(new_name)
    # doc = App.newDocument('Doc')
    # pf = doc.addObject("Part::Feature", "MyShape")
    # pf.Shape = shape
    # Mesh.export([pf], new_name)


def shapes_equal(a, b):       # this would copy every shape to compare with each other
                                                    # leading to n^2 copies
    if near(a.Volume, b.Volume):
        a.transformShape(a.Placement.inverse().toMatrix(), True)
        b.transformShape(b.Placement.inverse().toMatrix(), True)
        common = a.common(b)
        if near(a.Volume, common.Volume):
            return True     # parts overlay each other well
        if near(a.MemSize, b.MemSize) and near(a.Area, b.Area) and compare_length(a.Edges, b.Edges) and compare_length(a.Faces, b.Faces) and compare_length(a.Wires, b.Wires) and compare_length(a.Vertexes, b.Vertexes) and near(a.Length, b.Length) and near(a.Mass, b.Mass):
            return True     # parts are probably rotated but have similar characteristics
    return False


def find_duplicates_in_chunk(start_index, shapes_in_zero_placement, shapes_volumes, labels, shapes_duplicates):
    for a in range(start_index, len(shapes_in_zero_placement)):
        sha_a = shapes_in_zero_placement[a]
        a_volume = shapes_volumes[a]
        for b in range(a + 1, len(shapes_in_zero_placement)):
            sha_b = shapes_in_zero_placement[b]
            b_volume = shapes_volumes[b]
            if shapes_equal(sha_a, sha_b):
                print(f"duplicate tuple: {labels[a]} , {labels[b]}")
                # shapes_duplicates[b] = 1


def retrieve_objects_from_freecad(file_path):
    App.addImportType("STEP with colors (*.step *.stp)", "Import")
    App.loadFile(file_path)
    doc = App.activeDocument()

    # shapes = [o.Shape for o in doc.Objects if (hasattr(o, 'Shape') and o.Shape.Solids
    #                                            and not o.isDerivedFrom('PartDesign::Feature')
    #                                            and not hasattr(o, 'Type'))]
    objects = [o for o in doc.Objects if (hasattr(o, 'Shape') and not o.isDerivedFrom('PartDesign::Feature'))]
    # labels = [o.Label for o in objects]
    return objects


def find_duplicates_for_pairs(a, b, shapes_in_zero_placement, shapes_volumes, labels, shapes_duplicates):
    sha_a = shapes_in_zero_placement[a]
    sha_b = shapes_in_zero_placement[b]

    if shapes_equal(sha_a, sha_b):
        print(f"duplicate tuple: {labels[a]} , {labels[b]}")
        shapes_duplicates[b] = 1


def find_duplicate_ojects(objects, labels, shapes_duplicates, multiprocessor=True):
    shapes = [o.Shape for o in objects]
    shapes_volumes = [s.Volume for s in shapes]
    print("calculated Volumes")

    if multiprocessor:
        # Parallelize shape transformation to zero placement
        with multiprocessing.Pool() as pool:
            shapes_in_zero_placement = pool.map(copy_and_transform_shape, shapes)
    else:
        shapes_in_zero_placement = [copy_and_transform_shape(s) for s in shapes]

    print("transformed to zero placement")

    # Generate all unique (a, b) pairs where a < b
    all_pairs = list(combinations(range(len(shapes_in_zero_placement)), 2))

    # Prepare arguments for each pair to be passed to starmap
    args = [(a, b, shapes_in_zero_placement, shapes_volumes, labels, shapes_duplicates) for a, b in all_pairs]

    if multiprocessor:
        # Parallelize the pairwise comparison across multiple processes
        with multiprocessing.Pool() as pool:
            pool.starmap(find_duplicates_for_pairs, args)
    else:
        for arg in args:
            find_duplicates_for_pairs(*arg)

    return np.array(shapes_duplicates)


def copy_and_transform_shape(s):
    s_copy = s.copy()
    s_copy.Placement = App.Placement(App.Vector(0, 0, 0), App.Vector(0, 0, 0), 0)
    return s_copy


# def find_duplicate_shapes(shapes, labels):           # keeps copy of shape_a and compare with other
#     shapes_duplicates = numpy.zeros(len(shapes))                   # indexes of duplicating shapes
#     shapes_volumes = [s.Volume for s in shapes]
#     print("calculated Volumes")
#     shapes_in_zero_placement = [s.copy() for s in shapes]
#     for s in shapes_in_zero_placement:
#         s.Placement = App.Placement(App.Vector(0, 0, 0), App.Vector(0, 0, 0), 0)
#         # s.transformShape(s.Placement.inverse().toMatrix(), True)   # this might be done in multiprocessing pool
#     print("transformed to zero placement")
#     for a in range(len(shapes_in_zero_placement)):
#         sha_a = shapes_in_zero_placement[a]
#         a_volume = shapes_volumes[a]
#         for b in range(a + 1, len(shapes_in_zero_placement)):
#             sha_b = shapes_in_zero_placement[b]
#             b_volume = shapes_volumes[b]
#             if shapes_equal(sha_a, sha_b):
#                 print("duplicate tuple: " + str(labels[a]) + ' , ' + str(labels[b]))
#                 shapes_duplicates[b] = 1  # we do not include the occurance of b in a
#                 # thus the first occurance is the persistent one
#                 # turning the problem into binary relation
#                 print(shapes_duplicates)
#     return shapes_duplicates


def compare_and_remove_duplicates(sha_a, shapes, start_idx):
    """
    Compare sha_a with all other shapes in the list and remove duplicates.
    """
    shapes_to_remove = []
    vol_a = sha_a.Volume
    for idx in range(start_idx, len(shapes)):
        sha_b = shapes[idx]
        vol_b = sha_b.Volume
        if shapes_equal(sha_a, sha_b):
            shapes_to_remove.append(sha_b)

    # Safely remove duplicates from shapes
    with shapes_lock:
        for sha_b in shapes_to_remove:
            if sha_b in shapes:  # Double-check because another thread might have removed it
                shapes.remove(sha_b)


# Lock for thread-safe modifications to the shapes list
shapes_lock = threading.Lock()


def remove_duplicates_multithreaded(shapes):
    """
    Optimized function to remove duplicate shapes using multithreading.
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks to threads, each thread will compare a shape with others
        futures = []
        for a in range(len(shapes)):
            sha_a = shapes[a]
            # Each thread compares sha_a with the remaining shapes
            future = executor.submit(compare_and_remove_duplicates, sha_a, shapes, a + 1)
            futures.append(future)

        # Ensure all threads are finished
        concurrent.futures.wait(futures)


def isolate_to_stl_excluding_freecad_duplicates(step_file_path, multiprocessor=False):
    start_time = time.time()        # For performance measurements
    step_file_path = os.path.abspath(step_file_path)
    suffix = '.' + str(step_file_path).split('.')[-1]
    without_suffix = str(step_file_path).removesuffix(suffix)

    print("Converting File: " + step_file_path)
    App.addImportType("STEP with colors (*.step *.stp)", "Import")
    App.loadFile(step_file_path)
    doc = App.activeDocument()

    objects = [o for o in doc.Objects if hasattr(o, 'Shape')]   #  and o.Shape.Solids and not o.isDerivedFrom('PartDesign::Feature') and not hasattr(o, 'Type')
    labels = [o.Label for o in objects]

    if multiprocessor:
        # Move Manager outside of the pool
        manager = multiprocessing.Manager()
        shapes_duplicates = manager.list([0] * len(objects))  # Use shared list

        # Find duplicates using multiprocessing
        duplicates = find_duplicate_ojects(objects, labels, shapes_duplicates)
    else:
        shapes_duplicates = []
        duplicates = find_duplicate_ojects(objects, labels, shapes_duplicates)

    # Remove duplicates
    for i in range(len(objects) - 1, -1, -1):
        if duplicates[i]:
            objects.__delitem__(i)

    print(f"{sum(duplicates)} duplicates removed.")
    print(f"{len(objects)} remaining parts.")

    export_dir = None
    for obj in objects:
        export_dir = export_object_to_stl(obj, step_file_path)

    print("done isolating parts.")

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time} seconds")
    return export_dir


# def isolate_to_stl(file_path):
#     file_path = os.path.abspath(file_path)
#     suffix = '.' + str(file_path).split('.')[-1]
#     without_suffix = str(file_path).removesuffix(suffix)
#
#     print("Converting File: " + file_path)
#     App.addImportType("STEP with colors (*.step *.stp)", "Import")
#     App.loadFile(file_path)
#     doc = App.activeDocument()
#
#     # doc.Objects gives us all leaves, we like to remove duplicate parts of same product
#     product_representatives_leaves_uids = set()   # must be a set since we want a single part representing each product
#     product_ids = []
#     shapes = [o.Shape for o in doc.Objects if (
#                 hasattr(o, 'Shape') and o.Shape.Solids and not o.isDerivedFrom('PartDesign::Feature') and not hasattr(o,
#                                                                                                                       'Type'))]
#     objects = [o for o in doc.Objects if (
#                 hasattr(o, 'Shape') and o.Shape.Solids and not o.isDerivedFrom('PartDesign::Feature') and not hasattr(o,
#                                                                                                                       'Type'))]
#     # if len(shapes) >= 1:
#     #     for sha_a in shapes:
#     #         for sha_b in shapes[1:]:                                # compare all other with a
#     #             if shapes_equal(sha_a, sha_b):
#     #                 shapes.remove(sha_b)                            # prevents duplicate stl exports
#     #                 print(len(shapes))
#     labels = [o.Label for o in objects]
#     duplicates = find_duplicate_shapes(shapes, labels)
#
#     for i in range(len(shapes) - 1, -1, -1):
#         if duplicates[i]:
#             shapes.__delitem__(i)
#             objects.__delitem__(i)
#             print(shapes)
#     print(str(sum(duplicates)) + " duplicates removed.")
#     print(str(len(shapes)) + " remaining parts.")
#     # remove_duplicates_multithreaded(shapes)
#
#     for obj in objects:
#         export_object_to_stl(obj, file_path)
#         # # Check if the object is a root object (not used by any other objects)
#         # if not obj.InList:
#         #     if obj.TypeId == 'App::DocumentObjectGroup' or obj.Group is not None:
#         #         # If it's a root group, export objects inside
#         #         for sub_obj in obj.Group:
#         #             export_object_to_stl(sub_obj, without_suffix, prefix=obj.Label + "_")
#         #     else:
#         #         # If it's a single root body
#         #         export_object_to_stl(obj, without_suffix)
#     print("done isolating parts.")
#     return os.path.dirname(file_path)

    # base_path = os.path.dirname(doc.FileName)
    # base_filename = os.path.splitext(os.path.basename(doc.FileName))[0]

    # # Get current date and time in the desired format
    # current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    #
    # # Ensure the "exported_YYYY-MM-DD_HH-mm-ss" subfolder exists
    # export_folder = os.path.join(base_path, f"exported_{current_datetime}")
    # if not os.path.exists(export_folder):
    #     os.makedirs(export_folder)


def export_object_to_stl(obj, file_path, prefix="", export_shells=False):
    if export_shells:
        var = hasattr(obj, 'Shape')
    else:
        var = hasattr(obj, 'Shape') and obj.Shape.ShapeType == 'Solid' and hasattr(obj, 'Visibility') and obj.Visibility
    if var:
        # Remove any non-allowed characters from the label for file naming
        suffix = '.' + str(file_path).split('.')[-1]
        export_folder = str(file_path).removesuffix(suffix)
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)
        sanitized_label = ''.join(e for e in obj.Label if e.isalnum() or e in ['_', '-'])
        filename = os.path.join(export_folder, prefix + "__" + sanitized_label + ".stl")

        obj.Shape.exportStl(filename)
        App.Console.PrintMessage(f"Exported {filename}\n")
        return export_folder
    else:
        print(obj)
        print("object has no Attibute Shape.")


# def convert_dir(path):
#     #files = [f for f in listdir(filesPath) if isfile(join(filesPath, f))]
#     files = []
#     for file in pathlib.Path(path).rglob('*'):
#         if file.is_file():
#             suffix = str(file).split('.')[-1]
#             if suffix.lower() == 'stp' or suffix.lower() == 'step':
#                 files.append(str(file))
#     totalFiles = len(files)
#
#     start_time = time.time()
#
#     pool = multiprocessing.Pool(multiprocessing.cpu_count())
#     temp = partial(isolate_to_stl_excluding_freecad_duplicates)   #mapping works only if all files are in same root
#     print("Pool info: ", pool)
#     result = pool.map(func=temp, iterable=files, chunksize=1)
#     pool.close()
#     pool.join()
#
#     end_time = time.time()
#     print('\n' + "Execution time: ")
#     print(str(end_time - start_time) + " seconds" + '\n')
#     converted_parts_folder = path
#     return converted_parts_folder


#isolate_to_stl_excluding_freecad_duplicates("../../data/convert/gt/screw_or_not/no_screw/from_assemblies/Gas turbine Assembly/4_CompressorBlades_24530_.STEP")
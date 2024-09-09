# based on https://github.com/marcofariasmx/STP-STEP-to-STL-Python-Converter/forks
import pathlib
import time
import multiprocessing

import os.path
import datetime
import os
import platform
import sys
import glob
from functools import partial
from os import listdir
from os.path import isfile, join

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


def isolate_to_stl(file_path):
    file_path = os.path.abspath(file_path)
    suffix = '.' + str(file_path).split('.')[-1]
    without_suffix = str(file_path).removesuffix(suffix)

    print("Converting File: " + file_path)
    App.addImportType("STEP with colors (*.step *.stp)", "Import")
    App.loadFile(file_path)
    doc = App.activeDocument()
    for obj in doc.Objects:
        # Check if the object is a root object (not used by any other objects)
        if not obj.InList:
            if obj.TypeId == 'App::DocumentObjectGroup' or obj.Group is not None:
                # If it's a root group, export objects inside
                for sub_obj in obj.Group:
                    export_object_to_stl(sub_obj, without_suffix, prefix=obj.Label + "_")
            else:
                # If it's a single root body
                export_object_to_stl(obj, without_suffix)
    return os.path.dirname(file_path)

    # base_path = os.path.dirname(doc.FileName)
    # base_filename = os.path.splitext(os.path.basename(doc.FileName))[0]

    # # Get current date and time in the desired format
    # current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    #
    # # Ensure the "exported_YYYY-MM-DD_HH-mm-ss" subfolder exists
    # export_folder = os.path.join(base_path, f"exported_{current_datetime}")
    # if not os.path.exists(export_folder):
    #     os.makedirs(export_folder)


def export_object_to_stl(obj, file_path_without_suffix, prefix=""):
    if hasattr(obj, 'Shape') and obj.Shape.ShapeType == 'Solid' and hasattr(obj, 'Visibility') and obj.Visibility:
        # Remove any non-allowed characters from the label for file naming
        sanitized_label = ''.join(e for e in obj.Label if e.isalnum() or e in ['_', '-'])
        filename = file_path_without_suffix + prefix + sanitized_label + ".stl"
        try:
            obj.Shape.exportStl(filename)
            App.Console.PrintMessage(f"Exported {filename}\n")
        except Exception as e:
            App.Console.PrintError(f"Error exporting {filename}: {str(e)}\n")


def convert_dir(path):
    #files = [f for f in listdir(filesPath) if isfile(join(filesPath, f))]
    files = []
    for file in pathlib.Path(path).rglob('*'):
        if file.is_file():
            suffix = str(file).split('.')[-1]
            if suffix.lower() == 'stp' or suffix.lower() == 'step':
                files.append(str(file))
    totalFiles = len(files)

    start_time = time.time()

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    temp = partial(isolate_to_stl)   #mapping works only if all files are in same root
    print("Pool info: ", pool)
    result = pool.map(func=temp, iterable=files, chunksize=1)
    pool.close()
    pool.join()

    end_time = time.time()
    print('\n' + "Execution time: ")
    print(str(end_time - start_time) + " seconds" + '\n')
    converted_parts_folder = path
    return converted_parts_folder


#isolate("../../data/baugruppen/vespa/src/vesp.stp")

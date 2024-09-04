# based on https://github.com/marcofariasmx/STP-STEP-to-STL-Python-Converter/forks
import pathlib
import time
import multiprocessing
from functools import partial

import os
from os import listdir
from os.path import isfile, join
import platform
import sys
import glob


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


def converter(filesPath, totalFiles, file):
    # totalFiles is unused, was not able to put current number of process.

    # if not os.path.exists(filesPath + "/Converted-STLs"):
    #     os.makedirs(filesPath + "/Converted-STLs")
    #
    # if not os.path.exists(filesPath + "/OriginalFiles"):
    #     os.makedirs(filesPath + "/OriginalFiles")

    suffix = '.' + str(file).split('.')[-1]
    without_suffix = str(file).removesuffix(suffix)
    newName = without_suffix + ".stl"
    if not os.path.exists(newName):
        print("Converting File: " + file)
        shape = Part.Shape()
        shape.read(file)
        doc = App.newDocument('Doc')
        pf = doc.addObject("Part::Feature", "MyShape")
        pf.Shape = shape
        Mesh.export([pf], newName)
    #os.replace(filesPath + "/" + file, filesPath + "/OriginalFiles/" + file)


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
    temp = partial(converter, '', totalFiles)   #mapping works only if all files are in same root
    print("Pool info: ", pool)
    result = pool.map(func=temp, iterable=files, chunksize=1)
    pool.close()
    pool.join()

    end_time = time.time()
    print('\n' + "Execution time: ")
    print(str(end_time - start_time) + " seconds" + '\n')
    converted_parts_folder = path
    return converted_parts_folder


# if __name__ == "__main__":
#     main()
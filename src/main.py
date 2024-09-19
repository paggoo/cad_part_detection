from src.classify.classify_screw_no_screw_keras import classify_assembly_screw_no_screw_keras
from src.classify.classify_screw_no_screw_torch import classify_assembly_screw_no_screw_torch
from src.extract_part.extract_parts_and_shapes_to_STL import isolate_to_stl_excluding_freecad_duplicates
from src.generate_datasets.generate_dataset_for_classification_screw_no_screw import generate_dataset_to_classify
from src.generate_ground_truth.build_dictionaries import make_screw_gt_dictionary
from src.generate_datasets.generate_gt_dataset_from_dictionary import build_gt_dataset
from src.train_classifier.mvcnn_screw_no_screw_torch import train_classifier_screw_no_screw_torch

# def extract_features(p):        # TODO
#     for file_name in os.listdir(p):
#         if not file_name.__contains__("_raw"):
#             export_path = os.path.join(p, file_name)
#             import_export(export_path)
#
#
# path = "../data/products"

# train workflow:
# # 0. isolate one part per product
# isolate_folder()
# # 1. stp -> stl
# # convert_dir("../data/convert/gt/screw_or_not/")
#     # deprecated. now covered by isolate()
# # 2. create dict
# make_screw_gt_dictionary("../data/convert/gt/screw_or_not/", "screw", "no_screw")
# # 3. build dataset
# data, labels = build_gt_dataset("../data/convert/gt/screw_or_not/")
# # 3. train net
# train_classifier_screw_no_screw_torch("../data/convert/gt/screw_or_not/",
#                                       "../models/mvcnn_screw_no_screw_torch_model_17Sept.pth")


# # classify workflow:
# # 0. isolate one part per product
# root = isolate_to_stl(step_file_path)
# # 1. stp -> stl
#     # deprecated. now covered by isolate
# # 2. stl -> multiview
# data, labels = generate_dataset_to_classify(root)
# # 3. multiview -> classify
# classify_assembly_screw_no_screw_keras("../data/Clamp_Holdfast_.stp", "../models/mvcnn_screw_no_screw_simpler.keras")
# classify_assembly_screw_no_screw_torch("../data/Clamp_Holdfast_.stp", "../models/mvcnn_torch_model.pth")

# classify_assembly_screw_no_screw_torch("../data/convert/gt/screw_or_not/no_screw/from_assemblies/Gas turbine Assembly.STEP", "../models/mvcnn_screw_no_screw_torch_model_11Sept.pth")
# classify_assembly_screw_no_screw_torch("../data/convert/gt/screw_or_not/no_screw/from_assemblies/Dental Drill.step", "../models/mvcnn_screw_no_screw_torch_model_11Sept.pth")
# classify_assembly_screw_no_screw_torch("../data/convert/gt/screw_or_not/no_screw/from_assemblies/FORKLIFT.stp", "../models/mvcnn_screw_no_screw_torch_model_11Sept.pth")
# classify_assembly_screw_no_screw_torch("../data/convert/gt/screw_or_not/no_screw/from_assemblies/THERMOSTAT ASSY (19301-PAA-306).STEP", "../models/mvcnn_screw_no_screw_torch_model_11Sept.pth")

# classify_assembly_screw_no_screw_torch("../data/baugruppen/MQ135_MH_sensor_with_socket_pins_90grd.STEP", "../models/mvcnn_screw_no_screw_torch_model_11Sept.pth")
# classify_assembly_screw_no_screw_torch("../data/baugruppen/Piston assembly1.stp", "../models/mvcnn_screw_no_screw_torch_model_17Sept.pth")
# classify_assembly_screw_no_screw_torch("../data/baugruppen/Tray Mould Assembly.STEP", "../models/mvcnn_screw_no_screw_torch_model_17Sept.pth")
classify_assembly_screw_no_screw_torch("../data/baugruppen/Scara Robot.step", "../models/mvcnn_screw_no_screw_torch_model_17Sept.pth")

import os
from subprocess import Popen, PIPE
import numpy as np
import pyvista as pv
import meshio
from matplotlib import pyplot as plt


def get_density_for_axis(min_value, max_value, target_points=80):
    return (max_value - min_value) / target_points


def stl_to_multiview(path, view_size: int, debug=False):
    # path = str(os.path.realpath(path))
    if debug:
        print("path to read: " + str(path))
    mesh = pv.read(path)
    # mask = get_array(mesh, mesh.length / 150)
    # mask = get_array(mesh, .3)              # fix density unwanted since gives bigger pic for big parts
    # mask = get_array(mesh, sum(mesh.bounds)*.01 / len(mesh.bounds))
    mask = get_array(mesh, view_size)

    if mask is None:
        return None, None, None
    x, y, z = mask.sum(0), mask.sum(1), mask.sum(2)
    if debug:
        plt.imshow(x)
        plt.show()
        plt.imshow(y)
        plt.show()
        plt.imshow(z)
        plt.show()
    return x, y, z


# mesh_ = pv.read("../../gt/washer/plain/stl.stl")
# mesh_ = pv.read("../../data/convert/gt/screw_or_not/no_screw/nut/hex/1 18 - 7 UNC_67738__67709.stl")
# mesh_ = pv.read("../../data/convert/gt/screw_or_not/screw/screw/head shape/bugle/philips/wood/BHDkS Coarse, 6 x 1.25.ipt.stl")

#cpos = mesh_.plot()
#vox = pv.voxelize(mesh_, density=mesh_.length / 200)
#vox.plot()

    #
    # x_min, x_max, y_min, y_max, z_min, z_max = mesh.bounds
    # x = np.arange(x_min, x_max, density)
    # y = np.arange(y_min, y_max, density)
    # z = np.arange(z_min, z_max, density)
    # x, y, z = np.meshgrid(x, y, z)
    #
    # # Create unstructured grid from the structured grid
    # grid = pv.StructuredGrid(x, y, z)
    # ugrid = pv.UnstructuredGrid(grid)
    #
    # # get part of the mesh within the mesh's bounding surface.
    # selection = ugrid.select_enclosed_points(mesh.extract_surface(),
    #                                          tolerance=0.0,
    #                                          check_surface=False)
    # mask = selection.point_data['SelectedPoints'].view(bool)
    # pv.plot(ugrid.points, scalars=mask.astype(int))


def get_array(mesh: pv.PolyData, view_size: int):
    x_min, x_max, y_min, y_max, z_min, z_max = mesh.bounds
    density_x = get_density_for_axis(x_min, x_max, target_points=view_size)
    density_y = get_density_for_axis(y_min, y_max, target_points=view_size)
    density_z = get_density_for_axis(z_min, z_max, target_points=view_size)
    # if density <= 0:
    #     print("low density!")
    #     return None
    # density = (mesh.bounds[1] - mesh.bounds[0]) * 0.1
    x = np.arange(x_min, x_max, density_x)
    y = np.arange(y_min, y_max, density_y)
    z = np.arange(z_min, z_max, density_z)
    x, y, z = np.meshgrid(x, y, z)

    # Create unstructured grid from the structured grid
    grid = pv.StructuredGrid(x, y, z)
    ugrid = pv.UnstructuredGrid(grid)

    # get part of the mesh within the mesh's bounding surface.
    selection = ugrid.select_enclosed_points(mesh.extract_surface(),
                                            tolerance=0.0,
                                            check_surface=False)
    mask = selection['SelectedPoints'].view(bool)
    mask = mask.reshape(x.shape, order='F')
    mask = np.array(mask)
    return mask


# mask_ = get_array(mesh_, mesh_.length/100)
# here is the array dependend on voxalised shape of the part
# screw for instance can be 25x25x100
# washer can be 5x45x45
# how to normalize this to have a fixed dataset shape?
# streching it all to e.g. 100x100x100 might be our best bet
#mask_ = mask_.stretch...
# idea: multiview
# first simple the 3 axis, but summed up (this might be enough for classification)

#fig, axes = plt.subplots(1, 3)

# x = mask_.sum(0)
# y = mask_.sum(1)
# z = mask_.sum(2)

# axes[0].imshow(x)
# axes[0].set_title('Sum along X-axis')
# axes[1].imshow(y)
# axes[1].set_title('Sum along Y-axis')
# axes[2].imshow(z)
# axes[2].set_title('Sum along Z-axis')
# plt.show()
#
# # # Plot mask in 3D with matplotlib
# mask = np.transpose(mask, (1, 2, 0))
# xs, ys, zs = np.where(mask)
#
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.voxels(mask)
# ax.set_xlabel('X')
# ax.set_ylabel('Y')
# ax.set_zlabel('Z')
# ax.set_box_aspect((np.ptp(xs), np.ptp(ys), np.ptp(zs)))  # aspect ratio is 1:1:1 in data space
#
# plt.show()


# a, b, c = stl_to_multiview(os.path.abspath("../../data/convert/gt/screw_or_not/no_screw/nut/hex/1 18 - 7 UNC_67738__67709.stl"), True)
# pass
# x,y,z = stl_to_multiview(os.path.abspath("../../data/convert/gt/screw_or_not/no_screw/nut/hex/1 38 - 6 UNC_43167__43138.stl"), True)

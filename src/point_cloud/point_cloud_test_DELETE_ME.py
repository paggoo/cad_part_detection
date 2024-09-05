from pyntcloud import PyntCloud
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

point_cloud = np.loadtxt("../../data/schraube1.asc")
#point_cloud = np.loadtxt("../../gt/washer/plain/points.asc")

print(point_cloud.shape)
print(point_cloud[1])
#v = pptk.viewer(point_cloud)


df = pd.DataFrame(data=point_cloud, columns=['x', 'y', 'z'])
cloud = PyntCloud(df)
print(cloud)

#cloud.plot(point_size=0.1, opacity=0.6)

voxelgrid_id = cloud.add_structure("voxelgrid", n_x=512, n_y=512, n_z=512)
voxelgrid = cloud.structures[voxelgrid_id]

voxelgrid.plot(d=3, mode="density", cmap="hsv")

Binary_voxel_array = voxelgrid.get_feature_vector(mode="binary")
print(Binary_voxel_array.shape)

plt.imshow(Binary_voxel_array[200, :, :], cmap='grey')
plt.show()
plt.imshow(Binary_voxel_array[:, 300, :], cmap='grey')
plt.show()
plt.imshow(Binary_voxel_array[:, :, 250], cmap='gray')
plt.show()
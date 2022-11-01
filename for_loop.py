import pydicom as dicom
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy import ndimage

path="D:\image modalities\project\Head"

#returns a list containing the names of the images in the directory given by path. The list is in arbitrary order
images=os.listdir(path)

#Reading the images 
slices = [dicom.read_file(path+'/'+s,force=True) for s in images]

#sorting files ,            ImagePositionPatient>>   The x, y, and z coordinates of the upper left hand corner, so we are taking Z coordinates
#The z-axis is increasing toward the head of the patient. and that is how we sort it 
slices = sorted(slices,key=lambda x:x.ImagePositionPatient[2])

#getting the shape of the image
img_shape = list(slices[0].pixel_array.shape)
#adding size of the slices to the shape
img_shape.append(len(slices))
#creating zeros of same shape as image
volume3d=np.zeros(img_shape)

#filling the volume 3d with the values of each of the slices
for i,s in enumerate(slices):
    array2D=s.pixel_array
    volume3d[:,:,i]= array2D
    

#####################################################3
Figure=plt.subplot(1,1,1)
plt.title("Axial")

for i in range(img_shape[2]):
    plt.clf() 
    plt.imshow(volume3d[:,:,i],cmap='gray')
    plt.draw()
    plt.pause(0.0001)
plt.close()

Figure=plt.subplot(1,1,1)
plt.title("Sagital")

for i in range(img_shape[2]):
    rotated=ndimage.rotate(volume3d[:,i,:],angle=90)
    plt.clf() 
    plt.imshow(rotated,cmap='gray')
    plt.pause(0.01)  

plt.close()

Figure=plt.subplot(1,1,1)
plt.title("Coronal")
for i in range(img_shape[2]):
    rotated=ndimage.rotate(volume3d[i,:,:],angle=90)
    plt.clf() 
    plt.imshow(rotated,cmap='gray')
    plt.pause(0.01)
plt.close()

##################################################







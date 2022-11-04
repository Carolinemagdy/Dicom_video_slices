import pydicom as dicom
import numpy as np
import matplotlib.pyplot as plt
import os
import matplotlib.animation as ani

path=".\Head"

#returns a list containing the names of the images in the directory given by path. The list is in arbitrary order
images=os.listdir(path)

#Reading the images 
slices = [dicom.dcmread(path+'/'+image) for image in images]
#sorting the images with respect to Z axis
sorted_slices = sorted(slices,key=lambda x:x.ImagePositionPatient[2])

#filling the volume 3d with the values of each of the slices

#getting the shape of the image
img_shape = list(slices[0].pixel_array.shape)
#adding size of the slices to the shape
img_shape.append(len(slices))
#creating zeros of same shape as image
volume3d = np.zeros(img_shape)

#filling the volume 3d with the values of each of the slices
for i,s in enumerate(slices):
    array2D=s.pixel_array
    volume3d[:,:,i]= array2D



#Axial moving along Z axis
def animation(volume3d):
    fig = plt.figure(1)
    plt.title("Axial")
    #intial image
    anim = plt.imshow(volume3d[:,:,0], cmap=plt.cm.gray)
    plt.grid(False)
    #updating frames of the image
    def update(i):
        anim.set_array(volume3d[:,:,i])
        anim.autoscale()
        return anim,
    #calling funcanimation function and giving  it the fig to show on it and the frames to update the image with the update function 
    a = ani.FuncAnimation(fig, update, frames=volume3d.shape[2], interval=0.1, blit=True,repeat=False)
    plt.show()

animation(volume3d)

#Sagital moving along Y axis
def animation(volume3d):
    fig = plt.figure(1)
    plt.title("Sagital")
    #intial stage of image
    anim = plt.imshow(volume3d[:,0,:], cmap=plt.cm.gray)
    plt.grid(False)
    #updating frames of the image
    def update(i):
        anim.set_array(volume3d[:,i,:])
        anim.autoscale()
        return anim,
    #calling funcanimation function and giving  it the fig to show on it and the frames to update the image with the update function 
    a = ani.FuncAnimation(fig, update, frames=volume3d.shape[1], interval=0.1, blit=True,repeat=False)
    plt.show()
    
animation(volume3d)


# Coronal moving along X axis
def animation(volume3d):
    fig = plt.figure(1)
    plt.title("Coronal")
    #intial stage of image
    anim = plt.imshow(volume3d[0,:,:], cmap=plt.cm.gray)
    plt.grid(False)
    #updating frames of the image
    def update(i):
        anim.set_array(volume3d[i,:,:])
        anim.autoscale()
        # plt.show()
        return anim,
    #calling funcanimation function and giving  it the fig to show on it and the frames to update the image with the update function 
    a = ani.FuncAnimation(fig, update, frames=volume3d.shape[0], interval=0.1, blit=True,repeat=False)
    plt.show()
animation(volume3d)







from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
from PyQt5 import QtCore
import os 
import sys
import pydicom as dicom
import numpy as np
from PyQt5.uic import loadUiType
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.lines as lines
matplotlib.use('Qt5Agg')

ui,_ = loadUiType(os.path.join(os.path.dirname(__file__),'dicom_viewer_ui.ui'))

class Dicom_Viewer_App(QMainWindow , ui):
    def __init__(self , parent=None):
        super(Dicom_Viewer_App , self).__init__(parent)
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.Handle_Buttons()
        self.dicom_path=''
        self.volume3d=''
        self.axial_x=0
        self.axial_y=0
        

    def Handle_Buttons(self):
        '''Initializing interface buttons'''
        self.browse_button.clicked.connect(self.Browse)
        self.browse_button_2.clicked.connect(self.Browse)
        self.reset_button.clicked.connect(self.reset)
        

    def Browse(self):
        '''Browse to get Dicom Folder'''
        #Getting folder path
        self.dicom_path = QFileDialog.getExistingDirectory(self,"Select Dicom Folder",directory='.')
        print(self.dicom_path)
        self.browse_bar.setText(self.dicom_path)
        #check if folder was selected
        if self.dicom_path !='':
            self.build_3D_volume()
        else:
            self.dicom_path=''
            return

    def build_3D_volume(self):
        '''Construct 3D volume from dicom slices'''
        images=os.listdir(self.dicom_path)

        #Reading the images 
        slices = [dicom.dcmread(self.dicom_path+'/'+image) for image in images]
        #sorting the images with respect to Z axis
        sorted_slices = sorted(slices,key=lambda x:x.ImagePositionPatient[2])

        #filling the volume 3d with the values of each of the slices

        #getting the shape of the image
        img_shape = list(slices[0].pixel_array.shape)
        #adding size of the slices to the shape
        img_shape.append(len(slices))
        #creating zeros of same shape as image
        self.volume3d = np.zeros(img_shape)

        #filling the volume 3d with the values of each of the slices
        for i,s in enumerate(slices):
            array2D=s.pixel_array
            self.volume3d[:,:,i]= array2D

        #Axial Canvas
        self.axial_fig,self.axial_axes = self.canvas_setup(397,305,self.axial_view)
        self.axial_axes.imshow(self.volume3d[:,:,0], cmap='gray')
        # _ = self.axial_fig.canvas.mpl_connect('button_press_event', self.onclick_axial)
        #Adding Lines
        self.h_line = lines.Line2D((0,512),(256,256),picker=5)
        self.v_line = lines.Line2D((256,256),(0,512),picker=5)
        self.d_line = lines.Line2D((0,512),(512,0),picker=5)

        self.axial_axes.add_line(self.h_line) 
        self.axial_axes.add_line(self.v_line)
        self.axial_axes.add_line(self.d_line)

        self.update(self.axial_fig)

        _ = self.axial_fig.canvas.mpl_connect('pick_event', self.clickonline)
        
        #Sagital Canvas
        self.sagital_fig,self.sagital_axes = self.canvas_setup(397,305,self.sagital_view)
        rotated_sagital_matrix = self.rotate_matrix(self.volume3d[:,256,:])
        self.sagital_axes.imshow(rotated_sagital_matrix, cmap='gray')

        #Coronal Canvas
        self.coronal_fig,self.coronal_axes = self.canvas_setup(397,305,self.coronal_view)
        rotated_coronal_matrix = self.rotate_matrix(self.volume3d[256,:,:])
        self.coronal_axes.imshow(rotated_coronal_matrix, cmap='gray')

    def rotate_matrix(self,matrix):
        return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0])-1,-1,-1)]
    
    # pick line when I select it 
    def clickonline(self, event):
        '''Picks line on canvas'''
        self.clicked_line = event.artist
        if self.clicked_line == self.d_line:
            self.pivot_xdata, self.pivot_ydata = event.mouseevent.xdata, event.mouseevent.ydata
        self.follower = self.axial_fig.canvas.mpl_connect("motion_notify_event", self.followmouse)
        self.releaser = self.axial_fig.canvas.mpl_connect("button_press_event", self.releaseonclick)

    # The selected line must follow the mouse
    def followmouse(self, event):
        '''Update lines as mouse moves'''
        if self.clicked_line == self.h_line:
            self.h_line.set_ydata([event.ydata, event.ydata])
        elif self.clicked_line == self.v_line:
            self.v_line.set_xdata([event.xdata, event.xdata])
        else :
            y=(event.xdata) + (event.ydata)
            x=(event.xdata) + (event.ydata)
            self.d_line.set_xdata([0, x])
            self.d_line.set_ydata([y, 0])
            # y=event.ydata
            # x=event.xdata
            # xdata,ydata = self.d_line.get_data()
            # self.d_line.set_xdata([self.pivot_xdata, x])
            # self.d_line.set_ydata([self.pivot_ydata,y])
            # from scipy.stats import linregress
            # intercept = linregress(xdata, ydata).intercept
            # slope = linregress(xdata, ydata).slope
            # print(slope,intercept)
            # self.d_line.set_xdata([0,self.pivot_xdata, x])
            # self.d_line.set_ydata([intercept,self.pivot_ydata,y])
        self.update(self.axial_fig)


        
        
    def releaseonclick(self, event):
        '''Update Slices according to position of the lines'''
        
        self.axial_y = round(self.h_line.get_ydata()[0])
        self.axial_x = round(self.v_line.get_xdata()[0])

        #Update Sagital
        if self.clicked_line == self.v_line:
            rotated_sagital_matrix = self.rotate_matrix(self.volume3d[:,self.axial_x,:])
            self.sagital_axes.imshow(rotated_sagital_matrix, cmap='gray')
            self.update(self.sagital_fig)
        #Update Coronal
        else:
            rotated_coronal_matrix = self.rotate_matrix(self.volume3d[self.axial_y,:,:])
            self.coronal_axes.imshow(rotated_coronal_matrix, cmap='gray')
            self.update(self.coronal_fig)
        
        self.axial_fig.canvas.mpl_disconnect(self.releaser)
        self.axial_fig.canvas.mpl_disconnect(self.follower) 
        
    def canvas_setup(self,fig_width,fig_height,view,bool=True):
        '''Setting up a canvas to view an image in its graphics view'''
        scene= QGraphicsScene()
        figure = Figure(figsize=(fig_width/90, fig_height/90),dpi = 90)
        canvas = FigureCanvas(figure)
        axes = figure.add_subplot()
        scene.addWidget(canvas)
        view.setScene(scene)
        if bool ==True:
            figure.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
            axes.get_xaxis().set_visible(False)
            axes.get_yaxis().set_visible(False)
        else:
            axes.get_xaxis().set_visible(True)
            axes.get_yaxis().set_visible(True)
        return figure,axes
    
    def update(self,axis):
        '''Update Canvas'''
        axis.canvas.draw_idle()
        axis.canvas.flush_events()

    def reset(self):
        if self.dicom_path=='':
            return
        #Reset Lines
        self.h_line.set_ydata([256, 256])
        self.v_line.set_xdata([256, 256])
        self.d_line.set_xdata([0, 512])
        self.d_line.set_ydata([512, 0])
        self.update(self.axial_fig)
        
        #Reset Sagital
        
        rotated_sagital_matrix = self.rotate_matrix(self.volume3d[:,256,:])
        self.sagital_axes.imshow(rotated_sagital_matrix, cmap='gray')        
        self.update(self.sagital_fig)
        #Reset Coronal
        rotated_coronal_matrix = self.rotate_matrix(self.volume3d[256,:,:])
        self.coronal_axes.imshow(rotated_coronal_matrix, cmap='gray')
        self.update(self.coronal_fig)

    # def onclick_axial(self,event):
    #     self.axial_x, self.axial_y = round(event.xdata), round(event.ydata)
    #     line = self.axial_axes.axvline(x=self.axial_x, visible=True)
    #     self.axial_fig.canvas.draw()
    #     line.remove()

    #     #Update Sagital
    #     self.sagital_axes.imshow(self.volume3d[:,self.axial_x,:], cmap='gray')
    #     self.sagital_fig.canvas.draw()

    #     #Update Coronal
    #     self.coronal_axes.imshow(self.volume3d[self.axial_x,:,:], cmap='gray')
    #     self.coronal_fig.canvas.draw()

    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Dicom_Viewer_App()
    window.show()
    app.exec_()
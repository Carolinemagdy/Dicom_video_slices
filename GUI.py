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
        #Task 1 & 2
        self.browse_button.clicked.connect(self.Browse)
        # self.image_button.clicked.connect(self.create_image)
        # self.color_button.clicked.connect(self.color_image)

        #Task 3
        # self.browse_button_2.clicked.connect(self.Browse)
        # self.zoom_button.clicked.connect(self.zoom)
        # self.zoom_factor.valueChanged.connect(self.value_change)
        # self.zoom_button_2.clicked.connect(lambda : self.tab_widget.setCurrentIndex(3))
        # self.histogram_button.clicked.connect(lambda : self.tab_widget.setCurrentIndex(4))
        # self.zoom_button_3.clicked.connect(self.browse_again)
        # self.zoom_button_5.clicked.connect(self.browse_again)
        # self.equalize_button.clicked.connect(self.equalize)

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
        _ = self.axial_fig.canvas.mpl_connect('button_press_event', self.onclick_axial)
        
        #Sagital Canvas
        self.sagital_fig,self.sagital_axes = self.canvas_setup(397,305,self.sagital_view)
        self.sagital_axes.imshow(self.volume3d[:,0,:], cmap='gray')

        #Coronal Canvas
        self.coronal_fig,self.coronal_axes = self.canvas_setup(397,305,self.coronal_view)
        self.coronal_axes.imshow(self.volume3d[0,:,:], cmap='gray')
        
        
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


    def onclick_axial(self,event):
        self.axial_x, self.axial_y = round(event.xdata), round(event.ydata)
        line = self.axial_axes.axvline(x=self.axial_x, visible=True)
        self.axial_fig.canvas.draw()
        line.remove()

        #Update Sagital
        self.sagital_axes.imshow(self.volume3d[:,self.axial_x,:], cmap='gray')
        self.sagital_fig.canvas.draw()

        #Update Coronal
        self.coronal_axes.imshow(self.volume3d[self.axial_x,:,:], cmap='gray')
        self.coronal_fig.canvas.draw()

    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Dicom_Viewer_App()
    window.show()
    app.exec_()
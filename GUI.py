from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from math import dist
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
        self.x_global=256
        self.y_global=256
        self.z_global=117
        

    def Handle_Buttons(self):
        '''Initializing interface buttons'''
        self.browse_button.clicked.connect(self.Browse)
        self.browse_button_2.clicked.connect(self.Browse)
        self.reset_button.clicked.connect(self.reset)
        

    def Browse(self):
        '''Browse to get Dicom Folder'''
        #Getting folder path
        self.dicom_path = QFileDialog.getExistingDirectory(self,"Select Dicom Folder",directory='.')
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

        # self.volume3d_R = np.rot90(self.volume3d,1,(1,2))
        #Axial Canvas
        self.axial_fig,self.axial_axes = self.canvas_setup(397,305,self.axial_view)
        self.axial_axes.imshow(self.volume3d[:,:,self.z_global], cmap='gray')
        # _ = self.axial_fig.canvas.mpl_connect('button_press_event', self.onclick_axial)

        #Adding Lines to axial plane
        self.h_line_axial = lines.Line2D((0,512),(256,256),picker=5)
        self.v_line_axial = lines.Line2D((256,256),(0,512),picker=5)
        self.d_line = lines.Line2D((0,512),(0,512),picker=5)

        self.axial_axes.add_line(self.h_line_axial) 
        self.axial_axes.add_line(self.v_line_axial)
        self.axial_axes.add_line(self.d_line)

        self.update(self.axial_fig)

        _ = self.axial_fig.canvas.mpl_connect('pick_event', self.clickonline)
        
        #Sagital Canvas
        self.sagital_fig,self.sagital_axes = self.canvas_setup(397,305,self.sagital_view)
        rotated_sagital_matrix = self.rotate_matrix(self.volume3d[:,self.y_global,:])
        self.sagital_axes.imshow(rotated_sagital_matrix, cmap='gray')


        #Adding Lines to sagital plane
        self.h_line_sagital = lines.Line2D((0,512),(128,128),picker=5)
        self.v_line_sagital = lines.Line2D((256,256),(0,512),picker=5)

        self.sagital_axes.add_line(self.h_line_sagital) 
        self.sagital_axes.add_line(self.v_line_sagital)
        self.update(self.sagital_fig)

        _ = self.sagital_fig.canvas.mpl_connect('pick_event', self.clickonline)

        #Coronal Canvas
        self.coronal_fig,self.coronal_axes = self.canvas_setup(397,305,self.coronal_view)
        rotated_coronal_matrix = self.rotate_matrix(self.volume3d[self.x_global,:,:])
        self.coronal_axes.imshow(rotated_coronal_matrix, cmap='gray')

        #Oblique_view Canvas
        self.oblique_fig,self.oblique_axes = self.canvas_setup(397,305,self.oblique_view)
        rotated_oblique_matrix = self.rotate_matrix(self.volume3d[self.x_global,:,:])
        self.oblique_axes.imshow(rotated_oblique_matrix, cmap='gray')

        #Adding Lines to coronal plane
        self.h_line_coronal = lines.Line2D((0,512),(128,128),picker=5)
        self.v_line_coronal = lines.Line2D((256,256),(0,512),picker=5)

        self.coronal_axes.add_line(self.h_line_coronal) 
        self.coronal_axes.add_line(self.v_line_coronal)

        self.update(self.coronal_fig)

        _ = self.coronal_fig.canvas.mpl_connect('pick_event', self.clickonline)

    def rotate_matrix(self,matrix):
        return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0])-1,-1,-1)]
    
    # pick line when I select it 
    def clickonline(self, event):
        '''Picks line on canvas'''
        self.clicked_line = event.artist
        if event.artist == self.d_line:
            self.flag=0
            self.first_point=self.d_line.get_xdata()[0] , self.d_line.get_ydata()[0]
            self.second_point=self.d_line.get_xdata()[1] , self.d_line.get_ydata()[1]
            mouse_event=event.mouseevent
            if dist((mouse_event.xdata,mouse_event.ydata),(self.first_point)) <50: 
                self.flag=1
            elif dist((mouse_event.xdata,mouse_event.ydata),(self.second_point)) <50: 
                self.flag=2

        if self.clicked_line == self.v_line_sagital or self.clicked_line == self.h_line_sagital:
            self.follower_sagital = self.sagital_fig.canvas.mpl_connect("motion_notify_event", self.followmouse)
            self.releaser_sagital = self.sagital_fig.canvas.mpl_connect("button_press_event", self.releaseonclick)
        elif self.clicked_line == self.v_line_coronal or self.clicked_line == self.h_line_coronal:
            self.follower_coronal = self.coronal_fig.canvas.mpl_connect("motion_notify_event", self.followmouse)
            self.releaser_coronal = self.coronal_fig.canvas.mpl_connect("button_press_event", self.releaseonclick)
        elif self.clicked_line == self.v_line_axial or self.clicked_line == self.h_line_axial or self.clicked_line == self.d_line:
            self.follower = self.axial_fig.canvas.mpl_connect("motion_notify_event", self.followmouse)
            self.releaser = self.axial_fig.canvas.mpl_connect("button_press_event", self.releaseonclick)


    # The selected line must follow the mouse
    def followmouse(self, event):
        '''Update lines as mouse moves'''
        if event.ydata == None or event.xdata ==None:
            return        
        if self.clicked_line == self.h_line_axial:
            self.h_line_axial.set_ydata([event.ydata, event.ydata])
            self.v_line_sagital.set_xdata([event.ydata, event.ydata])
            self.x_global=round(event.ydata)
            rotated_coronal_matrix = self.rotate_matrix(self.volume3d[self.x_global,:,:])
            self.coronal_axes.imshow(rotated_coronal_matrix, cmap='gray')
            self.update(self.sagital_fig)
            self.update(self.coronal_fig)
            
        elif self.clicked_line == self.v_line_axial:
            self.v_line_axial.set_xdata([event.xdata, event.xdata])
            self.v_line_coronal.set_xdata([event.xdata, event.xdata])
            self.y_global = round(event.xdata)
            rotated_sagital_matrix = self.rotate_matrix(self.volume3d[:,self.y_global,:])
            self.sagital_axes.imshow(rotated_sagital_matrix, cmap='gray')
            self.update(self.sagital_fig)
            self.update(self.coronal_fig)

        elif self.clicked_line == self.h_line_coronal:
            self.h_line_coronal.set_ydata([event.ydata, event.ydata])

            self.h_line_sagital.set_ydata([event.ydata, event.ydata])
            self.z_global = 234-round(event.ydata)
            self.axial_axes.imshow(self.volume3d[:,:,self.z_global], cmap='gray') 
            self.update(self.sagital_fig)
            self.update(self.coronal_fig)
           
        elif self.clicked_line == self.v_line_coronal:
            self.v_line_coronal.set_xdata([event.xdata, event.xdata])
            
            self.v_line_axial.set_xdata([event.xdata, event.xdata])
            self.y_global = round(event.xdata)
            rotated_sagital_matrix = self.rotate_matrix(self.volume3d[:,self.y_global,:])
            self.sagital_axes.imshow(rotated_sagital_matrix, cmap='gray')
            self.update(self.sagital_fig)
            self.update(self.coronal_fig)

        elif self.clicked_line == self.h_line_sagital:
            self.h_line_sagital.set_ydata([event.ydata, event.ydata])
            self.h_line_coronal.set_ydata([event.ydata, event.ydata])
            self.z_global = 234-round(event.ydata)
            self.axial_axes.imshow(self.volume3d[:,:,self.z_global], cmap='gray')
            self.update(self.sagital_fig)
            self.update(self.coronal_fig)

        elif self.clicked_line == self.v_line_sagital:
            self.v_line_sagital.set_xdata([event.xdata, event.xdata])
            self.h_line_axial.set_ydata([event.xdata, event.xdata])
            self.x_global=round(event.xdata)
            rotated_coronal_matrix = self.rotate_matrix(self.volume3d[self.x_global,:,:])
            self.coronal_axes.imshow(rotated_coronal_matrix, cmap='gray')
            self.update(self.sagital_fig)
            self.update(self.coronal_fig)
    
        if self.clicked_line == self.d_line : 
            if self.flag==1 and event.xdata != self.second_point[0] and event.ydata != self.second_point[1]:
                slope = (self.second_point[1] - event.ydata )/(self.second_point[0]-event.xdata)                    
                        
            elif self.flag==2 and event.xdata != self.first_point[0] and event.ydata != self.first_point[1]:
                slope = (self.first_point[1] - event.ydata )/(self.first_point[0]-event.xdata)
                
            elif self.flag==0:
                slope = (self.d_line.get_ydata()[1] -self.d_line.get_ydata()[0] ) / (self.d_line.get_xdata()[1] -self.d_line.get_xdata()[0] )
            y1=512 
            x1=((y1 -(event.ydata))/slope) + (event.xdata)
            if x1 <0 or x1> 512 :
                x1=0
                y1=(-1*slope*event.xdata) + (event.ydata)
                if y1 <0 or y1> 512:
                    y1=0
                    x1= (-1 * (event.ydata)/slope) +(event.xdata)
                    x2=512
                    y2=(slope*(512-event.xdata))+ event.ydata
                else:
                    x2=512
                    y2=(slope*(512-event.xdata))+ event.ydata
                    if y2 <0 or y2> 512:
                        y2=0
                        x2= (-1 * (event.ydata)/slope) +(event.xdata)
            else:
                x2=0
                y2=(-1*slope*event.xdata) + (event.ydata)
                if y2 <0 or y2> 512:
                    y2=0
                    x2= (-1 * (event.ydata)/slope) +(event.xdata)
                    if x2 <0 or x2> 512:
                        x2=512
                        y2=(slope*(512-event.xdata))+ event.ydata
            self.points=[]
            x1=int(round(x1))
            x2=int(round(x2))
            y1=int(round(y1))
            y2=int(round(y2))
            c=y1-(slope*x1)
            c=int(round(c))
            if x1>x2:     
                self.d_line.set_xdata([x2, x1,])
                self.d_line.set_ydata([y2, y1])
                for x in range(x2, x1):
                    y = slope*x + c
                    y=int(y)
                    if isinstance(y, int) and (x,y) not in [x2,x1]:
                        self.points.append((x,y))

            elif x1<x2:
                self.d_line.set_xdata([x1, x2])
                self.d_line.set_ydata([y1, y2])
                for x in range(x1, x2):
                    y = slope*x + c
                    y=int(y)
                    if isinstance(y, int) and (x,y) not in [x1,x2]:
                        self.points.append((x,y))
            ###Hna hnzabat el oblique
            
            
            # p1 = np.array([x1, y1,self.z_global])
            # p2 = np.array([x2, y2,self.z_global])
            # p3 = np.array([x1, y1,self.z_global+1])

            # # These two vectors are in the plane
            # v1 = p3 - p1
            # v2 = p2 - p1
            # # the cross product is a vector normal to the plane
            # cp = np.cross(v1, v2)
            # a, b, c = cp
            # # This evaluates a * x3 + b * y3 + c * z3 which equals d
            # d = np.dot(cp, p3)
            # print('The equation is {0}x + {1}y + {2}z = {3}'.format(a, b, c, d))
            # rotated_oblique_matrix = self.rotate_matrix(self.volume3d[#######])
            # self.oblique_axes.imshow(oblique_slice, cmap='gray')
            # self.update(self.oblique_fig)
            
        self.update(self.axial_fig)
            


        
        
    def releaseonclick(self, event):
        '''Update Slices according to position of the lines'''
        
        if self.clicked_line == self.v_line_axial or self.clicked_line == self.h_line_axial or self.clicked_line == self.d_line:
            self.axial_y = round(self.h_line_axial.get_ydata()[0])
            self.axial_x = round(self.v_line_axial.get_xdata()[0])
            if self.clicked_line==self.d_line:
                print(len(self.points))
                oblique_slice=np.zeros((len(self.points),self.volume3d.shape[2]))
                for i in range (self.volume3d.shape[2]):
                    for point in self.points:
                        print(point,"PPPPPPPPPPP")
                        # print(self.volume3d[point[0],point[1],i],"VVVVVVVVVVV")
                        oblique_slice[:,i]=self.volume3d[point[0],point[1],i]
                        self.oblique_axes.imshow(oblique_slice, cmap='gray')
                        self.update(self.oblique_fig)

            #Update Sagital
            if self.clicked_line == self.v_line_axial:
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

        elif self.clicked_line == self.v_line_sagital or self.clicked_line == self.h_line_sagital:
            self.sagital_y = round(self.h_line_sagital.get_ydata()[0])
            self.sagital_x = round(self.v_line_sagital.get_xdata()[0])
            #Update Axial
            if self.clicked_line == self.h_line_sagital:
                self.axial_axes.imshow(self.volume3d[:,:,234-self.sagital_y], cmap='gray')
                self.update(self.axial_fig)
            #Update Coronal
            elif self.clicked_line == self.v_line_sagital:
                rotated_coronal_matrix = self.rotate_matrix(self.volume3d[self.sagital_x,:,:])
                self.coronal_axes.imshow(rotated_coronal_matrix, cmap='gray')
                self.update(self.coronal_fig)
            
            self.sagital_fig.canvas.mpl_disconnect(self.releaser_sagital)
            self.sagital_fig.canvas.mpl_disconnect(self.follower_sagital)

        elif self.clicked_line == self.v_line_coronal or self.clicked_line == self.h_line_coronal:
            self.coronal_y = round(self.h_line_coronal.get_ydata()[0])
            self.coronal_x = round(self.v_line_coronal.get_xdata()[0])
            #Update Axial
            if self.clicked_line == self.h_line_coronal:
                self.axial_axes.imshow(self.volume3d[:,:,234-self.coronal_y], cmap='gray')
                self.update(self.axial_fig)
            #Update Sagital
            if self.clicked_line == self.v_line_coronal:
                rotated_sagital_matrix = self.rotate_matrix(self.volume3d[:,self.coronal_x,:])
                self.sagital_axes.imshow(rotated_sagital_matrix, cmap='gray')
                self.update(self.sagital_fig)
            
            self.coronal_fig.canvas.mpl_disconnect(self.releaser_coronal)
            self.coronal_fig.canvas.mpl_disconnect(self.follower_coronal)
            
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
        self.h_line_axial.set_ydata([256, 256])
        self.h_line_sagital.set_ydata([128, 128])
        self.h_line_coronal.set_ydata([128, 128])
        self.v_line_axial.set_xdata([256, 256])
        self.v_line_coronal.set_xdata([256, 256])
        self.v_line_sagital.set_xdata([256, 256])
        self.d_line.set_xdata([0, 512])
        self.d_line.set_ydata([0, 512])
        self.update(self.axial_fig)
        self.update(self.sagital_fig)
        self.update(self.coronal_fig)
        
        #Reset Axial
        self.axial_axes.imshow(self.volume3d[:,:,117], cmap='gray')        
        self.update(self.axial_fig)
        
        #Reset Sagital
        rotated_sagital_matrix = self.rotate_matrix(self.volume3d[:,256,:])
        self.sagital_axes.imshow(rotated_sagital_matrix, cmap='gray')        
        self.update(self.sagital_fig)
        
        #Reset Coronal
        rotated_coronal_matrix = self.rotate_matrix(self.volume3d[256,:,:])
        self.coronal_axes.imshow(rotated_coronal_matrix, cmap='gray')
        self.update(self.coronal_fig)

        try:
            self.axial_fig.canvas.mpl_disconnect(self.releaser)
            self.axial_fig.canvas.mpl_disconnect(self.follower)
            self.coronal_fig.canvas.mpl_disconnect(self.releaser_coronal)
            self.coronal_fig.canvas.mpl_disconnect(self.follower_coronal)
            self.sagital_fig.canvas.mpl_disconnect(self.releaser_sagital)
            self.sagital_fig.canvas.mpl_disconnect(self.follower_sagital)
        except:
            return
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
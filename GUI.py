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
import ROI as roi # ROI_class.py
from math import pi,atan
import math
matplotlib.use('Qt5Agg')

ui,_ = loadUiType(os.path.join(os.path.dirname(__file__),'dicom_viewer_ui.ui'))

class Dicom_Viewer_App(QMainWindow , ui):
    def __init__(self , parent=None):
        ''' variables initialization'''
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
        self.slope=0
        self.oblique_slice=0
        self.oblique_slice_initial=0
        self.x_coordinates=[]
        self.x_coordinates_=[]
        self.y_coordinates=[]
        self.y_coordinates_=[]

    def Handle_Buttons(self):
        '''Initializing interface buttons'''
        self.browse_button.clicked.connect(self.Browse)
        self.browse_button_2.clicked.connect(self.Browse)
        self.reset_button.clicked.connect(self.reset)
        self.Draw_button.clicked.connect(self.choose_roi)
        self.Distance_button.clicked.connect(self.GetDistance)
        self.Area_button.clicked.connect(self.GetArea)
        self.Ellipse_button.clicked.connect(self.DrawEllipse)
        self.XR_button.clicked.connect(self.get_X_Radius)
        self.YR_button.clicked.connect(self.get_Y_Radius)
        self.Slope_button.clicked.connect(self.GetSlope1)
        self.Slope_button_2.clicked.connect(self.GetSlope2)
        self.Angel_button.clicked.connect(self.GetAngel)
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
        self.axial_image=self.axial_axes.imshow(self.volume3d[:,:,self.z_global], cmap='gray')
        # _ = self.axial_fig.canvas.mpl_connect('button_press_event', self.onclick_axial)

        #Adding Lines to axial plane (vertical ,horizontal and diagonal)
        self.h_line_axial = lines.Line2D((0,512),(256,256),picker=5)
        self.v_line_axial = lines.Line2D((256,256),(0,512),picker=5)
        self.d_line = lines.Line2D((0,512),(0,512),picker=5)

        self.axial_axes.add_line(self.h_line_axial) 
        self.axial_axes.add_line(self.v_line_axial)
        self.axial_axes.add_line(self.d_line)

        self.update(self.axial_fig)
        # call clickonline function when a pick event happes in axial plane 
        _ = self.axial_fig.canvas.mpl_connect('pick_event', self.clickonline)
        
        #Sagital Canvas
        self.sagital_fig,self.sagital_axes = self.canvas_setup(397,305,self.sagital_view)
        rotated_sagital_matrix = self.rotate_matrix(self.volume3d[:,self.y_global,:])
        self.sagital_axes.imshow(rotated_sagital_matrix, cmap='gray')


        #Adding Lines to sagital plane ( vertical and horizontal)
        self.h_line_sagital = lines.Line2D((0,512),(128,128),picker=5)
        self.v_line_sagital = lines.Line2D((256,256),(0,512),picker=5)

        self.sagital_axes.add_line(self.h_line_sagital) 
        self.sagital_axes.add_line(self.v_line_sagital)
        self.update(self.sagital_fig)
        
        # call clickonline function when a pick event happes in sagital plane 
        _ = self.sagital_fig.canvas.mpl_connect('pick_event', self.clickonline)

        #Coronal Canvas
        self.coronal_fig,self.coronal_axes = self.canvas_setup(397,305,self.coronal_view)
        rotated_coronal_matrix = self.rotate_matrix(self.volume3d[self.x_global,:,:])
        self.coronal_axes.imshow(rotated_coronal_matrix, cmap='gray')

        #Oblique_view Canvas
        self.oblique_fig,self.oblique_axes = self.canvas_setup(397,305,self.oblique_view)

        for x in range(0, 512):
            y = 1*x + 0
            y=int(y)
            if isinstance(y, int) and (x,y) not in [0,512]:
                self.x_coordinates_.append(x)
                self.y_coordinates_.append(y)
        # initialize oblique slice by the initial diagonal line        
        self.oblique_slice_initial=np.zeros((self.volume3d.shape[2],512))
        for i in range(self.volume3d.shape[2]):
            self.oblique_slice_initial[i,:]=self.volume3d[self.y_coordinates_,self.x_coordinates_,233-i]
        self.oblique_axes.imshow(self.oblique_slice_initial, cmap='gray')

        #Adding Lines to coronal plane ( horizontal and vertical)
        self.h_line_coronal = lines.Line2D((0,512),(128,128),picker=5)
        self.v_line_coronal = lines.Line2D((256,256),(0,512),picker=5)

        self.coronal_axes.add_line(self.h_line_coronal) 
        self.coronal_axes.add_line(self.v_line_coronal)

        self.update(self.coronal_fig)
        # call clickonline function when a pick event happes in coronal plane 
        _ = self.coronal_fig.canvas.mpl_connect('pick_event', self.clickonline)

    
    def rotate_matrix(self,matrix):
        ''' rotate the 2D plane '''
        return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0])-1,-1,-1)]
    

    #Drawing on the axial image (line,polygon,points of ellipse)
    def choose_roi(self):
        self.Region = roi.new_ROI(self.axial_image)
        
    def GetArea(self):
        #getting Coordinates of all the points
        x,y=self.Region.get_coords()
        n=len(x)
        j=n-1
        Area=0
        #calculate the value  of sholeace formula 
        for i in range(0,n):
            Area+=(x[j]+x[i])*(y[j]-y[i])
            j=i    # j is previous vertex to i
        Area=int(abs(Area/2))
        Area="{:.2f}".format(Area)

        self.Calculation_label.setText("area of polygon\n"+str(Area))


    def GetSlope1(self):
        #getting poitns of line 1 to calculate slope 1
        x,y=self.Region.get_coords()
        self.slopeL1=((y[1]-y[0])/(x[1]-x[0]))
        print(x,y)
        print(self.slopeL1)

    def GetSlope2(self):
        #getting poitns of line 2 to calculate slope 2
        x,y=self.Region.get_coords()
        self.slopeL2=((y[1]-y[0])/(x[1]-x[0]))
        print(self.slopeL2)

    def dot(self,vA, vB):
        return vA[0]*vB[0]+vA[1]*vB[1]
    def GetAngel(self):
        
        # Store the tan value  of the angle
        angle = abs((self.slopeL2 - self.slopeL1) / (1 + self.slopeL1 * self.slopeL2))
    
        # Calculate tan inverse of the angle
        ret = atan(angle)
    
        # Convert the angle from
        # radian to degree
        val = (ret * 180) / pi
    
        # Print the result        
        print(360 - val)
        print(val)

        self.Calculation_label.setText("Acute Angel: "+str(round(val))+"\n"+"obtuse Angel:"+str(round(360 - val)))

    def DrawEllipse(self):
        #getting coordinates of center points
        x,y=self.Region.get_coords()
        u=x     #x-position of the center
        v=y    #y-position of the center
        a=np.abs(self.radius_on_X -x)    #radius on the x-axis
        b=np.abs(self.radius_on_Y -y)   #radius on the y-axis

        t = np.linspace(0, 2*pi, 100)
       
        self.axial_axes.plot(u+a*np.cos(t),v+b*np.sin(t), linewidth=3, color='red')
        area=pi*a*b

        self.update(self.axial_fig)
        self.Calculation_label.setText("ellipse area\n"+str(area))

    def get_X_Radius(self):
        #getting X radius of ellipse
        self.radius_on_X,y=self.Region.get_coords()

    def get_Y_Radius(self):
        #getting y radius of ellipse
        x,self.radius_on_Y=self.Region.get_coords()
    def GetDistance(self):
        #getting corrdinates of line to calculate it's distance using distance formula
        x,y=self.Region.get_coords()
        Distance=np.sqrt((x[1]-x[0])**2+(y[1]-y[0])**2)
        Distance="{:.2f}".format(Distance/3.779528)
        self.Calculation_label.setText("Distance\n"+str(Distance)+"mm/pixel")
        print(Distance)

    # pick line when I select it 
    def clickonline(self, event):
      
        '''Picks line on canvas'''
        self.clicked_line = event.artist
        if event.artist == self.d_line:
            self.flag=0
            # get the vertices of the diagonal line
            self.first_point=self.d_line.get_xdata()[0] , self.d_line.get_ydata()[0]
            self.second_point=self.d_line.get_xdata()[1] , self.d_line.get_ydata()[1]
            mouse_event=event.mouseevent
            # get which point  on the diagonal line is clicked by a distance less than 50
            if dist((mouse_event.xdata,mouse_event.ydata),(self.first_point)) <50: 
                self.flag=1
            elif dist((mouse_event.xdata,mouse_event.ydata),(self.second_point)) <50: 
                self.flag=2
        # check each event to connect it to its plane
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
        '''Update lines and planes as mouse moves'''
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
        try:
            if self.clicked_line == self.d_line : 
                # check which point is selected or the whole diagonal line
                # calculate the slope by having the two points
                if self.flag==1 and event.xdata != self.second_point[0] and event.ydata != self.second_point[1]:
                    slope = (self.second_point[1] - event.ydata )/(self.second_point[0]-event.xdata)                    
                            
                elif self.flag==2 and event.xdata != self.first_point[0] and event.ydata != self.first_point[1]:
                    slope = (self.first_point[1] - event.ydata )/(self.first_point[0]-event.xdata)
                    
                elif self.flag==0:
                    slope = (self.d_line.get_ydata()[1] -self.d_line.get_ydata()[0] ) / (self.d_line.get_xdata()[1] -self.d_line.get_xdata()[0] )
            # intersect the new clicked line with each frame of the image to extend the line from 0 to 512 
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
                # oblique slice calculations
                self.x_coordinates=[]
                self.y_coordinates=[]
                x1=int(round(x1))
                x2=int(round(x2))
                y1=int(round(y1))
                y2=int(round(y2))
                #calculate c (intercepted part) from the equation of line
                c=y1-(slope*x1)
                c=int(round(c))
                # check which difference is bigger to have the points along the line
                if abs(x1-x2)>= abs(y1-y2):
                    if x1>x2:     
                        self.d_line.set_xdata([x2, x1,])
                        self.d_line.set_ydata([y2, y1])
                        # get ell the points that belong to this equation of line
                        for x in range(x2, x1):
                            y = slope*x + c
                            y=int(y)
                            if isinstance(y, int) and (x,y) not in [x2,x1]:
                                self.x_coordinates.append(x)
                                self.y_coordinates.append(y)
                    elif x1<x2:
                        self.d_line.set_xdata([x1, x2])
                        self.d_line.set_ydata([y1, y2])
                        for x in range(x1, x2):
                            y = slope*x + c
                            y=int(y)
                            if isinstance(y, int) and (x,y) not in [x1,x2]:
                                self.x_coordinates.append(x)
                                self.y_coordinates.append(y)
                else:
                    if y1>y2:     
                        self.d_line.set_xdata([x2, x1,])
                        self.d_line.set_ydata([y2, y1])
                        for y in range(y2, y1):
                            x = (y - c)/slope
                            x=int(x)
                            if isinstance(x, int) and (x,y) not in [y2,y1]:
                                self.x_coordinates.append(x)
                                self.y_coordinates.append(y)


                    elif y2>y1:     
                        self.d_line.set_xdata([x1, x2,])
                        self.d_line.set_ydata([y1, y2])
                        for y in range(y1, y2):
                            x = (y - c)/slope
                            x=int(x)
                            if isinstance(x, int) and (x,y) not in [y1,y2]:
                                self.x_coordinates.append(x)
                                self.y_coordinates.append(y)
            self.oblique_slice=np.zeros((self.volume3d.shape[2],len(self.x_coordinates)))
            # loop over each slice of z with the same points of x and y
            for i in range(self.volume3d.shape[2]):
                self.oblique_slice[i,:]=self.volume3d[self.y_coordinates,self.x_coordinates,233-i]
            self.oblique_axes.imshow(self.oblique_slice, cmap='gray')
            self.update(self.oblique_fig)            
            self.update(self.axial_fig)
        except:
            return    


        
        
    def releaseonclick(self, event):
        '''Update Slices according to position of the lines'''
        
        if self.clicked_line == self.v_line_axial or self.clicked_line == self.h_line_axial or self.clicked_line == self.d_line:
            self.axial_y = round(self.h_line_axial.get_ydata()[0])
            self.axial_x = round(self.v_line_axial.get_xdata()[0])
            

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
        self.update(self.oblique_fig)
        
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

        #Reset oblique
        # rotated_oplique_matrix = self.rotate_matrix(self.volume3d[256,:,:])
        self.oblique_axes.imshow(self.oblique_slice_initial, cmap='gray')
        self.update(self.oblique_fig)

        try:
            self.axial_fig.canvas.mpl_disconnect(self.releaser)
            self.axial_fig.canvas.mpl_disconnect(self.follower)
            self.coronal_fig.canvas.mpl_disconnect(self.releaser_coronal)
            self.coronal_fig.canvas.mpl_disconnect(self.follower_coronal)
            self.sagital_fig.canvas.mpl_disconnect(self.releaser_sagital)
            self.sagital_fig.canvas.mpl_disconnect(self.follower_sagital)
        except:
            return    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Dicom_Viewer_App()
    window.show()
    app.exec_()
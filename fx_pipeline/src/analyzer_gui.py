from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import ttk
from tkinter import *
from tkinter.ttk import *
import tkinter as tk

from PIL import Image, ImageTk
from skimage import io
import pandas as pd
import numpy
import sys,os
import csv
import cv2
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from image_video_processing import *

class AnalysisConfigurer:
    # configuration
    def __init__(self,root):    
        self.settings = {}   
        self.display_funcs = {
            'phenotype'                 :   'self.display_phenotype()',
            'animal'                    :   'self.display_animal()',
            'day'                       :   'self.display_day()',
            'field1'                    :   'self.display_field1()',
            'group1'                    :   'self.display_group1()',
            'videopath'                 :   'self.display_selected_videofile()',
            'FPS'                       :   'self.display_FPS()',
            'topview_frame_0'           :   'self.display_topview_roi()',
            'topview_xmin'              :   'self.display_topview_roi()',
            'topview_ymin'              :   'self.display_topview_roi()',
            'topview_width'             :   'self.display_topview_roi()',
            'topview_height'            :   'self.display_topview_roi()',            
            'topview_thresh_level'      :   'self.display_topview_thresh()',            
            'topview_thresh_blocksize'  :   'self.display_topview_thresh()',            
            'interval type'             :   'self.display_intervaltype_selection()',
            'analysis start'            :   'self.display_startAn()',            
            'analysis stop'             :   'self.display_stopAn()',
            'stim_frame_0'              :   'self.display_selected_videofile()',
            'stim_xmin'                 :   'self.display_stim_roi()',
            'stim_ymin'                 :   'self.display_stim_roi()',
            'stim_width'                :   'self.display_stim_roi()',
            'stim_height'               :   'self.display_stim_roi()',
            'stim_thresh_level'         :   'self.display_stim_thresh()',
            'approx. trial times'       :   'self.display_trialtimes()', 
            'shadow on times'           :   'self.display_trialtimes()', 
            'shadow off times'          :   'self.display_trialtimes()', 
            'shelter_xmin'              :   'self.display_shelter_roi()',
            'shelter_ymin'              :   'self.display_shelter_roi()',
            'shelter_width'             :   'self.display_shelter_roi()',
            'shelter_height'            :   'self.display_shelter_roi()',
            'arena_corners'             :   'self.display_arena_corners()',
        }
        
        self.root = tk.Toplevel()
        self.root.iconbitmap('../gui/icon1.ico')
        self.root.title('Configure Analysis')
        
        # MAIN WINDOW LAYOUT
        fr_buttons = Frame(self.root)
        fr_tab = Frame(self.root)
        
        # BUTTONS
        fr_buttons.grid(row=0, column=0, sticky='ns')
        fr_tab.grid(row=0,column=1,sticky='nw')
        
        btn_load        = ttk.Button(fr_buttons, text='Load Settings',command = self.load_settings_file).grid(row=0, column=0, sticky='ew', padx=5)
        btn_save        = ttk.Button(fr_buttons, text='Save Settings',command = self.save_settings_file).grid(row=3, column=0, sticky='ew', padx=5)        
        run_img         = ImageTk.PhotoImage(Image.open('../gui/run_icon.png').resize( (35, 20), Image.ANTIALIAS))
        self.btn_run    = ttk.Button(fr_buttons, image=run_img, command = self.run_analysis)
        self.btn_run.grid(row=4, column=0, sticky='ew', padx=5)
        self.btn_run.image = run_img
        
        # TABS
        self.tab_control = ttk.Notebook(fr_tab)
        self.tab_control.grid()
        
        # EXPERIMENT TAB
        self.tab_experiment = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_experiment,text='EXPERIMENT')
        
        lbl_phenotype = tk.Label(self.tab_experiment,text='Phenotype',anchor='e').grid(row=0)
        self.phenotypeSV = StringVar()        
        self.entr_phenotype = tk.Entry(self.tab_experiment, textvariable = self.phenotypeSV,validate='focusout',validatecommand = self.handle_phenotype_entry)
        self.entr_phenotype.grid(row=0,column=1)
        
        lbl_animal = tk.Label(self.tab_experiment,text='Animal',anchor='e').grid(row=1)
        self.animalSV = StringVar()
        self.entr_animal = tk.Entry(self.tab_experiment, textvariable = self.animalSV,validate='focusout',validatecommand = self.handle_animal_entry)
        self.entr_animal.grid(row=1,column=1) 
        
        lbl_day = tk.Label(self.tab_experiment,text='Day',anchor='e').grid(row=2)
        self.daySV = StringVar()
        self.entr_day = tk.Entry(self.tab_experiment, textvariable = self.daySV,validate='focusout',validatecommand = self.handle_day_entry)
        self.entr_day.grid(row=2,column=1) 
        
        lbl_fields = tk.Label(self.tab_experiment,text='Fields').grid(row=3)
        
        lbl_field1 = tk.Label(self.tab_experiment,text='Field 1 Label',anchor='e').grid(row=3)
        self.field1SV = StringVar()
        self.entr_field1 = tk.Entry(self.tab_experiment, textvariable = self.field1SV,validate='focusout',validatecommand = self.handle_field1_entry)
        self.entr_field1.grid(row=3,column=1)         
        
        lbl_group1 = tk.Label(self.tab_experiment,text='Field 1 Group',anchor='e').grid(row=3,column=2)
        self.group1SV = StringVar()
        self.entr_group1 = tk.Entry(self.tab_experiment, textvariable = self.group1SV,validate='focusout',validatecommand = self.handle_group1_entry)
        self.entr_group1.grid(row=3,column=3)            

        # I/O TAB
        self.tab_io = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_io,text='I/O')
        
        # VIEWS TAB
        self.tab_views = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_views,text='VIEWS')
        self.img_height = 200
        self.img_width = 300
        
        self.tab_views.rowconfigure(0, minsize=10, weight=1)        
        self.tab_views.rowconfigure(1, minsize=self.img_height, weight=1)
        self.tab_views.rowconfigure(2, minsize=10, weight=1)
        self.tab_views.rowconfigure(3, minsize=self.img_height, weight=1)        
        
        self.tab_views.columnconfigure(0, minsize=10, weight=1)        
        self.tab_views.columnconfigure(1, minsize=self.img_width, weight=1)
        self.tab_views.columnconfigure(2, minsize=10, weight=1)   
        self.tab_views.columnconfigure(3, minsize=10, weight=1)   

        self.btn_open        = ttk.Button(self.tab_views, text='Select Video File', command = self.handle_select_videofile)    
        self.btn_open.grid(row=0, column=0, sticky='ew', padx=5)
        self.sc_vidframe = tk.Scale(self.tab_views, from_= 0.000, to= 1.000, resolution=0.0001,command = self.handle_video_frame,orient=HORIZONTAL,length=self.img_width)
        self.sc_vidframe.grid(row=0,column=1, sticky='ew', padx=5)
        self.panel_vid       = tk.Canvas(self.tab_views, bg='black',width=self.img_width,height=self.img_height)       
        self.panel_vid.grid(row=1, column=1, sticky="n")     
        self.settings['topview_thresh_blocksize'] = 641
        self.settings['topview_thresh_level'] = 1

        # lbl_fps = tk.Label(self.tab_views,text='FPS',anchor='e').grid(row=0,column=2)
        # self.fpsSV = StringVar()
        # self.entr_fps = tk.Entry(self.tab_views, textvariable = self.fpsSV,validate='focusout',validatecommand = self.handle_fps_entry)
        # self.entr_fps.grid(row=0,column=3) 
        
        self.arena_corners = []
        self.btn_set_topview_roi = ttk.Button(self.tab_views, text='Set ROI', command = self.handle_select_topview_roi)
        self.btn_set_topview_roi.grid(row=2, column=0, sticky='n', padx=5)  

        self.btn_set_gen_bgmod = ttk.Button(self.tab_views, text='Generate Background Model', command = self.handle_gen_bg_model)
        self.btn_set_gen_bgmod.grid(row=3, column=0, sticky='n', padx=5)
        
        self.btn_set_arena_corners = ttk.Button(self.tab_views, text='Identify Arena Corners', command = self.handle_arena_corners)
        self.btn_set_arena_corners.grid(row=4, column=0, sticky='n', padx=5)
        
        self.panel_topview       = tk.Canvas(self.tab_views, bg='black',width=self.img_width,height=self.img_height)       
        self.panel_topview.grid(row=3, column=1, sticky="n")        
        
        self.sc_topview_thresh = tk.Scale(self.tab_views, from_= 64, to= 4, command = self.handle_thresh_topview)
        #self.sc_topview_thresh.grid(row=3,column=2, sticky='ns')
        
        self.sc_topview_blocksize = tk.Scale(self.tab_views, from_= 961, to= 321, resolution=40, command = self.handle_blocksize_topview)
        self.sc_topview_blocksize.grid(row=3,column=2, sticky='ns')        
        
        # INTERVALS TAB
        self.tab_intervals = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_intervals,text='INTERVALS')
        
        lbl_intervaltype = tk.Label(self.tab_intervals,text='Interval Type').grid(row=0)
        self.intervalType = StringVar()
        self.intervalType.set('other')
        IT_select1 = tk.Radiobutton(self.tab_intervals, text = 'Other', anchor='w',variable=self.intervalType, value='other',command=self.handle_intervaltype_selection)        
        IT_select1.grid(row=0,column=1)        
        IT_select3 = tk.Radiobutton(self.tab_intervals, text = 'Trials - User Defined', anchor='w', variable=self.intervalType, value='trials-userdefined',command=self.handle_intervaltype_selection)
        IT_select3.grid(row=1,column=1)        
        IT_select2 = tk.Radiobutton(self.tab_intervals, text = 'Trials - Automatic', anchor='w', variable=self.intervalType, value='trials-automatic',command=self.handle_intervaltype_selection)
        IT_select2.grid(row=2,column=1)        
        
        self.approxtrialtimesSV = StringVar()
        self.lbl_trialtimes = tk.Label(self.tab_intervals,text = 'Approx. Trial Times: ')
        self.entr_trialtimes = tk.Entry(self.tab_intervals, textvariable = self.approxtrialtimesSV,validate='focusout',validatecommand = self.handle_trialtimes_entry)

        self.shadowontimesSV = StringVar()
        self.lbl_shadowontimes = tk.Label(self.tab_intervals,text = 'Shadow On Times: ')
        self.entr_shadowontimes = tk.Entry(self.tab_intervals, textvariable = self.shadowontimesSV,validate='key',validatecommand = self.handle_shadowontimes_entry)

        self.shadowofftimesSV = StringVar()
        self.lbl_shadowofftimes = tk.Label(self.tab_intervals,text = 'Shadow Off Times: ')
        self.entr_shadowofftimes = tk.Entry(self.tab_intervals, textvariable = self.shadowofftimesSV,validate='key',validatecommand = self.handle_shadowofftimes_entry)
        
        lbl_startAn = tk.Label(self.tab_intervals,text='Start analysis (s)').grid(row=6,column=0)
        self.startAnSV = StringVar()        
        self.entr_startan = tk.Entry(self.tab_intervals, textvariable = self.startAnSV,validate='focusout',validatecommand = self.handle_startAn_entry)
        self.entr_startan.grid(row=6,column=1)
        
        lbl_stopAn = tk.Label(self.tab_intervals,text='Stop analysis (s)').grid(row=6,column=2)
        self.stopAnSV = StringVar()        
        self.entr_stopan = tk.Entry(self.tab_intervals, textvariable = self.stopAnSV,validate='focusout',validatecommand = self.handle_stopAn_entry)
        self.entr_stopan.grid(row=6,column=3)        
        
        self.btn_set_roi     = ttk.Button(self.tab_intervals, text='Set ROI', command = self.handle_select_stim_roi)
        self.sc_thresh  = tk.Scale(self.tab_intervals, from_= 255, to= 0, command = self.handle_thresh_stim)
        self.panel_stim_vid = tk.Canvas(self.tab_intervals, bg='black',width=self.img_width,height=self.img_height)
        self.sc_stim_vidframe  = tk.Scale(self.tab_intervals, from_= 0.000, to= 1.000, resolution=0.001,command = self.handle_stim_video_frame,orient=HORIZONTAL,length=self.img_width)
        self.panel_stim = tk.Canvas(self.tab_intervals, bg='black',width=self.img_width,height=self.img_height)
        
        # BEHAVIORS
        self.shelter_img_width = 225
        self.shelter_img_height = 150
        
        self.tab_behaviors = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_behaviors,text='BEHAVIORS')        

        self.tab_behaviors.rowconfigure(0, minsize=10)
        self.tab_behaviors.rowconfigure(1, minsize=self.shelter_img_height,weight=1)
        self.tab_behaviors.rowconfigure(2, minsize=10,weight=1)
        
        self.tab_behaviors.columnconfigure(0, minsize=10,weight=1)   
        self.tab_behaviors.columnconfigure(1, minsize=10,weight=1)
        self.tab_behaviors.columnconfigure(2, minsize=self.shelter_img_width,weight=1)

        self.btn_set_shelter_roi = ttk.Button(self.tab_behaviors, text='Identify Shelter', command = self.handle_select_shelter_roi)
        self.btn_set_shelter_roi.grid(row=1, column=1, sticky='ne', padx=5)
        self.panel_shelter       = tk.Canvas(self.tab_behaviors, bg='black',width=self.shelter_img_width,height=self.shelter_img_height)
        self.panel_shelter.grid(row=1, column=2,sticky='nw')

    # update a setting
    def update_setting(self,label,value,*args):
        self.settings[label] = value    
    
    # update display
    def display_phenotype(self,*args):
        self.phenotypeSV.set(self.settings['phenotype'])

    def display_animal(self,*args):
        self.animalSV.set(self.settings['animal'])

    def display_day(self,*args):
        self.daySV.set(self.settings['day'])
        
    def display_field1(self,*args):
        self.field1SV.set(self.settings['field1'])        
        
    def display_group1(self,*args):
        self.group1SV.set(self.settings['group1'])               

    def display_FPS(self,*args):
        self.fpsSV.set(self.settings['FPS'])          

    def display_trialtimes(self,*args):
        if self.settings['interval type'] == 'trials-userdefined':
            self.shadowontimesSV.set(self.settings['shadow on times'])
            self.shadowofftimesSV.set(self.settings['shadow off times'])
            if 'approx. trial times' in self.settings.keys():
                self.approxtrialtimesSV.set(self.settings['approx. trial times'])
        elif self.settings['interval type'] == 'trials-automatic':    
            self.approxtrialtimesSV.set(self.settings['approx. trial times'])  
            if 'shadow on times' in self.settings.keys():
                self.shadowontimesSV.set(self.settings['shadow on times'])
            if 'shadow off times' in self.settings.keys():
                self.shadowofftimesSV.set(self.settings['shadow off times'])

    def display_startAn(self,*args):
        self.startAnSV.set(self.settings['analysis start'])                

    def display_stopAn(self,*args):
        self.stopAnSV.set(self.settings['analysis stop'])                

    def display_selected_videofile(self,*args):    
        self.sc_vidframe.set(self.settings['topview_frame_0'])
        
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['topview_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame0 = vidcap.read()
        
        self.vid_res_width = vidcap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.vid_res_height = vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        vidcap.release()
        
        img = ImageTk.PhotoImage(Image.fromarray(frame0).resize((self.img_width, self.img_height), Image.ANTIALIAS))
        self.panel_vid.create_image(0,0,anchor = 'nw',image = img)
        self.panel_vid.image = img

        sh_img = ImageTk.PhotoImage(Image.fromarray(frame0).resize((self.shelter_img_width, self.shelter_img_height), Image.ANTIALIAS))
        self.panel_shelter.create_image(0,0,anchor = 'nw',image = sh_img)
        self.panel_shelter.image = sh_img

    def display_arena_corners(self,*args):    
        #self.sc_vidframe.set(self.settings['topview_frame_0'])

        for x,y in self.arena_corners:
            x = x * self.img_width / self.vid_res_width
            y = y * self.img_height / self.vid_res_height
            self.panel_vid.create_oval(x-1,y-1,x+1,y+2,fill='white',outline='white')
        
    def display_shelter_roi(self,*args):    
        #self.sc_vidframe.set(self.settings['topview_frame_0'])
        
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['topview_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame0 = vidcap.read()
        vidcap.release()
        
        sh_img = ImageTk.PhotoImage(Image.fromarray(frame0).resize((self.shelter_img_width, self.shelter_img_height), Image.ANTIALIAS))
        self.panel_shelter.create_image(0,0,anchor = 'nw',image = sh_img)
        self.panel_shelter.image = sh_img
        
        xmin = self.settings['shelter_xmin']
        ymin = self.settings['shelter_ymin']
        xmax = self.settings['shelter_xmin'] + self.settings['shelter_width']
        ymax = self.settings['shelter_ymin'] + self.settings['shelter_height']
        
        xmin = xmin * self.shelter_img_width / self.vid_res_width
        xmax = xmax * self.shelter_img_width / self.vid_res_width
        ymin = ymin * self.shelter_img_height / self.vid_res_height
        ymax = ymax * self.shelter_img_height / self.vid_res_height
        
        self.panel_shelter.create_rectangle(xmin,ymin,xmax,ymax,outline='#482677',fill=None)

    def display_stim_videofile(self,*args):    
        self.sc_stim_vidframe.set(self.settings['stim_frame_0'])
        
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['stim_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame0 = vidcap.read()
        vidcap.release()
        
        img = ImageTk.PhotoImage(Image.fromarray(frame0).resize((self.img_width, self.img_height), Image.ANTIALIAS))
        self.panel_stim_vid.create_image(0,0,anchor = 'nw',image = img)
        self.panel_stim_vid.image = img

    def display_topview_roi(self,*args):  
        xat = self.settings['topview_xmin']
        yat = self.settings['topview_ymin']
        wat = self.settings['topview_width']
        hat = self.settings['topview_height']
        
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['topview_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame0 = vidcap.read()
        vidcap.release()

        topviewROI = frame0[yat:yat+hat,xat:xat+wat]        
        img = ImageTk.PhotoImage(Image.fromarray(topviewROI).resize((self.img_width, self.img_height), Image.ANTIALIAS))
        self.panel_topview.create_image(0,0,anchor = 'nw',image = img)
        self.panel_topview.image = img

    def display_topview_thresh(self,*args):
        xat = self.settings['topview_xmin']
        yat = self.settings['topview_ymin']
        wat = self.settings['topview_width']
        hat = self.settings['topview_height']
    
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['topview_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame0 = vidcap.read()
        vidcap.release()
        
        topviewROI = frame0[yat:yat+hat,xat:xat+wat] 
        self.sc_topview_thresh.set(self.settings['topview_thresh_level'])
        self.sc_topview_blocksize.set(self.settings['topview_thresh_blocksize'])
        
        #gray = cv2.cvtColor(cv2.cvtColor(topviewROI, cv2.COLOR_BGR2RGB), cv2.COLOR_BGR2GRAY)
        #blur = cv2.blur(gray,(10,10))
        #ret,thresh_img = cv2.threshold(blur,self.settings['topview_thresh_level'],255,cv2.THRESH_BINARY) 

        if not hasattr(self,'bg_model'):
            self.handle_gen_bg_model()
            
        roi = {
            'xmin'   : self.settings['topview_xmin'],
            'ymin'   : self.settings['topview_ymin'],
            'width'  : self.settings['topview_width'],
            'height' : self.settings['topview_height'],
        }
        method_args = {
            'k'             : 7,
            'inv_offset'    : 255,
            'at_level'      : self.settings['topview_thresh_level'],
            'at_blocksize'  : self.settings['topview_thresh_blocksize'],
            'bg_blur'       : cv2.blur(cv2.cvtColor(self.bg_model, cv2.COLOR_BGR2GRAY),(7,7)).astype(np.float32),
            'fr'            : topviewROI,
            'selem_e'       : disk(5),
            'selem_d'       : disk(5),
            'diff'          : numpy.zeros( (roi['height'],roi['width'],1) ).astype(np.float32),
            'at2'           : numpy.zeros( (roi['height'],roi['width'],1) ),
            'at'            : numpy.zeros( (roi['height'],roi['width'],1) ),
        }
        lbl,at,confidence = thresholdImage(method='BSAT',method_args=method_args)
        
        disp = ImageTk.PhotoImage(Image.fromarray(at).resize((self.img_width, self.img_height), Image.ANTIALIAS))
        self.panel_topview.create_image(0,0,anchor = 'nw',image = disp)
        self.panel_topview.image = disp

    def display_stim_roi(self,*args):  
        xsh = self.settings['stim_xmin']
        ysh = self.settings['stim_ymin']
        wsh = self.settings['stim_width']
        hsh = self.settings['stim_height']
        
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['stim_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame0 = vidcap.read()
        vidcap.release()

        stimROI = frame0[ysh:ysh+hsh,xsh:xsh+wsh]        
        img = ImageTk.PhotoImage(Image.fromarray(stimROI).resize((self.img_width, self.img_height), Image.ANTIALIAS))
        self.panel_stim.create_image(0,0,anchor = 'nw',image = img)
        self.panel_stim.image = img

    def display_stim_thresh(self,*args):
        xsh = self.settings['stim_xmin']
        ysh = self.settings['stim_ymin']
        wsh = self.settings['stim_width']
        hsh = self.settings['stim_height']
    
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['stim_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame0 = vidcap.read()
        vidcap.release()
        
        stimROI = frame0[ysh:ysh+hsh,xsh:xsh+wsh] 
        self.sc_thresh.set(self.settings['stim_thresh_level'])
        gray = cv2.cvtColor(cv2.cvtColor(stimROI, cv2.COLOR_BGR2RGB), cv2.COLOR_BGR2GRAY)
        blur = cv2.blur(gray,(10,10))
        ret,thresh_img = cv2.threshold(blur,self.settings['stim_thresh_level'],255,cv2.THRESH_BINARY)         
        disp = ImageTk.PhotoImage(Image.fromarray(thresh_img).resize((self.img_width, self.img_height), Image.ANTIALIAS))
        self.panel_stim.create_image(0,0,anchor = 'nw',image = disp)
        self.panel_stim.image = disp

    # INTERVALS
    
    # EVENT HANDLING
    def handle_phenotype_entry(self,*args):
        phenotype = self.phenotypeSV.get()
        self.update_setting(label = 'phenotype', value = phenotype)    

    def handle_animal_entry(self,*args):
        animal = self.animalSV.get()
        self.update_setting(label = 'animal', value = animal)    

    def handle_day_entry(self,*args):
        day = self.daySV.get()
        self.update_setting(label = 'day', value = day)    
        
    def handle_field1_entry(self,*args):
        field1 = self.field1SV.get()
        self.update_setting(label = 'field1', value = field1)         
        
    def handle_group1_entry(self,*args):
        group1 = self.group1SV.get()
        self.update_setting(label = 'group1', value = group1)         

    def handle_fps_entry(self,*args):
        fps = self.fpsSV.get()
        self.update_setting(label = 'FPS', value = int(float(fps)))
        print('handling fps entry')

    def display_intervaltype_selection(self,*args):
        if self.settings['interval type'] == 'trials-automatic':       
            self.lbl_shadowontimes.grid_remove()
            self.entr_shadowontimes.grid_remove()
            self.lbl_shadowofftimes.grid_remove()
            self.entr_shadowofftimes.grid_remove()
            
            self.lbl_trialtimes.grid(row=3)
            self.entr_trialtimes.grid(row=3,column = 1)
            
            self.sc_stim_vidframe.grid(row=7, column=1, sticky='ns')  
            self.panel_stim_vid.grid(row=8, column=1, sticky="nsew")
            
            self.btn_set_roi.grid(row=9, column=0, sticky='ew', padx=5)
            self.panel_stim.grid(row=10, column=1, sticky="nsew")     
            self.sc_thresh.grid(row=10, column=2, sticky='ns')                    
            
        elif self.settings['interval type'] == 'other':       
            self.lbl_trialtimes.grid_remove()
            self.entr_trialtimes.grid_remove()
            self.lbl_shadowontimes.grid_remove()
            self.entr_shadowontimes.grid_remove()            
            self.lbl_shadowofftimes.grid_remove()
            self.entr_shadowofftimes.grid_remove()     
            
            self.btn_set_roi.grid_remove()
            self.sc_thresh.grid_remove()
            self.panel_stim_vid.grid_remove()
            self.sc_stim_vidframe.grid_remove()
            self.panel_stim.grid_remove()

        elif self.settings['interval type'] == 'trials-userdefined':
            self.lbl_trialtimes.grid_remove()
            self.entr_trialtimes.grid_remove()
            self.btn_set_roi.grid_remove()
            self.sc_thresh.grid_remove()
            self.panel_stim_vid.grid_remove()
            self.sc_stim_vidframe.grid_remove()
            self.panel_stim.grid_remove()
            
            self.lbl_shadowontimes.grid(row=3)
            self.entr_shadowontimes.grid(row=3,column = 1)
            self.lbl_shadowofftimes.grid(row=4)
            self.entr_shadowofftimes.grid(row=4,column = 1)            
        self.intervalType.set(self.settings['interval type'])      
            

    def handle_intervaltype_selection(self,*args):
        self.update_setting(label = 'interval type', value = self.intervalType.get())                  # trials selected            
        self.display_intervaltype_selection()
        if self.intervalType.get() == 'other':
            self.update_setting(label = 'analysis start', value = float(self.startAnSV.get()))    
            self.update_setting(label = 'analysis stop', value = float(self.stopAnSV.get()))   
        if self.intervalType.get() == 'trials-userdefined':            
            self.update_setting(label = 'shadow on times', value = self.shadowontimesSV.get())      
            self.update_setting(label = 'shadow off times', value = self.shadowofftimesSV.get())               
        
        
    def handle_shadowontimes_entry(self,*args):    
        self.update_setting(label = 'shadow on times', value = self.shadowontimesSV.get())
        self.update_setting(label = 'interval type', value = self.intervalType.get())
        
    def handle_shadowofftimes_entry(self,*args):        
        self.update_setting(label = 'shadow off times', value = self.shadowofftimesSV.get())   
        self.update_setting(label = 'interval type', value = self.intervalType.get())
        
    def handle_trialtimes_entry(self,*args):
        self.update_setting(label = 'approx. trial times', value = self.approxtrialtimesSV.get())  
        self.update_setting(label = 'interval type', value = self.intervalType.get())

    def handle_startAn_entry(self,*args):
        startAn = float(self.startAnSV.get())
        self.update_setting(label = 'analysis start', value = startAn)    

    def handle_stopAn_entry(self,*args):
        stopAn = float(self.stopAnSV.get())
        self.update_setting(label = 'analysis stop', value = stopAn)

    def handle_select_videofile(self,*args):
        """Open a file for editing."""
        
        videopath = askopenfilename(
            filetypes=[('Video Files', '*.avi; *.MP4'), ('All Files', '*.*')]
        )
        if not videopath:
            return
            
        self.update_setting(label = 'videopath',value=videopath)  
        self.update_setting(label = 'topview_frame_0',value=0)
        self.update_setting(label = 'stim_frame_0',value=0)
        self.display_selected_videofile()    
    
    def handle_video_frame(self,*args):
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidframe = float(self.sc_vidframe.get())
        
        self.update_setting(label = 'topview_frame_0',value=vidframe)
        self.display_selected_videofile()
        self.display_topview_thresh()

    def selectPoint(self,event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(x,",",y)
            
            self.arena_corners.append([x,y])
            font = cv2.FONT_HERSHEY_SIMPLEX
            strXY = str(x)+", "+str(y)
        
    def handle_arena_corners(self,*args):
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['topview_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame = vidcap.read()
        vidcap.release()
        for corner in ['back left','back right','front right','front left']:
            cv2.imshow("frame",frame)
            print('identify {} corner'.format(corner))
            cv2.setMouseCallback("frame",self.selectPoint)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        self.update_setting(label = 'arena_corners',value=self.arena_corners)
        self.display_arena_corners()    

    def handle_gen_bg_model(self,*args):
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        roi = {
            'xmin'   : self.settings['topview_xmin'],
            'ymin'   : self.settings['topview_ymin'],
            'width'  : self.settings['topview_width'],
            'height' : self.settings['topview_height'],
        }
        self.bg_model = generateBackgroundModel(vidcap,roi,210,vidcap.get(cv2.CAP_PROP_FPS))

    def handle_stim_video_frame(self,*args):
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidframe = float(self.sc_stim_vidframe.get())
        
        self.update_setting(label = 'stim_frame_0',value=vidframe)
        self.display_stim_videofile()
    
    def handle_select_topview_roi(self,*args):
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['topview_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame0 = vidcap.read()
        vidcap.release()
    
        box_s = cv2.selectROIs("Select top view ROI", frame0, fromCenter=False)
        ((xat,yat,wat,hat),) = tuple(map(tuple, box_s))
        cv2.destroyAllWindows()
        
        roi = {
            'topview_xmin'     : xat,
            'topview_ymin'     : yat,
            'topview_width'    : wat,
            'topview_height'   : hat,
        }    
        
        for label,value in roi.items():
            self.update_setting(label=label,value=value)
            
        self.display_topview_roi()        
    
    def handle_select_stim_roi(self,*args):
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['stim_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame0 = vidcap.read()
        vidcap.release()
    
        box_s = cv2.selectROIs("Select stim ROI", frame0, fromCenter=False)
        ((xsh,ysh,wsh,hsh),) = tuple(map(tuple, box_s))
        cv2.destroyAllWindows()
        
        roi = {
            'stim_xmin'     : xsh,
            'stim_ymin'     : ysh,
            'stim_width'    : wsh,
            'stim_height'   : hsh,
        }    
        
        for label,value in roi.items():
            self.update_setting(label=label,value=value)
            
        self.display_stim_roi()    
    
    def handle_thresh_stim(self,*args):
        self.update_setting(label = 'stim_thresh_level',value=self.sc_thresh.get())
        self.display_stim_thresh()

    def handle_thresh_topview(self,*args):
        self.update_setting(label = 'topview_thresh_level',value=self.sc_topview_thresh.get())
        self.display_topview_thresh()

    def handle_blocksize_topview(self,*args):
        blocksize=self.sc_topview_blocksize.get()
        if (blocksize % 2 == 0) & (blocksize > 1):
            blocksize = blocksize + 1
        self.update_setting(label = 'topview_thresh_blocksize',value=blocksize)
        self.display_topview_thresh()        

    def handle_select_shelter_roi(self,*args):
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['topview_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame0 = vidcap.read()
        vidcap.release()
    
        box_s = cv2.selectROIs("Select shelter ROI", frame0, fromCenter=False)
        ((xsh,ysh,wsh,hsh),) = tuple(map(tuple, box_s))
        cv2.destroyAllWindows()
        
        roi = {
            'shelter_xmin'     : xsh,
            'shelter_ymin'     : ysh,
            'shelter_width'    : wsh,
            'shelter_height'   : hsh,
        }    
        
        for label,value in roi.items():
            self.update_setting(label=label,value=value)
            
        self.display_shelter_roi() 
        
    def save_settings_file(self,*args):
        filepath = asksaveasfilename(
            defaultextension='txt',
            filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')],
        )
        if not filepath:
            return
            
        outdf = pd.DataFrame(columns = ['label','value','dtype'])
        # appending item by item preserves element datatype
        for key,value in self.settings.items():
            print(key,value,type(value))
            outdf = outdf.append( {'label' : key, 'value' : value, 'dtype' : type(value)}, ignore_index = True)
        print('SETTINGS SAVED:')
        print(outdf.head(100))

        outdf.to_csv(filepath,index=None)
        self.root.title(f'Analysis Settings - {filepath}')

    # todo: configure a default filesaving location
    # todo: learn wtf pickling is because this is a hack
    def load_settings_file(self,*args):
        filepath = askopenfilename(
            defaultextension='txt',
            filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')],
        )
        if not filepath:
            return
        
        settingsdf = pd.read_csv(filepath,index_col = 0)
        
        # lol
        settingsdf['value'] = [ eval(re.search("<class '(.*)'>", typestr).group(1))(value) if typestr != "<class 'list'>" else eval(value) for value,typestr in zip(settingsdf['value'],settingsdf['dtype']) ]
        
        settingsdf.drop('dtype',axis=1,inplace=True)
        print('SETTINGS LOADED:')
        print(settingsdf.head(100))
        
        self.settings = settingsdf.to_dict()['value']
        for setting in self.settings.keys():
            eval(self.display_funcs[setting])
        
        self.root.title(f'Analysis Settings - {filepath}')
        
    def load_settings_fromfile(self,filepath,*args):
        # filepath = askopenfilename(
            # defaultextension='txt',
            # filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')],
        # )
        # if not filepath:
            # return
        
        settingsdf = pd.read_csv(filepath,index_col = 0)
        
        # lol
        settingsdf['value'] = [ eval(re.search("<class '(.*)'>", typestr).group(1))(value) if typestr != "<class 'list'>" else eval(value) for value,typestr in zip(settingsdf['value'],settingsdf['dtype']) ]
        
        settingsdf.drop('dtype',axis=1,inplace=True)
        print('SETTINGS LOADED:')
        print(settingsdf.head(100))
        
        self.settings = settingsdf.to_dict()['value']
        self.root.title(f'Analysis Settings - {filepath}')        

    def run_analysis(self,*args):
        self.root.quit()
        self.root.destroy()
        
        
        
        
        
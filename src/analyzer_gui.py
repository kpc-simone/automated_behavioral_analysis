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

class AnalysisConfigurer:
    # configuration
    def __init__(self,root):    
        self.settings = {}   
        self.display_funcs = {
            'phenotype'             :   'self.display_phenotype()',
            'animal'                :   'self.display_animal()',
            'day'                   :   'self.display_day()',
            'field1'                :   'self.display_field1()',
            'group1'                :   'self.display_group1()',
            'stim_thresh_level'     :   'self.display_stim_thresh()',
            'interval type'         :   'self.display_intervaltype_selection()',
            'approx. trial times'   :   'self.display_trialtimes()', 
            'shadow on times'       :   'self.display_trialtimes()', 
            'shadow off times'      :   'self.display_trialtimes()', 
            'analysis start'        :   'self.display_startAn()',            
            'analysis stop'         :   'self.display_stopAn()',
            'videopath'             :   'self.display_selected_videofile()',
            'stim_frame_0'          :   'self.display_selected_videofile()',
            'stim_xmin'             :   'self.display_stim_roi()',
            'stim_ymin'             :   'self.display_stim_roi()',
            'stim_width'            :   'self.display_stim_roi()',
            'stim_height'           :   'self.display_stim_roi()',
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

        self.btn_open        = ttk.Button(self.tab_views, text='Select Video File', command = self.handle_select_videofile)    
        self.btn_open.grid(row=0, column=0, sticky='ew', padx=5)
        self.sc_vidframe  = tk.Scale(self.tab_views, from_= 0.000, to= 1.000, resolution=0.001,command = self.handle_video_frame,orient=HORIZONTAL,length=self.img_width)
        self.sc_vidframe.grid(row=0,column=1, sticky='ew', padx=5)
        self.panel_vid       = tk.Canvas(self.tab_views, bg='black')       
        self.panel_vid.grid(row=1, column=1, sticky="nsew")        
        
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
        
        self.btn_set_roi     = ttk.Button(self.tab_intervals, text='Set ROI', command = self.handle_select_roi)
        self.sc_thresh  = tk.Scale(self.tab_intervals, from_= 255, to= 0, command = self.handle_thresh_stim)
        self.panel_stim_vid = tk.Canvas(self.tab_intervals, bg='black')
        self.sc_stim_vidframe  = tk.Scale(self.tab_intervals, from_= 0.000, to= 1.000, resolution=0.001,command = self.handle_video_frame,orient=HORIZONTAL,length=self.img_width)
        self.panel_stim = tk.Canvas(self.tab_intervals, bg='black')
        
        # BEHAVIORS
        self.tab_behaviors = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_behaviors,text='BEHAVIORS')        

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
        self.sc_vidframe.set(self.settings['stim_frame_0'])
        
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['stim_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame0 = vidcap.read()
        vidcap.release()
        
        img = ImageTk.PhotoImage(Image.fromarray(frame0).resize((self.img_width, self.img_height), Image.ANTIALIAS))
        self.panel_vid.create_image(0,0,anchor = 'nw',image = img)
        self.panel_vid.image = img

    def display_stim_videofile(self,*args):    
        self.sc_stim_vidframe.set(self.settings['stim_frame_0'])
        
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(self.settings['stim_frame_0']*vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
        success,frame0 = vidcap.read()
        vidcap.release()
        
        img = ImageTk.PhotoImage(Image.fromarray(frame0).resize((self.img_width, self.img_height), Image.ANTIALIAS))
        self.panel_stim_vid.create_image(0,0,anchor = 'nw',image = img)
        self.panel_stim_vid.image = img
    
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
            filetypes=[('Video Files', '*.avi'), ('All Files', '*.*')]
        )
        if not videopath:
            return
            
        self.update_setting(label = 'videopath',value=videopath)  
        self.update_setting(label = 'stim_frame_0',value=0)
        self.display_selected_videofile()    
    
    def handle_video_frame(self,*args):
        vidcap = cv2.VideoCapture(self.settings['videopath'])
        vidframe = float(self.sc_stim_vidframe.get())
        
        self.update_setting(label = 'stim_frame_0',value=vidframe)
        self.display_selected_videofile()
    
    def handle_select_roi(self,*args):
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
    def load_settings_file(self,*args):
        filepath = askopenfilename(
            defaultextension='txt',
            filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')],
        )
        if not filepath:
            return
        
        settingsdf = pd.read_csv(filepath,index_col = 0)
        
        # lol
        settingsdf['value'] = [ eval(re.search("<class '(.*)'>", typestr).group(1))(value) for value,typestr in zip(settingsdf['value'],settingsdf['dtype']) ]
        
        settingsdf.drop('dtype',axis=1,inplace=True)
        print('SETTINGS LOADED:')
        print(settingsdf.head(100))
        
        self.settings = settingsdf.to_dict()['value']
        for setting in self.settings.keys():
            eval(self.display_funcs[setting])
        
        self.root.title(f'Analysis Settings - {filepath}')

    def run_analysis(self,*args):
        self.root.quit()
        self.root.destroy()
        
        
        
        
        
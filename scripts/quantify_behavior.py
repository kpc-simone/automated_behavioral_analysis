from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from skimage.morphology import disk, binary_erosion, binary_opening, binary_closing, closing
from tkinter.filedialog import askopenfilename
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd
import progressbar
import sys,os
import time
import math
import cv2
import csv

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from extract_features import initializeDF, initializeCSV, analyzeInterval
from image_video_processing import *
from analyzer_gui import *

if __name__ == '__main__':
    args = sys.argv
    print(args)
    if '--plot' in args:
        plot_all = True
        plot = True
    else:
        plot_all = False
        plot = False
        
GUI = tk.Tk()
config = AnalysisConfigurer(GUI)
GUI.mainloop()  

# grab settings from AnalysisConfigurer object for use in script
# to do: create a class that inherits configuration settings - then don't need to grab them like this
videopath = config.settings['videopath']
FPS = config.settings['FPS']
interval_type = config.settings['interval type']
thresh_dict = {}
if interval_type == 'trials-automatic':
    analysis_period = [config.settings['analysis start'], config.settings['analysis stop']]
    trial_times = [float(s) for s in config.settings['approx. trial times'].split(',')]
    modifier = 'full'
    sh_dict = {}
    sh_dict['xmin'] = config.settings['stim_xmin']
    sh_dict['ymin'] = config.settings['stim_ymin']
    sh_dict['width'] = config.settings['stim_width']
    sh_dict['height'] = config.settings['stim_height']
    thresh_dict['shadow'] = config.settings['stim_thresh_level']
    sh_thresh_args = {
        'level'     : thresh_dict['shadow'],
        'sh_dict'   : sh_dict,
    }
elif interval_type == 'trials-userdefined':
    analysis_period = [config.settings['analysis start'], config.settings['analysis stop']]
    shadow_on_times = [float(s) for s in config.settings['shadow on times'].split(',')]
    shadow_off_times = [float(s) for s in config.settings['shadow off times'].split(',')]
    modifier = 'trial'
elif interval_type == 'other':
    analysis_period = [config.settings['analysis start'], config.settings['analysis stop']]
    analysis_period = [float(s) for s in analysis_period]
    modifier = 'general'
roi = {
    'xmin'   : config.settings['topview_xmin'],
    'ymin'   : config.settings['topview_ymin'],
    'width'  : config.settings['topview_width'],
    'height' : config.settings['topview_height'],
}
nest_corners = {
    'xmin'   : config.settings['shelter_xmin']-config.settings['topview_xmin'],
    'ymin'   : config.settings['shelter_ymin']-config.settings['topview_ymin'],
    'width'  : config.settings['shelter_width'],
    'height' : config.settings['shelter_height'],
}

# initialize program flow variables
S = 0

vidcap = cv2.VideoCapture(videopath)
# DLR algorithm step -6: generate a background frame

seg_method = 'BSAT'

bg_frame = generateBackgroundModel(vidcap,roi,30,FPS)
if ( seg_method == 'BSAT') or ( seg_method == '3CAT') or ( seg_method == 'ALDR'):
    method_args = getMethodParams(seg_method,config,bg_frame=bg_frame)

in_analysis_interval = False
shadow_detected = False
ROIs_set = False

# initialize behaviors
freeze = False
rear = False
escape = False
hide = False

# configure image processing variables

#'shadow'    : 240,         #930-934
#'shadow'    : 175,         #909-914

arena_size = [300,500]

# skip to time of interest
if interval_type == 'trials-automatic':
    vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(trial_times[S]*FPS))
elif interval_type == 'trials-userdefined':
    vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(shadow_on_times[S]*FPS))
elif interval_type == 'other':
    vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(analysis_period[0]*FPS))

print('skipped to frame# {}'.format(int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))))

while vidcap.isOpened():
    success,frame = vidcap.read()
    
    if frame is None:
        break
    
    key = cv2.waitKey(1)
    
    if not ROIs_set:
        key = cv2.waitKey(1)

        arena_corners, xform = getTransformParams(config.settings['arena_corners'],arena_size,roi)
        ROIs_set = True
        
    else: 
        if interval_type == 'trials-automatic':
            roi_sh = frame[sh_dict['ymin']:sh_dict['ymin']+sh_dict['height'],sh_dict['xmin']:sh_dict['xmin']+sh_dict['width']]
            sh_thresh_args['roi'] = roi_sh
            lbl_sh,thresh_sh,level_sh,confidence = thresholdImage(method='simple',method_args = sh_thresh_args)
            in_analysis_interval = getShadowStatus(lbl_sh)
            
        elif interval_type == 'trials-userdefined':
            in_analysis_interval = True
            
        elif interval_type == 'other':
            in_analysis_interval = True
        
        if in_analysis_interval:
            metadata,csvfilename = initializeCSV(videopath,modifier,config.settings,S+1)
            # todo - just pass config to analyze interval
            if interval_type == 'trials-automatic':
                if seg_method == 'ALDR':
                    analyzeInterval(interval_type,thresh_dict,frame,vidcap,FPS,roi,nest_corners,S,csvfilename,xform,arena_corners,plot,sh_dict=sh_dict,bgz_roi=data_bg_z,ref_int=ref_int,mask0=mask0,mask1_b=mask1_b,selem=selem1,trp=analysis_period,adaptive_level=adaptive_level,blocksize=blocksize) 	# breaks off to loop through video from set cap
                
                if seg_method == 'BSAT':
                    analyzeInterval(interval_type,seg_method,thresh_dict,frame,vidcap,FPS,roi,nest_corners,S,csvfilename,xform,arena_corners,plot,sh_thresh_args=sh_thresh_args,trp=analysis_period,method_args=method_args) 	# breaks off to loop through video from set cap
                
                # with open(summary_filepath, 'a', newline='') as csvFile:
                    # filewriter = csv.writer(csvFile, delimiter = ',', quotechar = '|', quoting = csv.QUOTE_MINIMAL)
                    # filewriter.writerow(key_timings)
                # csvFile.close()

            elif interval_type == 'trials-userdefined':                
                shadow_on_rel = shadow_on_times[S] - shadow_on_times[S]
                shadow_off_rel = shadow_off_times[S] - shadow_on_times[S]
                shadow_period = [shadow_on_rel,shadow_off_rel]
                key_timings1 = analyzeInterval(interval_type,thresh_dict,frame,vidcap,FPS,roi,nest_corners,S,csvfilename,xform,arena_corners,plot,trp=analysis_period,shp=shadow_period) 	# breaks off to loop through video from set cap
                print(key_timings1,metadata)
                key_timings = metadata + key_timings1
                
                with open(summary_filepath, 'a', newline='') as csvFile:
                    filewriter = csv.writer(csvFile, delimiter = ',', quotechar = '|', quoting = csv.QUOTE_MINIMAL)
                    filewriter.writerow(key_timings)
                csvFile.close()
            
            elif interval_type == 'other':    
                #analyzeInterval(interval_type,thresh_dict,frame,vidcap,FPS,roi,nest_corners,S,csvfilename,xform,arena_corners,plot,bgz_roi=data_bg_z,ref_int=ref_int,mask0=mask0,mask1_b=mask1_b,selem=selem1,trp=analysis_period,adaptive_level=adaptive_level,blocksize=blocksize) 	# breaks off to loop through video from set cap
                #analyzeInterval(interval_type,thresh_dict,frame,vidcap,FPS,roi,nest_corners,S,csvfilename,xform,arena_corners,plot,trp=analysis_period) 	# breaks off to loop through video from set cap
                if seg_method == '3CAT':
                    analyzeInterval(interval_type,seg_method,thresh_dict,frame,vidcap,FPS,roi,nest_corners,S,csvfilename,xform,arena_corners,plot,trp=analysis_period,method_args=method_args) 	# breaks off to loop through video from set cap
            
            S += 1
            in_analysis_interval = False
            if plot_all:
                if input('skip plotting for remaining trials? ( accept [y]/n ): ') == 'y':
                    plot = False
                else:
                    plot = True
                    
            if interval_type == 'trials-automatic':
                if S < len(trial_times):
                    vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(trial_times[S])*FPS)
                else:
                    break
            if interval_type == 'trials-userdefined':
                if S < len(trial_times):
                    vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(shadow_on_times[S])*FPS)
                else:
                    break            
            else:
                break
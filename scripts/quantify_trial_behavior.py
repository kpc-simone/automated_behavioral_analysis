from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
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
from image_video_processing import selectROIs, getShadowStatus, thresholdImage, selectPoint, getTransformParams, getBackground
from extract_features import initializeDF, initializeCSV, analyzeInterval
import image_video_processing
from analyzer_gui import *

now = datetime.now()
dt_str = now.strftime('%d%m%Y')
summary_filepath = '../video_analyses/automated_trial_keytimings_{}.csv'.format(dt_str)

if not os.path.isfile(summary_filepath):
    row = ['animal','day','trial','shadowON','escape','hide','shadowOFF']
    with open(summary_filepath, 'w') as csvFile:
        filewriter = csv.writer(csvFile, delimiter = ',', quotechar = '|', quoting = csv.QUOTE_MINIMAL)
        filewriter.writerow(row)
    csvFile.close()

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
interval_type = config.settings['interval type']
thresh_dict = {}
if interval_type == 'trials-automatic':
    analysis_period = [config.settings['analysis start'], config.settings['analysis stop']]
    trial_times = [float(s) for s in config.settings['approx. trial times'].split(',')]
    modifier = 'trial'
    sh_dict = {}
    sh_dict['xmin'] = config.settings['stim_xmin']
    sh_dict['ymin'] = config.settings['stim_ymin']
    sh_dict['width'] = config.settings['stim_width']
    sh_dict['height'] = config.settings['stim_height']
    thresh_dict['shadow'] = config.settings['stim_thresh_level']
elif interval_type == 'trials-userdefined':
    analysis_period = [config.settings['analysis start'], config.settings['analysis stop']]
    shadow_on_times = [float(s) for s in config.settings['shadow on times'].split(',')]
    shadow_off_times = [float(s) for s in config.settings['shadow off times'].split(',')]
    modifier = 'trial'
elif interval_type == 'other':
    analysis_period = [config.settings['analysis start'], config.settings['analysis stop']]
    analysis_period = [float(s) for s in analysis_period]
    modifier = 'general'

# configure video properties
FPS = 20

# initialize program flow variables
S = 0
background_frame = 10             
in_analysis_interval = False
shadow_detected = False
ROIs_set = False

# initialize behaviors
freeze = False
rear = False
escape = False
hide = False

# configure image processing variables
thresh_dict['animal'] = 17
#'shadow'    : 240,         #930-934
#'shadow'    : 175,         #909-914

arena_size = [300,500]

# skip to time of interest
vidcap = cv2.VideoCapture(videopath)
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
        a_dict, nest_corners = selectROIs(frame)
        ROIs_set = True

        for corner in ['back left','back right','front right','front left']:
            cv2.imshow("frame",frame)
            print('identify {} corner'.format(corner))
            cv2.setMouseCallback("frame",selectPoint)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        points = image_video_processing.points  
        arena_corners, xform = getTransformParams(points,arena_size,a_dict)
        
    else: 
        if interval_type == 'trials-automatic':
            roi_sh = frame[sh_dict['ymin']:sh_dict['ymin']+sh_dict['height'],sh_dict['xmin']:sh_dict['xmin']+sh_dict['width']]
            lbl_sh,thresh_sh,level_sh = thresholdImage(roi_sh,thresh_dict['shadow'])
            in_anaysis_interval = getShadowStatus(lbl_sh)
            
        elif interval_type == 'trials-userdefined':
            in_analysis_interval = True
            
        elif interval_type == 'other':
            in_analysis_interval = True
        
        if in_analysis_interval:
            metadata,csvfilename = initializeCSV(videopath,modifier,S+1)
            if interval_type == 'trials-automatic':
                key_timings1 = analyzeInterval(interval_type,thresh_dict,frame,vidcap,FPS,a_dict,nest_corners,S,csvfilename,xform,arena_corners,plot,sh_dict,trp=analysis_period) 	# breaks off to loop through video from set cap
                print(key_timings1,metadata)
                key_timings = metadata + key_timings1
                with open(summary_filepath, 'a', newline='') as csvFile:
                    filewriter = csv.writer(csvFile, delimiter = ',', quotechar = '|', quoting = csv.QUOTE_MINIMAL)
                    filewriter.writerow(key_timings)
                csvFile.close()

            elif interval_type == 'trials-userdefined':                
                shadow_on_rel = shadow_on_times[S] - shadow_on_times[S]
                shadow_off_rel = shadow_off_times[S] - shadow_on_times[S]
                shadow_period = [shadow_on_rel,shadow_off_rel]
                key_timings1 = analyzeInterval(interval_type,thresh_dict,frame,vidcap,FPS,a_dict,nest_corners,S,csvfilename,xform,arena_corners,plot,trp=analysis_period,shp=shadow_period) 	# breaks off to loop through video from set cap
                print(key_timings1,metadata)
                key_timings = metadata + key_timings1
                
                with open(summary_filepath, 'a', newline='') as csvFile:
                    filewriter = csv.writer(csvFile, delimiter = ',', quotechar = '|', quoting = csv.QUOTE_MINIMAL)
                    filewriter.writerow(key_timings)
                csvFile.close()
            elif interval_type == 'other':    
                analyzeInterval(interval_type,thresh_dict,frame,vidcap,FPS,a_dict,nest_corners,S,csvfilename,xform,arena_corners,plot,trp=analysis_period) 	# breaks off to loop through video from set cap
            
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
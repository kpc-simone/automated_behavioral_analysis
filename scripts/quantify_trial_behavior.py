from tkinter.filedialog import askopenfilename
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
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
import image_video_processing
from extract_features import initializeDF, initializeCSV, analyzeTrial

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
        
# initialize program flow variables
S = 0
background_frame = 10             
in_a_trial = False
shadow_detected = False
ROIs_set = False

# initialize behaviors
freeze = False
rear = False
escape = False
hide = False

# configure image processing variables
thresh_dict = {
    'animal'    : 17,
    'shadow'    : 240,         #930-934
    #'shadow'    : 175,         #909-914
}

# 909-914 : 175
# 930-934 : 240
arena_size = [300,500]

# configure output file properties
trial_period = [-10,50]
modifier = 'trial'

# configure video properties
FPS = 20

#todo
# write configuration function 
# pull out settings from a returned dict object for use in the rest of the script

# select video file to analyze
videopath = askopenfilename()    

# select trial metadatafile
trial_md = askopenfilename()
f = open(trial_md)
trial_times = f.readline().split(' ')[1:]

# skip to time of interest
vidcap = cv2.VideoCapture(videopath)
vidcap.set(cv2.CAP_PROP_POS_FRAMES,background_frame)
success,bframe = vidcap.read()

background = getBackground(bframe)

vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(trial_times[S])*FPS)
print('skipped to frame# {}'.format(int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))))

while vidcap.isOpened():
    success,frame = vidcap.read()
    
    if frame is None:
        break
    
    key = cv2.waitKey(1)
    
    if not ROIs_set:
        key = cv2.waitKey(1)
        a_dict, sh_dict, nest_corners = selectROIs(frame)
        roi_sh = frame[sh_dict['ymin']:sh_dict['ymin']+sh_dict['height'],sh_dict['xmin']:sh_dict['xmin']+sh_dict['width']]
        ROIs_set = True

        for corner in ['back left','back right','front right','front left']:
            cv2.imshow("frame",frame)
            print('identify {} corner'.format(corner))
            cv2.setMouseCallback("frame",selectPoint)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        points = image_video_processing.points  
        arena_corners, xform = getTransformParams(points,arena_size,a_dict)
        
        # get background intensity and then return to main loop frame
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,background_frame)
        success,bframe = vidcap.read()
        background = getBackground(bframe[a_dict['ymin']:a_dict['ymin']+a_dict['height'],a_dict['xmin']:a_dict['xmin']+a_dict['width']])
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(trial_times[S])*FPS)
        
    else: 

        roi_sh = frame[sh_dict['ymin']:sh_dict['ymin']+sh_dict['height'],sh_dict['xmin']:sh_dict['xmin']+sh_dict['width']]
        lbl_sh,thresh_sh,level_sh = thresholdImage(roi_sh,thresh_dict['shadow'])
        in_a_trial = getShadowStatus(lbl_sh)
        
        if in_a_trial:
            metadata,csvfilename = initializeCSV(videopath,modifier,S+1)
            #todo: have analyzeTrial return keytimings from df for a trial, rather than pass summary file or return the df and process in the main loop

            key_timings1 = analyzeTrial(thresh_dict,frame,vidcap,FPS,trial_period,a_dict,sh_dict,nest_corners,S,csvfilename,xform,arena_corners,plot,background) 	# breaks off to loop through video from set cap
            print(key_timings1,metadata)
            
            key_timings = metadata + key_timings1
            print(type(key_timings),key_timings)
            
            with open(summary_filepath, 'a', newline='') as csvFile:
                filewriter = csv.writer(csvFile, delimiter = ',', quotechar = '|', quoting = csv.QUOTE_MINIMAL)
                filewriter.writerow(key_timings)
            csvFile.close()
            
            S += 1
            in_a_trial = False
            if plot_all:
                if input('skip plotting for remaining trials? ( accept [y]/n ): ') == 'y':
                    plot = False
                else:
                    plot = True
            if S < len(trial_times):
                vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(trial_times[S])*FPS)
            else:
                break
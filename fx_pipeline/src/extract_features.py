import matplotlib.pyplot as plt
from datetime import datetime
import progressbar
import pandas as pd
import numpy as np
import sys,os
import math
import cv2

from identify_behaviors import getHide, getFreeze, getRear, getEscape
from generate_animation import initializeFigAxes, updateFigure
from image_video_processing import thresholdImage, getPrimitives


def initializeDF (p_cols,d_cols,b_cols,trp,FPS):
    out_data = {}
    ts = np.linspace(trp[0],trp[1]+1,int(trp[1]-trp[0]+1)*FPS)
    n_frames = len(ts)
    out_data['time'] = ts
    out_data['confidence'] = 0.0
    out_data['shadow'] = False
    for feature in (p_cols + d_cols + b_cols):
        out_data[feature] = np.zeros((n_frames,))
        if feature in p_cols:
            out_data[feature][:] = np.NaN					# simplifies interpolation
        if feature in d_cols:
            out_data[feature][1:] = np.NaN					# simplifies interpolation    
        if feature in b_cols:
            out_data[feature][3:] = np.NaN					# simplifies interpolation        
    out_df = pd.DataFrame(out_data)
    p_cols.insert(0,'shadow')
    p_cols.insert(0,'confidence')
    p_cols.insert(0,'time')
    return out_df, p_cols
    
def initializeCSV(videopath,modifier,settings,rep):
    directory = os.path.split(videopath)[0].split('/')[-1]
    videofile = os.path.split(videopath)[1][:-4]         #exclude file extension
    
    s = directory.split('_')
    
    experiment = settings['experiment'] = 'tonic'
    animal = settings['animal']
    day = settings['day']
    lux = settings['group1']

    now = datetime.now()
    dtstr = now.strftime("%d%m%Y_%H%M%S")
    
    #todo - configure this filename in i/o
    csvfilename = '../../fx_analyses/{}-{}-{}-{}-{}-{}-{}.csv'.format(experiment,animal,day,lux,modifier,rep,dtstr)
    
    return [animal,day,rep],csvfilename    
    
#def analyzeInterval(interval_type,seg_method,thresh_dict,frame,vidcap,FPS,roi,nest_corners,S,csvfilename,xform,arena_corners,plot,rlim=5.0,vlim=150.0,bgz_roi=None,ref_int=None,mask0=None,mask1_b=None,selem=None,sh_dict=None,trp=None,shp=None,adaptive_level=None,blocksize=None):
def analyzeInterval(interval_type,seg_method,thresh_dict,frame,vidcap,FPS,roi,nest_corners,S,csvfilename,xform,arena_corners,plot,sh_thresh_args=None,trp=None,method_args=None):
    
    # determine analysis interval timing from settings and set video playback
    if interval_type == 'trials-automatic' or interval_type == 'trials-userdefined':
        f0_analysis = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,f0_analysis+trp[0]*FPS)
        #print(f0_analysis,trp[0]*FPS,f0_analysis+trp[0]*FPS)
        #print(f0_analysis/FPS,trp[0],f0_analysis/FPS+trp[0])
        t0_analysis = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))/FPS
    if interval_type == 'other':
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,trp[0]*FPS)
        t0_analysis = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))/FPS
        trp = [ t-t0_analysis for t in trp ]
    print('analyzing behavior for interval {} from {} to {}'.format(S+1,t0_analysis,t0_analysis+(trp[1]-trp[0])))
    
    # grab and segment first frame in interval
    success,frame = vidcap.read()
    roi_a = frame[roi['ymin']:roi['ymin']+roi['height'],roi['xmin']:roi['xmin']+roi['width']]
    if seg_method == 'BSAT':
        method_args['fr'] = roi_a.astype(np.float32)
        method_args['diff'] = np.zeros( (roi['height'],roi['width'],1) ).astype(np.float32)
        method_args['at2']  = np.zeros( (roi['height'],roi['width'],1) )
        method_args['at'] = np.zeros( (roi['height'],roi['width'],1) )
        lbl_a,at,confidence = thresholdImage(method='BSAT',method_args=method_args)
    elif seg_method == '3CAT':
        k = method_args['k']
        method_args['fr_blur'] = cv2.blur(roi_a,(k,k)).astype(np.float64)
        lbl_a,at,confidence = thresholdImage(method='3CAT',method_args=method_args)
        # Some version of 3CAT needed 3- 64-bit precision FP matrices
        #frame_a1 = np.zeros( (roi['height'],roi['width'],3) ).astype(np.float64)
        #frame_a2 = np.zeros( (roi['height'],roi['width'],3) ).astype(np.float64)
    elif seg_method == 'ALDR':
        lbl_a,thresh_a,level_a,confidence = thresholdImage(roi_a=roi_a,method='ADLR',bgz_roi=bgz_roi,level=adaptive_level,blocksize=blocksize,mask1_b=mask1_b,mask0=mask0,ref_int=ref_int)
        # ALDR would have needed some frame averaging
        # DLR Algorithm step -1: generate empty frame matrices
        frame_a1 = np.zeros( (roi['height'],roi['width'],3) )
        frame_a2 = np.zeros( (roi['height'],roi['width'],3) )

    if interval_type == 'trials-automatic':
        sh_dict = sh_thresh_args['sh_dict']
        sh_thresh_args['roi'] = frame[sh_dict['ymin']:sh_dict['ymin']+sh_dict['height'],sh_dict['xmin']:sh_dict['xmin']+sh_dict['width']]
        lbl_sh,thresh_sh,level_sh,confidence = thresholdImage(method='simple',method_args = sh_thresh_args)

    # extract parameters for transform
    x0 = xform['x0']
    ymin = xform['ymin']
    y0_max = xform['y0_max']
    mx1 = xform['mx1']
    mx2 = xform['mx2']
    my = xform['my']    

    # initialize output csv
    p_cols = ['xc','yc','minr','maxr','maj-ax','min-ax','orientation','x-pos','y-pos']
    d_cols = ['x-corr','y-corr','x-vel','y-vel','speed']
    b_cols = ['rear','freeze','escape','hide']
    df0,p_cols = initializeDF(p_cols,d_cols,b_cols,trp,FPS)
    print(df0.head())
    print(df0.tail())
    d_cols = p_cols + d_cols
    b_cols = d_cols + b_cols 

    # initialize plotting
    if plot:
        if interval_type == 'trials-automatic':
            fig,plot_dict,data_dict = initializeFigAxes(trp,FPS,at,arena_corners,thresh_sh = thresh_sh)
            # figt,axt = plt.subplots(1,1)
            # axt.imshow(thresh_sh)
            # plt.show(block=False)
            # plt.pause(1)
            # plt.close()            
        else:    
            fig,plot_dict,data_dict = initializeFigAxes(trp,FPS,at,arena_corners)
        
    # initialize stimulus/behavior conditions
    shadow_detected = False
    escape = False
    
    t_idx = 0
    N_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
    # set initial primitives
    with progressbar.ProgressBar( max_value = ( trp[1] - trp[0] ) ) as p_bar:
        while ( ( ( vidcap.get(cv2.CAP_PROP_POS_FRAMES)/FPS - t0_analysis) < ( trp[1] - trp[0] ) ) & (vidcap.get(cv2.CAP_PROP_POS_FRAMES)/N_frames < 1.0) ):
            #print(vidcap.get(cv2.CAP_PROP_POS_FRAMES)/N_frames)
            p_bar.update( vidcap.get(cv2.CAP_PROP_POS_FRAMES)/FPS - t0_analysis )
            
            #print('{} %'.format( (int(vidcap.get(cv2.CAP_PROP_POS_MSEC)-trp[0] * 1000 ) / ( (trp[1]-trp[0]) * 1000 ) ) * 100 ) )
            success,frame0 = vidcap.read()
            if frame0 is None:
                break
            
            key = cv2.waitKey(1)
            
            # Roll the next few lines together as a function -- updateFrames
            # if no averaging, pass. ie -- frames = updateFrames(frame0,averaging=None) or frames = updateFrames(frame0,averaging=2,3)
            
            if seg_method == 'BSAT':
                roi_a = frame0[roi['ymin']:roi['ymin']+roi['height'],roi['xmin']:roi['xmin']+roi['width']]     
                method_args['fr'] = roi_a
                lbl_a,at,confidence = thresholdImage(method='BSAT',method_args=method_args)
                
            elif seg_method == '3CAT':
                roi_a = frame0[roi['ymin']:roi['ymin']+roi['height'],roi['xmin']:roi['xmin']+roi['width']]     
                fr = np.float64( roi_a*0.6 + frame_a1*0.3 + frame_a2*0.1 )           
                method_args['fr_blur'] = cv2.blur(fr,(k,k)).astype(np.float64)
                lbl_a,at,confidence = thresholdImage(method='3CAT',method_args=method_args)
                frame_a1 = roi_a
                frame_a2 = frame_a1 
            
            elif seg_method == 'ALDR':
                # DLR algorithm step 0: get current frame and ROI
                frame_a0 = frame0[roi['ymin']:roi['ymin']+roi['height'],roi['xmin']:roi['xmin']+roi['width']]     
                frame_a = np.uint8( frame_a0*0.9 + frame_a1*0.1 + frame_a2*0.0 )           
                lbl_a,thresh_a,level_a,confidence = thresholdImage(frame_a,method='ADLR',bgz_roi=bgz_roi,level=adaptive_level,blocksize=blocksize,mask0=mask0,mask1_b=mask1_b,ref_int=ref_int,selem=selem)
                frame_a1 = frame_a0
                frame_a2 = frame_a1 


            # add extra args passed to getPrimites to config settings
            
            if interval_type == 'other':
                df0.iloc[t_idx, [df0.columns.get_loc(col) for col in p_cols]] = getPrimitives(lbl_a,df0.iloc[t_idx, [df0.columns.get_loc(col) for col in p_cols]],confidence,ymin = ymin,ymax=y0_max+ymin-25,interval_type=interval_type)
            
            elif interval_type == 'trials-userdefined':
                relative_time = df0.at[t_idx,'time']
                df0.iloc[t_idx, [df0.columns.get_loc(col) for col in p_cols]] = getPrimitives(lbl_a,df0.iloc[t_idx, [df0.columns.get_loc(col) for col in p_cols]],confidence,ymin = ymin,ymax=y0_max+ymin-25,interval_type=interval_type,shadow_period_exact=shp,relative_time = relative_time)
            
            elif interval_type == 'trials-automatic':
                roi_sh = frame0[sh_dict['ymin']:sh_dict['ymin']+sh_dict['height'],sh_dict['xmin']:sh_dict['xmin']+sh_dict['width']]
                sh_thresh_args['roi'] = roi_sh
                lbl_sh,thresh_sh,level_sh,confidence1 = thresholdImage(method='simple',method_args = sh_thresh_args)
                df0.iloc[t_idx, [df0.columns.get_loc(col) for col in p_cols]] = getPrimitives(lbl_a,df0.iloc[t_idx, [df0.columns.get_loc(col) for col in p_cols]],confidence,ymin = ymin,ymax=y0_max+ymin-25,interval_type=interval_type,lbl_sh=lbl_sh)
                
            if t_idx > 0:
                
                if ((df0.at[t_idx,'maj-ax'] / df0.at[t_idx,'min-ax']) > 2.0) and (abs(df0.at[t_idx,'orientation']) < 0.6):
                    df0.at[t_idx,'y-pos'] = df0.at[t_idx,'yc'] + math.cos(df0.at[t_idx,'orientation'])*0.5*df0.at[t_idx,'maj-ax']
                    df0.at[t_idx,'x-pos'] = df0.at[t_idx,'xc'] + math.sin(df0.at[t_idx,'orientation'])*0.5*df0.at[t_idx,'maj-ax']
                else:    
                    df0.at[t_idx,'y-pos'] = df0.at[t_idx,'yc'] + (df0.at[t_idx,'maxr']-df0.at[t_idx,'minr'])*1/2
                    df0.at[t_idx,'x-pos'] = df0.at[t_idx,'xc']

                df0.at[t_idx,'x-corr'] = (df0['x-pos'].iloc[t_idx] - x0) * (mx2 + (mx1-mx2)*(y0_max-((df0['y-pos'].iloc[t_idx] - ymin)))/y0_max)
                df0.at[t_idx,'y-corr'] = (df0['y-pos'].iloc[t_idx] - ymin) * my
                df0.at[t_idx,'x-vel'] = df0['x-corr'].iloc[t_idx] - df0['x-corr'].iloc[t_idx-1]
                df0.at[t_idx,'y-vel'] = df0['y-corr'].iloc[t_idx] - df0['y-corr'].iloc[t_idx-1]
                df0.at[t_idx,'speed'] = math.sqrt( df0['x-vel'].iloc[t_idx]**2 + df0['y-vel'].iloc[t_idx]**2 )
                
            # todo configure behavioral thresholds and pass as a dict from main script loop
            if t_idx > 2:    
                df0.at[t_idx,'hide'],hide = getHide(df0.at[t_idx,'x-pos'],df0.at[t_idx,'y-pos'],nest_corners)
                df0.at[t_idx,'rear'],rear = getRear(df0.at[t_idx,'maj-ax'],df0.at[t_idx,'min-ax'],2.0,df0.at[t_idx,'orientation'],0.6)
                df0.at[t_idx,'freeze'] = getFreeze(df0.at[t_idx,'speed'],df0.at[t_idx-1,'speed'],df0.at[t_idx-2,'speed'],df0.at[t_idx-3,'speed'],2.5, rear)
                df0.at[t_idx,'escape'],escape = getEscape(df0.at[t_idx,'shadow'],abs(df0.at[t_idx,'speed']),40,1.0,escape,hide,rear)
            
            if plot:
                yc = df0.at[t_idx,'yc']
                xc = df0.at[t_idx,'xc']
                major_axis_length = df0.at[t_idx,'maj-ax']
                minor_axis_length = df0.at[t_idx,'min-ax']
                orientation = df0.at[t_idx,'orientation']
                x1 = xc + math.cos(orientation) * 0.5 * minor_axis_length
                y1 = yc - math.sin(orientation) * 0.5 * minor_axis_length
                x2 = xc - math.sin(orientation) * 0.5 * major_axis_length
                y2 = yc - math.cos(orientation) * 0.5 * major_axis_length
                
                data_dict['tdata'].append(df0.at[t_idx,'time'])
                data_dict['xdata'] = df0.at[t_idx,'x-pos']
                data_dict['ydata'] = df0.at[t_idx,'y-pos']
                data_dict['xdata1'] = (xc,x1)
                data_dict['ydata1'] = (yc,y1)
                data_dict['xdata2'] = (xc,x2)
                data_dict['ydata2'] = (yc,y2)
                data_dict['hdata'].append(df0.at[t_idx,'hide'])
                data_dict['fdata'].append(df0.at[t_idx,'freeze'])
                data_dict['rdata'].append(df0.at[t_idx,'rear'])
                data_dict['edata'].append(df0.at[t_idx,'escape'])
                data_dict['sdata'].append(df0.at[t_idx,'speed'])
                data_dict['vxdata'].append(df0.at[t_idx,'x-vel'])
                data_dict['vydata'].append(df0.at[t_idx,'y-vel'])
                
                data_dict['pxdata'].append(df0.at[t_idx,'x-corr'])
                data_dict['pydata'].append(df0.at[t_idx,'y-corr'])
                
                if interval_type == 'trials-automatic':
                    updateFigure(plot_dict,data_dict,at,thresh_sh=thresh_sh)
                else:    
                    updateFigure(plot_dict,data_dict,at)
            
            t_idx += 1

            #df0.interpolate(inplace=True)              # interpolate missing data

        df0.to_csv(csvfilename)
    
    if plot:
        plt.close(fig)
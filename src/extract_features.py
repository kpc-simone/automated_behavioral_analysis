import matplotlib.pyplot as plt
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
    ts = np.linspace(trp[0],trp[1],int(trp[1]-trp[0])*FPS)
    n_frames = len(ts)
    out_data['time'] = ts
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
    p_cols.insert(0,'time')
    return out_df, p_cols
    
def initializeCSV(videopath,modifier,rep):
    directory = os.path.split(videopath)[0].split('/')[-1]
    videofile = os.path.split(videopath)[1][:-4]         #exclude file extension
    
    s = directory.split('_')
    experiment = s[0]
    day = s[1]
    animal = videofile[:4]
    csvfilename = '../video_analyses/{}-{}-{}-{}-{}.csv'.format(experiment,animal,day,modifier,rep)
    
    return [animal,day,rep],csvfilename    
    
def analyzeInterval(interval_type,thresh_dict,frame,vidcap,FPS,a_dict,nest_corners,S,csvfilename,xform,arena_corners,plot,rlim=5.0,vlim=150.0,sh_dict=None,trp=None,shp=None):
    tS_start = int(vidcap.get(cv2.CAP_PROP_POS_MSEC))/1000
    if interval_type == 'trials-automatic' or interval_type == 'trials-userdefined':
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(vidcap.get(cv2.CAP_PROP_POS_FRAMES)+trp[0]*FPS))
    t0_analysis = int(vidcap.get(cv2.CAP_PROP_POS_MSEC))
    print('analyzing behavior for trial {} from {}'.format(S+1,t0_analysis/1000))
    
    thresh_level_animal = thresh_dict['animal']
    roi_a = frame[a_dict['ymin']:a_dict['ymin']+a_dict['height'],a_dict['xmin']:a_dict['xmin']+a_dict['width']]
    lbl_a,thresh_a,level_a = thresholdImage(roi_a,thresh_level_animal,adaptive=False,dynamic=True)
    roi_a_n1 = np.zeros( (a_dict['height'],a_dict['width']) )
    roi_a_n2 = np.zeros( (a_dict['height'],a_dict['width']) )
    
    x0 = xform['x0']
    ymin = xform['ymin']
    y0_max = xform['y0_max']
    mx1 = xform['mx1']
    mx2 = xform['mx2']
    my = xform['my']

    if interval_type == 'trials-automatic':
        thresh_level_shadow = thresh_dict['shadow']
        roi_sh = frame[sh_dict['ymin']:sh_dict['ymin']+sh_dict['height'],sh_dict['xmin']:sh_dict['xmin']+sh_dict['width']]
        lbl_sh,thresh_sh,level_sh = thresholdImage(roi_sh,thresh_level_shadow,adaptive=False)

    p_cols = ['xc','yc','minr','maxr','maj-ax','min-ax','orientation','x-pos','y-pos']
    d_cols = ['x-corr','y-corr','x-vel','y-vel','speed']
    b_cols = ['rear','freeze','escape','hide']
    df0,p_cols = initializeDF(p_cols,d_cols,b_cols,trp,FPS)
    print(df0.head())
    d_cols = p_cols + d_cols
    b_cols = d_cols + b_cols    
    #will need to pass another variable to analyzeTrial

    if plot:
        fig,plot_dict,data_dict = initializeFigAxes(trp,FPS,rlim,vlim,thresh_a,thresh_sh,arena_corners)
    t_idx = 0
    shadow_detected = False
    
    escape = False
    # set initial primitives
    while int(vidcap.get(cv2.CAP_PROP_POS_MSEC)) < (t0_analysis + (trp[1]-trp[0])*1000):
        success,frame = vidcap.read()
        if frame is None:
            break
        key = cv2.waitKey(1)
        
        roi_a = frame[a_dict['ymin']:a_dict['ymin']+a_dict['height'],a_dict['xmin']:a_dict['xmin']+a_dict['width']]
        if t_idx > 1:
            roi_a = cv2.blur(cv2.cvtColor(cv2.cvtColor(roi_a, cv2.COLOR_BGR2RGB), cv2.COLOR_BGR2GRAY),(6,6))
            roi_a_avg = np.float32(roi_a*0.6 + roi_a_n1*0.3 + roi_a_n2*0.1)
            lbl_a,thresh_a,level_a = thresholdImage(roi_a_avg,level_a,adaptive=False,dynamic=True,ymin = ymin,ymax=y0_max+ymin-25)
        elif t_idx > 0:
            lbl_a,thresh_a,level_a = thresholdImage(roi_a,thresh_level_animal,adaptive=False,dynamic=True)
        else:
            lbl_a,thresh_a,level_a = thresholdImage(roi_a,thresh_level_animal,adaptive=False,dynamic=True)
        roi_a_n2 = roi_a_n1
        roi_a_n1 = cv2.blur(cv2.cvtColor(cv2.cvtColor(roi_a, cv2.COLOR_BGR2RGB), cv2.COLOR_BGR2GRAY),(6,6))
        
        if interval_type == 'other':
            df0.iloc[t_idx, [df0.columns.get_loc(col) for col in p_cols]] = getPrimitives(lbl_a,df0.iloc[t_idx, [df0.columns.get_loc(col) for col in p_cols]],ymin = ymin,ymax=y0_max+ymin-25,interval_type=interval_type)
        
        elif interval_type == 'trials-userdefined':
            relative_time = df0.at[t_idx,'time']
            df0.iloc[t_idx, [df0.columns.get_loc(col) for col in p_cols]] = getPrimitives(lbl_a,df0.iloc[t_idx, [df0.columns.get_loc(col) for col in p_cols]],ymin = ymin,ymax=y0_max+ymin-25,interval_type=interval_type,shadow_period_exact=shp,relative_time = relative_time)
        
        elif interval_type == 'trials-automatic':
            roi_sh = frame[sh_dict['ymin']:sh_dict['ymin']+sh_dict['height'],sh_dict['xmin']:sh_dict['xmin']+sh_dict['width']]
            lbl_sh,thresh_sh,level_sh = thresholdImage(roi_sh,thresh_level_shadow)          #global binarization            
            df0.iloc[t_idx, [df0.columns.get_loc(col) for col in p_cols]] = getPrimitives(lbl_a,df0.iloc[t_idx, [df0.columns.get_loc(col) for col in p_cols]],ymin = ymin,ymax=y0_max+ymin-25,interval_type=interval_type,lbl_sh=lbl_sh)
        
        if t_idx > 0:
            
            if ((df0.at[t_idx,'maj-ax'] / df0.at[t_idx,'min-ax']) > 2.0) and (abs(df0.at[t_idx,'orientation']) < 0.6):
                df0.at[t_idx,'y-pos'] = df0.at[t_idx,'yc'] + math.cos(df0.at[t_idx,'orientation'])*0.5*df0.at[t_idx,'maj-ax']
                df0.at[t_idx,'x-pos'] = df0.at[t_idx,'xc'] + math.sin(df0.at[t_idx,'orientation'])*0.5*df0.at[t_idx,'maj-ax']
            else:    
                df0.at[t_idx,'y-pos'] = df0.at[t_idx,'yc'] + (df0.at[t_idx,'maxr']-df0.at[t_idx,'minr'])*1/3
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
            df0.at[t_idx,'escape'],escape = getEscape(df0.at[t_idx,'shadow'],abs(df0.at[t_idx,'speed']),15,1.0,escape,hide,rear)
        
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
            
            updateFigure(plot_dict,data_dict,thresh_sh,thresh_a)
        
        t_idx += 1

    df0.interpolate(inplace=True)              # interpolate missing data
    df0.to_csv(csvfilename)
    
    if plot:
        plt.close(fig)
    
    if interval_type == 'trials-automatic' or interval_type == 'trials-userdefined':
        found_hide = False
        escape_trial = False
        idxs = int(FPS * 10 ) + 1
        idxs_old = idxs
        idxh = int(FPS * 10 ) + 1
        while ( (df0.at[idxs,'shadow'] == 'True') and (df0.at[idxs_old,'shadow'] == 'True') ) or ( (df0.at[idxs,'shadow'] == True) and (df0.at[idxs_old,'shadow'] == True) ):
            idxs_old = idxs
            idxs += 1
            if not found_hide:
                idxh += 1
                if df0.at[idxh,'hide'] == 1.0 or df0.at[idxh,'hide'] == '1.0':
                    found_hide = True
                    escape_trial = True
        tS_end = float(df0.at[idxs,'time'])
        
        if escape_trial:
            tH_init = float(df0.at[idxh,'time'])
            idxe = idxh
            while df0.at[idxe,'escape'] == 0.0 or df0.at[idxe,'escape'] == '0.0':
                print(idxe,df0.at[idxe,'escape'])
                idxe -= 2
            while df0.at[idxe,'escape'] == 1.0 or df0.at[idxe,'escape'] == '1.0':
                print(idxe,df0.at[idxe,'escape'])
                idxe -= 2
            tE_init = float(df0.at[idxe,'time'])
        else:
            tH_init = 'n/a'
            tE_init = 'n/a'
        
        #row = ['animal','day','trial','shadowON','escape','hide','shadowOFF']
        key_timings = [tS_start,tE_init,tH_init,tS_end]
            
        print('timing data in analyzeTrial: ',key_timings)    
        return key_timings    
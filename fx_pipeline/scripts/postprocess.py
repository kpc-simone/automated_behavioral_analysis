# plot_trial_feature.py
from tkinter.filedialog import askopenfilenames
import matplotlib.pyplot as plt
from scipy import signal
import numpy as np
import pandas as pd
import sys,os
import re

def getFreezeBouts(speed_ts,f_threshold=0.025):
    freeze_bouts = np.zeros( (len(speed_ts,) ) )
    for idx,speed in enumerate(speed_ts):
        if (speed < f_threshold):
            freeze_bouts[idx] = 1.0
            
    return freeze_bouts
            
def getEscapeBouts(speed_ts,hide_ts,shadow_ts,v_threshold1=0.25,v_threshold2=0.025):
    escape_bouts = np.zeros( (len(speed_ts,) ) )
    in_escape_bout = False
    
    for idx,(shadow,hide,speed) in enumerate(zip(shadow_ts,hide_ts,speed_ts)):
        if shadow and hide < 1.0:
            if not in_escape_bout:     
                escape_bouts[idx] = 0.0
                if (speed > v_threshold1):
                    in_escape_bout = True
            if in_escape_bout:
                escape_bouts[idx] = 1.0
                if (speed < v_threshold2):
                    in_escape_bout = False
        else:     
            in_escape_bout = False
    return escape_bouts

def getHideBouts(xcorr_ts,ycorr_ts,y_thresh=0.130,x_thresh = 0.01):
    hide_bouts = np.zeros( (len(xcorr_ts,) ) )
    
    for idx,(xcorr,ycorr) in enumerate(zip(xcorr_ts,ycorr_ts)):
        if xcorr < x_thresh and ycorr < y_thresh:
            hide_bouts[idx] = 1.0
        else:
            hide_bouts[idx] = 0.0
            
    return hide_bouts

if __name__ == "__main__":
    args = sys.argv[1:]

if '--frontview' in args:
    behaviors = ['freeze','escape','hiding','rearing']
else:
    behaviors = ['freeze','escape','hiding']

files = askopenfilenames()
print(files)

primitives = ['x-corr','y-corr']
derivatives = ['x-vel','y-vel','speed']

FPS = float(input('Enter FPS for this batch of feature timeseries: '))

for file in files:
    print(file)
    df = pd.read_csv(file)
    df = df.interpolate(method='linear')
    fig, axes = plt.subplots(len(primitives)+len(derivatives)+len(behaviors)+1,1,squeeze=False,sharex=True,figsize=(16,10))
        
    b,a = signal.butter(5,0.2)
    for i,feature in enumerate(primitives):
    
        # convert mm to m
        if ( ( feature == 'x-corr') | ( feature == 'y-corr' ) ):
            df[feature] = df[feature] / 1000   
            unit = 'm'
            df['{}-filtered'.format(feature)] = signal.filtfilt(b,a,df[feature].fillna(value=0.0).to_numpy())
            axes[i,0].plot(df['time-aligned'],df[feature],color='dimgray',label='original')
            axes[i,0].plot(df['time-aligned'],df['{}-filtered'.format(feature)],color='k',linestyle='--',label='filtered')
            axes[i,0].set_ylabel('{} ({})'.format(feature,unit))

    # convert velocities from mm/frame to m/s, given FPS
    for i,feature in enumerate(derivatives):
        unit = 'm/s'
        if feature == 'speed':
            df[feature] = df[feature] * FPS / 1000
            df['speed-filtered'] = np.sqrt(df['x-vel-filtered']**2+df['y-vel-filtered']**2)
            axes[i+2,0].plot(df['time-aligned'],df[feature],color='dimgray',label='original')
            axes[i+2,0].plot(df['time-aligned'],df['{}-filtered'.format(feature)],color='k',linestyle='--',label='filtered')
            axes[i+2,0].set_ylabel('{} ({})'.format(feature,unit))
            axes[i+2,0].set_ylim( [0.0,1.0] )
        else:
            df[feature] = df[feature] * FPS / 1000
            df['{}-filtered'.format(feature)] = df['{}-corr-filtered'.format(feature[:1])].diff() * FPS
            axes[i+2,0].plot(df['time-aligned'],df[feature],color='dimgray',label='original')
            axes[i+2,0].plot(df['time-aligned'],df['{}-filtered'.format(feature)],color='k',linestyle='--',label='filtered')
            axes[i+2,0].set_ylabel('{} ({})'.format(feature,unit))
            axes[i+2,0].set_ylim( [-1.0,1.0] )

    f_threshold = 0.05
    v_threshold1 = 0.25
    v_threshold2 = f_threshold
    df['freeze-filtered'] = getFreezeBouts(df['speed-filtered'],f_threshold = f_threshold)
    df['escape-filtered'] = getEscapeBouts(df['speed-filtered'],df['hide'],df['shadow-cleaned'],v_threshold1=v_threshold1,v_threshold2=v_threshold2)
    df['hide-filtered'] = getHideBouts(df['x-corr-filtered'],df['y-corr-filtered'],y_thresh = 0.130,x_thresh = 0.01)

    axes[5,0].plot(df['time-aligned'],df['freeze-filtered'],color='#92ab87FF')
    axes[5,0].set_ylabel('freeze')
    axes[6,0].plot(df['time-aligned'],df['escape-filtered'],color='#55868CFF')
    axes[6,0].set_ylabel('escape')
    axes[7,0].plot(df['time-aligned'],df['hide-filtered'],color='#675159FF')
    axes[7,0].set_ylabel('hide')

    if 'rearing' in behaviors:
        axes[-2,0].plot(df['time-aligned'],df['rear'],color='#EBBC6Fff')
        axes[-2,0].set_ylabel('rear')

    axes[-1,0].plot(df['time-aligned'],df['shadow-cleaned'],color='k')
    axes[-1,0].set_ylabel('shadow')
    axes[-1,0].set_xlabel('Time (s)')

    for ax in axes.ravel():
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        #ax.set_xlim(-30,30)
            
    print(df.head())
    
    filename = file.split('/')[-1]
    axes[-1,0].legend(loc='upper left',frameon=False)
    fig.tight_layout()
    plt.savefig('../../fx_analyses/{}.png'.format(filename[:-4]),format='png')
    plt.show()

    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.to_csv('../../fx_analyses/{}-postprocessed.csv'.format(filename[:-4]))
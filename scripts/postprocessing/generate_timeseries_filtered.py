# plot_trial_feature.py
from tkinter.filedialog import askopenfilenames
import matplotlib.pyplot as plt
from scipy import signal
import numpy as np
import pandas as pd
import sys,os
import re

files = askopenfilenames()
print(files)

primitives = ['x-corr','y-corr']
derivatives = ['x-vel','y-vel','speed']

for file in files:
    df = pd.read_csv(file)
    FPS = float(input('Enter FPS for this feature timeseries: '))
    fig, axes = plt.subplots(len(primitives)+len(derivatives)+1,1,squeeze=False,sharex=True,figsize=(16,10))
        
    b,a = signal.butter(5,0.2)
    for i,feature in enumerate(primitives):
    
        # convert mm to m
        if ( ( feature == 'x-corr') | ( feature == 'y-corr' ) ):
            df[feature] = df[feature] / 1000   
            unit = 'm'
            df['{}-filtered'.format(feature)] = signal.filtfilt(b,a,df[feature].fillna(value=0.0).to_numpy())
            axes[i,0].plot(df['time'],df[feature],color='dimgray',label='original')
            axes[i,0].plot(df['time'],df['{}-filtered'.format(feature)],color='k',linestyle='--',label='filtered')
            axes[i,0].set_ylabel('{} ({})'.format(feature,unit))

    # convert velocities from mm/frame to m/s, given FPS

    for i,feature in enumerate(derivatives):
        unit = 'm/s'
        if feature == 'speed':
            df[feature] = df[feature] * FPS / 1000
            df['speed-filtered'] = np.sqrt(df['x-vel-filtered']**2+df['y-vel-filtered']**2)
            axes[i+2,0].plot(df['time'],df[feature],color='dimgray',label='original')
            axes[i+2,0].plot(df['time'],df['{}-filtered'.format(feature)],color='k',linestyle='--',label='filtered')
            axes[i+2,0].set_ylabel('{} ({})'.format(feature,unit))
        else:
            df[feature] = df[feature] * FPS / 1000
            df['{}-filtered'.format(feature)] = df['{}-corr-filtered'.format(feature[:1])].diff() * FPS
            axes[i+2,0].plot(df['time'],df[feature],color='dimgray',label='original')
            axes[i+2,0].plot(df['time'],df['{}-filtered'.format(feature)],color='k',linestyle='--',label='filtered')
            axes[i+2,0].set_ylabel('{} ({})'.format(feature,unit))

    axes[5,0].plot(df['time'],df['shadow'],color='k')
    axes[5,0].set_ylabel('shadow')

    for ax in axes.ravel():
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
            
    print(df.head())
    
    filename = file.split('/')[-1]
    axes[0,0].legend(loc='upper right',frameon=False)
    plt.savefig('../../video_analyses/{}.png'.format(filename[:-4]),format='png')
    plt.show()

    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.to_csv('../../video_analyses/{}-postprocessed.csv'.format(filename[:-4]))
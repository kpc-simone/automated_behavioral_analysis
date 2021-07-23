# clean_align_shadows.py

from tkinter.filedialog import askopenfilename,askopenfilenames
import matplotlib.pyplot as plt
import pandas as pd
import sys,os

print("select csv with manually-annotated shadow key timings")
man_df = pd.read_csv(askopenfilename())

print("select feature csv's to clean")
feature_csvs = askopenfilenames()

FPS = int(input('enter FPS for this set of feature timeseries CSVS: '))
for feature_csv in feature_csvs:

    fig,axes = plt.subplots(2,1,sharex=True,squeeze=False)
    fdf = pd.read_csv(feature_csv)
    print(fdf.head())
    
    feature_csv_filename = os.path.split(feature_csv)[-1]
    animal = feature_csv_filename.split('-')[1]
    day = feature_csv_filename.split('-')[2]  
    
    print('cleaning {} for animal {}, day {}'.format(feature_csv_filename,animal,day))
    
    # look up manual trial key timings for this assay
    a_df = man_df[ (man_df['animal'] == animal) & (man_df['day'] == int(day)) ]
    t_sh0 = a_df['shadowON-abs'].iloc[0]
    
    fdf['shadow-cleaned'] = fdf['shadow']
    fdf.loc[:,'shadow-cleaned'].iloc[:int(t_sh0*FPS)] = False
    
    tidx = fdf.index[-1]
    time = fdf['time'].iloc[-1]
    shadow = fdf['shadow-cleaned'].iloc[-1]
    while(time > 0):
        time = fdf['time'].iloc[tidx]
        shadow = fdf['shadow-cleaned'].iloc[tidx]
        
        if shadow:
            fdf.loc[:,'shadow-cleaned'].iloc[int(tidx-6*FPS):tidx] = True
            tidx -= int(10*FPS)
            print('shadow found, skipping to index: {}, time: {}'.format(tidx,fdf.loc[:,'time'].iloc[int(tidx)]))
        else:    
            tidx -= 1    
        #print(idx,time,value)
        
    
    axes[0,0].plot(fdf['time'],fdf['shadow'],color='k')
    axes[0,0].set_ylabel('shadow')
    
    axes[1,0].plot(fdf['time'],fdf['shadow-cleaned'],color='k')
    axes[1,0].set_ylabel('shadow, cleaned')
    
    for ax in axes.ravel():
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    axes[1,0].set_xlabel('Time (s)')
    plt.show()
    
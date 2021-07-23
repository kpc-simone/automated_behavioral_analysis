from tkinter.filedialog import askopenfilename
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def draw_box(ax,bb):

    # a fancy box with round corners. pad=0.1
    box = mpatches.FancyBboxPatch((bb['xmin']+10, bb['ymin']+10),
                             abs(bb['width']-20), abs(bb['height']-20),
                             boxstyle="round,pad=10.0",
                             fc=(0.9, 0.9, 0.9),
                             ec=(0.1, 0.1, 0.1))

    ax.add_patch(box)

plots = {
    'trajectory'            :   'plot_trajectory(dfa,fig,ax)',
    'dg_cumu'               :   'plot_dg_cumu(dfa,fig,ax)',
    'center_cumu'           :   'plot_center_cumu(dfa,fig,ax)',
    'vel_hist'              :   'plot_vel_hist(dfa,fig,ax)',
    'trajectory_1_3'        :   'plot_trajectory_1_3(dfa,fig,ax)',
    'trajectory_3_5'        :   'plot_trajectory_3_5(dfa,fig,ax)',    
    'defensive strategy'    :   'plot_defensive_strategy(animal,ax)',
}

# def plot_trajectory(dfa,fig,ax):
    # ax.plot(dfa['x-corr'],dfa['y-corr'],color='dimgray',alpha=0.5)
    
    # a_corr = {
    # 'xmin'      : -150,
    # 'ymin'      : 0,
    # 'width'     : 300,
    # 'height'    : 500,
    # }

    # draw_box(ax,a_corr)
    # ax.set_xlim(-150,150)
    # ax.set_ylim(500,0)
    # nest = plt.Rectangle((-145, 0), 160, 120,facecolor='#482677FF', alpha=0.5)
    # ax.add_patch(nest)
    # ax.set_axis_off()

def plot_trajectory(dfa,fig,ax):
    scale = ax.scatter(dfa['x-corr'],dfa['y-corr'],s=0.5,c=dfa['speed']*20/1000,zorder=15,cmap='inferno',vmin=0,vmax=0.5,alpha=1)
    
    a_corr = {
    'xmin'      : -150,
    'ymin'      : 0,
    'width'     : 300,
    'height'    : 500,
    }

    draw_box(ax,a_corr)
    ax.set_xlim(-150,150)
    ax.set_ylim(500,0)
    nest = plt.Rectangle((-145, 0), 160, 120,facecolor='#482677FF', alpha=0.5)
    ax.add_patch(nest)
    ax.set_axis_off()
    cbar = fig.colorbar(scale,ax=ax)
    cbar.set_label('Speed (m/s)')
    
    center = plt.Rectangle((-50, 150), 100, 200,facecolor='None',linestyle='--',edgecolor='k')
    ax.add_patch(center)

    dangerzone = plt.Rectangle((-150, 250), 300, 250,facecolor='None',linestyle='--',edgecolor='r')
    ax.add_patch(dangerzone)

def plot_trajectory_1_3(dfa,fig,ax):
    FPS = 20
    idx1 = ( 1 - 1 ) * 60 * FPS
    idx2 = ( 3 - 1 ) * 60 * FPS
    ax.plot(dfa['x-corr'].iloc[idx1:idx2],dfa['y-corr'].iloc[idx1:idx2],color='dimgray',alpha=0.5)
    
    a_corr = {
    'xmin'      : -150,
    'ymin'      : 0,
    'width'     : 300,
    'height'    : 500,
    }

    draw_box(ax,a_corr)
    ax.set_xlim(-150,150)
    ax.set_ylim(500,0)
    nest = plt.Rectangle((-145, 0), 160, 120,facecolor='#482677FF', alpha=0.5)
    ax.add_patch(nest)
    ax.set_axis_off()
    
def plot_trajectory_3_5(dfa,fig,ax):
    FPS = 20
    idx1 = ( 3 - 1 ) * 60 * FPS
    idx2 = ( 5 - 1 ) * 60 * FPS
    ax.plot(dfa['x-corr'].iloc[idx1:idx2],dfa['y-corr'].iloc[idx1:idx2],color='dimgray',alpha=0.5)
    
    a_corr = {
    'xmin'      : -150,
    'ymin'      : 0,
    'width'     : 300,
    'height'    : 500,
    }

    draw_box(ax,a_corr)
    ax.set_xlim(-150,150)
    ax.set_ylim(500,0)
    nest = plt.Rectangle((-145, 0), 160, 120,facecolor='#482677FF', alpha=0.5)
    ax.add_patch(nest)
    ax.set_axis_off()    

def plot_dg_cumu(dfa,fig,ax):
    dfa['y-corr-dg'] = 1/20
    dfa['y-corr-dg'] = dfa['y-corr-dg'].where(dfa['y-corr'] > 250, other = 0)
    #ax.plot(dfa['time'],dfa['y-corr-dg'],color='b',alpha=0.6,label='instantaneous')
    ax.plot(dfa['time'],dfa['y-corr-dg'].cumsum(),color='r',alpha=0.6,label='cumulative')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

def plot_center_cumu(dfa,fig,ax):
    dfa['center'] = 1/20
    dfa['center'] = dfa['center'].where( (dfa['x-corr'] > -50) & (dfa['x-corr'] < 50) & (dfa['y-corr'] > 150) & (dfa['y-corr'] < 350), other = 0)
    #ax.plot(dfa['time'],dfa['center'],color='b',alpha=0.6,label='instantaneous')
    ax.plot(dfa['time'],dfa['center'].cumsum(),color='k',alpha=0.6,label='cumulative')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

def plot_vel_hist(dfa,fig,ax):
    ax.hist(dfa['speed'] * 20 / 1000,50,range=(0,0.5),facecolor='dimgray',alpha=0.6) # mm/frame * frames / sec (20) * m / mm (1/1000)
    ax.set_xlim(0,0.5)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
def plot_defensive_strategy(animal,ax):
    
    behavior = {
        'animals'   :   ['m910','m911','m930','m931','m932'],
        'escapes'   :   [5 ,5 ,5 ,5, 4],
        'avoids'    :   [0 ,0 ,0 ,0, 0],
        'freezes'   :   [0 ,0 ,0 ,0, 1],
    }
    df = pd.DataFrame(behavior)
    
    totals = [i+j+k for i,j,k in zip(df['escapes'], df['avoids'], df['freezes'])]
    escapes = [i / j * 100 for i,j in zip(df['escapes'], totals)]
    avoids = [i / j * 100 for i,j in zip(df['avoids'], totals)]
    freezes = [i / j * 100 for i,j in zip(df['freezes'], totals)]
    
    r = behavior['animals'].index(animal)    
    
    barWidth = 0.5 
    ax.bar(0, escapes[r], color='#279edd', edgecolor='black', width=barWidth)
    ax.bar(0, avoids[r], bottom=escapes[r], color='#009999', edgecolor='black', width=barWidth)
    f_bottoms = escapes[r] + avoids[r]
    ax.bar(0, freezes[r], bottom=f_bottoms, color='#27c687', edgecolor='black', width=barWidth)
    ax.set_xticklabels([])
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
# todo change to gridspec framework
features = plots.keys()
#animals = ['m913','m914','m933','m934']
animals = ['m910','m911','m930','m931','m932']
fig, axes = plt.subplots(len(animals),len(features),squeeze = False,figsize=( len(features)*2, len(animals)*3.3),sharey='col')

for i,animal in enumerate(animals):
    dfa = pd.read_csv('../tonic-{}-1-12-habituation.csv'.format(animal))
    for j,feature in enumerate(features):
        ax = axes[i,j]
        eval(plots[feature])
    axes[i,0].set_ylabel(animal)   

axes[0,0].set_title('Position and Speed, \n60s - 300s')

axes[0,1].set_title('Time spent in "Danger Zone"')
axes[0,1].legend(loc='lower right',frameon=False,fontsize='small')    
axes[0,1].set_xlabel('Time (s)')
axes[0,1].set_ylabel('Time (s)')

axes[0,2].set_title('Time spent in arena center')
axes[0,2].legend(loc='lower right',frameon=False,fontsize='small')    
axes[0,2].set_xlabel('Time (s)')
axes[0,2].set_ylabel('Time (s)')

axes[0,3].set_title('Distribution of Speed')
axes[0,3].set_xlabel('Speed (m/s)')
axes[0,3].set_ylabel('Counts')
    
axes[0,4].set_title('Trajectory, \n60s - 180s')
axes[0,5].set_title('Trajectory, \n180s - 300s')    
axes[0,6].set_title('Defensive Strategies')    
    
fig.tight_layout()
plt.show()        
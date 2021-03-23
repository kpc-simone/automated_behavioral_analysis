import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import math

from image_video_processing import thresholdImage

def draw_box(ax,bb):

    # a fancy box with round corners. pad=0.1
    box = mpatches.FancyBboxPatch((bb['xmin']+10, bb['ymin']+10),
                             abs(bb['width']-20), abs(bb['height']-20),
                             boxstyle="round,pad=10.0",
                             fc=(0.9, 0.9, 0.9),
                             ec=(0.1, 0.1, 0.1))

    ax.add_patch(box)

def initializeFigAxes(trp,FPS,rlim,vlim,thresh_a,thresh_sh,arena_corners):
    
    fig = plt.figure(figsize=(18,8))
    gs = GridSpec(5,8,figure=fig)

    ax1 = fig.add_subplot(gs[:3,:3])
    ax2 = fig.add_subplot(gs[3:,:3])
    ax_f = fig.add_subplot(gs[0,3:6])
    ax_e = fig.add_subplot(gs[1,3:6],sharex=ax_f)
    ax_r = fig.add_subplot(gs[2,3:6],sharex=ax_e)
    ax_h = fig.add_subplot(gs[3,3:6],sharex=ax_r)
    ax_s = fig.add_subplot(gs[4,3:6],sharex=ax_h)
    ax_p = fig.add_subplot(gs[:,6:])
    
    for ax in (ax1,ax2,ax_p):
        ax.set_axis_off()
    
    for ax in (ax_s,ax_f,ax_r,ax_e,ax_h):
        ax.set_xlim(trp[0],trp[1])
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        
    for ax in (ax_f,ax_e,ax_h,ax_r):            
        ax.set_ylim(-0.1,1.1)
                
    ax_s.set_ylim(0.0,vlim)
    
    ax_p.set_xlim(-150,150)
    ax_p.set_ylim(500,0)
    
    fig.subplots_adjust(wspace=1.0)
    fig.subplots_adjust(hspace=0.5)
    
    data_dict = {}
    dict_entries = ['xdata','ydata','xdata1','ydata1','xdata2','ydata2','tdata','vydata','vxdata','sdata','fdata','rdata','edata','hdata','pxdata','pydata']
    for entry in dict_entries:
        data_dict[entry] = []
    
    arena = ax1.imshow(thresh_a,cmap='gray')

    x,y, = [],[]
    
    for i,point in enumerate(arena_corners):
        x = arena_corners[point][0]
        y = arena_corners[point][1]
        if i == 0:
            xi = x
            yi = y
        elif i < 3:
            ax1.plot((x_old,x),(y_old,y),color='dimgray')
        elif i == 3:    
            ax1.plot((x_old,x),(y_old,y),color='dimgray')
            ax1.plot((x,xi),(y,yi),color='dimgray')
        x_old = x     
        y_old = y
    
    shadow = ax2.imshow(thresh_sh,cmap='gray')
    minor_axis, = ax1.plot(data_dict['xdata1'], data_dict['ydata1'], '-r', linewidth=1.0)
    major_axis, = ax1.plot(data_dict['xdata2'], data_dict['ydata2'], '-r', linewidth=1.0)
    position, = ax1.plot(data_dict['xdata'], data_dict['ydata'], color='silver',marker='.', markersize=10)
    f_state, = ax_f.plot(data_dict['tdata'],data_dict['fdata'], color='#29AF7FFF',linewidth=2.0)
    e_state, = ax_e.plot(data_dict['tdata'],data_dict['edata'], color='#33638DFF',linewidth=2.0)
    h_state, = ax_h.plot(data_dict['tdata'],data_dict['hdata'], color='#482677FF',linewidth=2.0,)
    r_state, = ax_r.plot(data_dict['tdata'],data_dict['rdata'], color='#FDE725FF',linewidth=2.0)
    s_state, = ax_s.plot(data_dict['tdata'],data_dict['sdata'], color='dimgray',linewidth=2.0)
    vx_state, = ax_s.plot(data_dict['tdata'],data_dict['vxdata'], color='steelblue',linewidth=2.0)
    vy_state, = ax_s.plot(data_dict['tdata'],data_dict['vydata'], color='firebrick',linewidth=2.0)
    p_state, = ax_p.plot(data_dict['pxdata'],data_dict['pydata'], color='dimgray',linewidth=2.0)
    
    plot_dict = {
    'arena'             :   arena,
    'shadow'            :   shadow,
    'minor_axis'        :   minor_axis,
    'major_axis'        :   major_axis,
    'position'          :   position,
    'f_state'           :   f_state,
    'e_state'           :   e_state,
    'h_state'           :   h_state,
    'r_state'           :   r_state,
    's_state'           :   s_state,
    'vx_state'          :   vx_state,
    'vy_state'          :   vy_state,
    'p_state'           :   p_state,
    }
    
    a_corr = {
    'xmin'      : -150,
    'ymin'      : 0,
    'width'     : 300,
    'height'    : 500,
    }
    
    draw_box(ax_p,a_corr)
    nest = plt.Rectangle((-145, 0), 160, 120,
                     facecolor='#482677FF', alpha=0.5)

    ax_p.add_patch(nest)
    
    return fig, plot_dict, data_dict

def updateFigure(plot_dict,data_dict,thresh_sh,thresh_a):
    
    plot_dict['shadow'].set_data(thresh_sh)
    plot_dict['arena'].set_data(thresh_a)
    plot_dict['minor_axis'].set_data(data_dict['xdata1'],data_dict['ydata1'])
    plot_dict['major_axis'].set_data(data_dict['xdata2'],data_dict['ydata2'])
    plot_dict['f_state'].set_data(data_dict['tdata'],data_dict['fdata'])
    plot_dict['s_state'].set_data(data_dict['tdata'],data_dict['sdata'])
    plot_dict['e_state'].set_data(data_dict['tdata'],data_dict['edata'])
    plot_dict['r_state'].set_data(data_dict['tdata'],data_dict['rdata'])
    plot_dict['h_state'].set_data(data_dict['tdata'],data_dict['hdata'])
    
    if len(data_dict['tdata']) > 1:
        plot_dict['p_state'].set_data(data_dict['pxdata'],data_dict['pydata'])
        plot_dict['position'].set_data(data_dict['xdata'],data_dict['ydata'])
        plot_dict['vx_state'].set_data(data_dict['tdata'],data_dict['vxdata'])
        plot_dict['vy_state'].set_data(data_dict['tdata'],data_dict['vydata'])
    
    plt.draw()
    plt.pause(1e-17)
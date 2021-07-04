from tkinter.filedialog import askopenfilename
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

def draw_box(ax,bb):

    # a fancy box with round corners. pad=0.1
    box = mpatches.FancyBboxPatch((bb['xmin']+10, bb['ymin']+10),
                             abs(bb['width']-20), abs(bb['height']-20),
                             boxstyle="round,pad=10.0",
                             fc=(0.9, 0.9, 0.9),
                             ec=(0.1, 0.1, 0.1))

    ax.add_patch(box)

analysis_file = askopenfilename()

dfa = pd.read_csv(analysis_file)
print(dfa.head(25))

fig, axes = plt.subplots(1,2,squeeze=False,figsize=(6,5))

axes[0,0].plot(-dfa['yc']/2.02,dfa['xc']/1.83,color='dimgray',zorder=10)
#axes[0,1].plot(dfa['x-corr-filtered']*1000,dfa['y-corr-filtered']*1000,color='dimgray',zorder=10)

a_corr = {
'xmin'      : -300,
'ymin'      : 0,
'width'     : 300,
'height'    : 500,
}
for ax in axes.ravel():
    draw_box(ax,a_corr)
    ax.set_xlim(-300,0)
    ax.set_ylim(500,0)
    nest = plt.Rectangle((-300, 0), 160, 120,facecolor='#482677FF', alpha=0.5)
    ax.add_patch(nest)
    ax.set_axis_off()

axes[0,0].set_title('Original')
axes[0,1].set_title('Filtered')

plt.show()
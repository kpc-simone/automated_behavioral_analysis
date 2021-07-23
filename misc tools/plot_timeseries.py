# plot_trial_feature.py
from tkinter.filedialog import askopenfilename
import matplotlib.pyplot as plt
import pandas as pd
import sys,os
import re

analysis_file = askopenfilename()
df = pd.read_csv(analysis_file)
for col in df.columns:
    print(col)

if __name__ == '__main__':
    features = list(sys.argv[1:])
    
fig, axes = plt.subplots(len(features),1,squeeze=False,sharex=True)
    
for i,feature_str in enumerate(features):
    feature = feature_str[2:]
    print(feature)
    axes[i,0].plot(df['time-aligned'],df[feature])
    axes[i,0].set_ylabel(feature)

plt.show()
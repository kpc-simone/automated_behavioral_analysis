import pandas as pd

def findShadow(fdf, idx_start = 0):
    
    shadow_found = False
    idxs = idx_start
    while ( (fdf.at[idxs,'shadow'] == False) and ( idxs < ( len(fdf) - 2 ) ) ):
        idxs += 1
        if fdf.at[idxs+1,'shadow'] == True:
            shadow_found = True
            print('shadow found at index {}'.format(idxs+1))
            idx_start = idxs+1
            break
    
    if shadow_found:
        idxs = idx_start
        while ( (fdf.at[idxs,'shadow'] == True) ) :
            idxs += 1
        idx_end = idxs
        return True, [idx_start, idx_end]
        
    else:    
        return False, [idx_start,idx_start]
    

def getKeyTimings(fdf, idx_start = 0, escape_colname = 'escape-filtered', hide_colname = 'hide-filtered'):
    found_hide = False
    escape_trial = False    
    
    idxs = idx_start
    idxs_old = idxs
    idxh = idxs
    
    while ( (fdf.at[idxs,'shadow'] == True) and (fdf.at[idxs_old,'shadow'] == True) ) :
        idxs_old = idxs
        idxs += 1
        if not found_hide:
            idxh += 1
            if fdf.at[idxh,hide_colname] == 1.0 or fdf.at[idxh,hide_colname] == '1.0':
                found_hide = True
                escape_trial = True
    
    if escape_trial:
        tH_init = float(fdf.at[idxh,'time'])
        idxe = idxh
        while fdf.at[idxe,escape_colname] == 0.0 or fdf.at[idxe,escape_colname] == '0.0':
            idxe -= 2
        while fdf.at[idxe,escape_colname] == 1.0 or fdf.at[idxe,escape_colname] == '1.0':
            idxe -= 2
        tE_init = float(fdf.at[idxe,'time'])
    else:
        tH_init = 'n/a'
        tE_init = 'n/a'    
        
    return tE_init,tH_init

# write_key_timings.py
from tkinter.filedialog import askdirectory,askopenfilenames
from datetime import datetime
import csv
import os

print("select .csv's for which to extract key timings")
feature_CSVs = askopenfilenames()

print("select folder in which to save the output .csv")
analyses_folder = askdirectory()

now = datetime.now()
dtstr = now.strftime("%d%m%Y_%H%M%S")
out_CSV = os.path.join(analyses_folder,'automated_trial_keytimings_{}.csv'.format(dtstr))    
if not os.path.isfile(out_CSV):
    row = ['animal','day','trial','shadowON-abs','escape-rel','hide-rel','shadowOFF-rel']
    with open(out_CSV, 'w', newline='') as csvFile:
        filewriter = csv.writer(csvFile, delimiter = ',', quotechar = '|', quoting = csv.QUOTE_MINIMAL)
        filewriter.writerow(row)
    
for feature_csv in feature_CSVs:
    trial = 1
    feature_csv_filename = os.path.split(feature_csv)[-1]
    animal = feature_csv_filename.split('-')[1]
    day = feature_csv_filename.split('-')[2]    
    
    print('loading data for animal {} ...'.format(animal))
    fdf = pd.read_csv(feature_csv)
    print(fdf.head())
    
    print('{} day {} key timings: '.format(animal,day))
    while(True):
        if trial == 1:
            success,idxs = findShadow(fdf,idx_start = 0)
        elif idxs[1] < ( len(fdf) - 2 ) :
            # after the 1st trial, start looking for the next shadow after end of last shadow
            success,idxs = findShadow(fdf,idx_start = idxs[1]) 
        if success:
            print('trial {} indexes: {}'.format(trial,idxs))
        else:
            break
        
        tS_start = float(fdf.at[idxs[0],'time'])
        tE,tH = getKeyTimings(fdf, idx_start = idxs[0], escape_colname = 'escape-filtered', hide_colname = 'hide-filtered')        
        tS_end = float(fdf.at[idxs[1],'time']) - tS_start
        
        if type(tH) == float:
            tE = tE - tS_start
            tH = tH - tS_start
        
        row_data = [animal,day,trial,tS_start,tE,tH,tS_end]
        
        # oscillator_play comes to mind
        with open(out_CSV, 'a', newline='') as csvFile:
            filewriter = csv.writer(csvFile, delimiter = ',', quotechar = '|', quoting = csv.QUOTE_MINIMAL)
            filewriter.writerow(row_data)
            
        trial += 1    
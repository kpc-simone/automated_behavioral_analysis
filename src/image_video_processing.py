# image/video processing
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from skimage.measure import label, regionprops, regionprops_table
from skimage.morphology import disk, dilation, closing
import numpy as np
import math
import cv2

points = []

def getBackground(broi):

    gray = cv2.cvtColor(cv2.cvtColor(broi, cv2.COLOR_BGR2RGB), cv2.COLOR_BGR2GRAY)
    blur = cv2.blur(gray,(6,6))
    background = blur.mean(axis=0)

    return background

def selectROIs(frame):
    print('identify arena area')
    box_a = cv2.selectROIs("Frame", frame, fromCenter=False)
    ((xa,ya,wa,ha),) = tuple(map(tuple, box_a)) 
    a_dict = {
        'xmin'      : xa,
        'ymin'      : ya,
        'width'     : wa,
        'height'    : ha,
    }
    cv2.destroyAllWindows()
    
    print('identify shadow area')
    box_s = cv2.selectROIs("Frame", frame, fromCenter=False)
    ((xsh,ysh,wsh,hsh),) = tuple(map(tuple, box_s))
    sh_dict = {
        'xmin'      : xsh,
        'ymin'      : ysh,
        'width'     : wsh,
        'height'    : hsh,
    }
    cv2.destroyAllWindows()
	
    print('identify nest area')
    box_n = cv2.selectROIs("Frame", frame, fromCenter=False)
    ((xn,yn,wn,hn),) = tuple(map(tuple, box_n)) 
    nest_corners = {
        'xmin'          :   xn-xa,
        'ymin'          :   yn-ya,
        'width'         :   wn,        
        'height'        :   hn,
    }
    cv2.destroyAllWindows()

    return a_dict, sh_dict, nest_corners

def thresholdImage(roi,level,adaptive=False,dynamic=False,spatiodynamic=False,background=None,y_corr=0.0,ymin=150,ymax=475):
    gray = cv2.cvtColor(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB), cv2.COLOR_BGR2GRAY)
    blur = cv2.blur(gray,(6,6))
    
    if adaptive:
        thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,151,2)
        lbl = label(thresh,background=255)
    elif dynamic:
        ns, bins, = np.histogram(blur.ravel(), bins=511)
        sum_ns = np.cumsum(ns)
        counts_thresh = ((10000-3600)*(y_corr/500)+3600)
        for bin,sum_n in zip(bins[:-1],sum_ns):
            if sum_n > counts_thresh:
                level = bin
                #print('updated threshold: {}, difference: {}'.format(level, sum_n - counts_thresh))
                break
        ret,thresh = cv2.threshold(blur,level,255,cv2.THRESH_BINARY)
        lbl,num = label(thresh,background=255,return_num=True)
        
        # get all regions and sort by y-location of centroid
        regions = [region for region in sorted(regionprops(lbl), key=lambda r: r.centroid[0], reverse=True)]
        centroid_r0 = regions[0].centroid
        
        labels_to_merge = []
        labels_to_discard = []
        tol = 100*(1+y_corr/500)

        for region in [region for region in sorted(regionprops(lbl), key=lambda r: abs(r.centroid[0]-(ymax+ymin)/2),reverse=True)]:
            #print(region.label,region.centroid,region.area)
            
            if region.centroid[0] > ymin and region.centroid[0] < ymax and np.linalg.norm(np.asarray(region.centroid)-centroid_r0) < tol:
                labels_to_merge.append(region.label)            

        labels_to_discard = [label for label in range(1, lbl.max()+1) if label not in labels_to_merge]
        #print('labels to merge: {}, discard: {}'.format(labels_to_merge,labels_to_discard))

       # selem = disk(6)
        lbl = merge_labels(lbl,labels_to_discard,0)
        lbl = closing(merge_labels(lbl,labels_to_merge,1),np.ones((12,12)))
        #print(lbl.max())

        # figt,axt = plt.subplots(1,1)
        # axt.imshow(lbl)
        # plt.show(block=False)
        # plt.pause(0.5)
        # plt.close()
        
    else:    
        ret,thresh = cv2.threshold(blur,level,255,cv2.THRESH_BINARY) 
        lbl = label(thresh,background=255)
    
    return lbl, thresh, level

def merge_labels(labels_image,labels_to_merge,label_after_merge):
    labels_map = np.arange(np.max(labels_image)+1)
    labels_map[labels_to_merge] = label_after_merge
    return labels_map[labels_image]
	
def getShadowStatus(lbl_sh):
    #print('checking shadow')
    for region in sorted(regionprops(lbl_sh), key=lambda r: r.area, reverse=True):
        # fig,ax = plt.subplots(1,1)
        # ax.imshow(lbl_sh)
        # minr, minc, maxr, maxc = region.bbox
        # rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,fill=False, edgecolor='red', linewidth=2)
        # ax.add_patch(rect)
        # plt.show()
        
        if region.area >= 200 and region.solidity > 0.8:
            
            shadow_detected = True
            return shadow_detected
        else:
            shadow_detected = False
            return shadow_detected

def getShadowStatus2(lbl_sh):
    #print('checking shadow')
    for region in sorted(regionprops(lbl_sh), key=lambda r: r.area, reverse=True):
        # fig,ax = plt.subplots(1,1)
        # ax.imshow(lbl_sh)
        # minr, minc, maxr, maxc = region.bbox
        # rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,fill=False, edgecolor='red', linewidth=2)
        # ax.add_patch(rect)
        # plt.show()
            
        if region.area >= 200 and region.solidity > 0.8:
            #print('shadow_detected',region.area,region.solidity)
            
            #shadow_detected = True
            #return shadow_detected
            return True
        else:
            #print('shadow not detected',region.area,region.solidity)
            #shadow_detected = False
            #return shadow_detected            
            return False
    return False        
    
def getPrimitives(lbl_a,lbl_sh,df_slice,ymin=150,ymax=475):
    df_slice['shadow'] = getShadowStatus2(lbl_sh)
    for region in sorted(regionprops(lbl_a), key=lambda r: abs(r.centroid[0]-(ymax+ymin)/2), reverse=True):
        if region.centroid[0] > ymin and region.centroid[0] < ymax:
            #if region.area > 2650 and region.solidity > 0.8:
            y0, x0 = region.centroid
            minr, minc, maxr, maxc = region.bbox
            
            df_slice['xc'] = x0
            df_slice['yc'] = y0
            df_slice['minr'] = minr
            df_slice['maxr'] = maxr
            df_slice['maj-ax'] = region.major_axis_length
            df_slice['min-ax'] = region.minor_axis_length
            df_slice['orientation'] = region.orientation
            break
            #print(df_slice['orientation'])
            
    return df_slice    

#click event function
def selectPoint(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(x,",",y)
        global points
        
        points.append([x,y])
        font = cv2.FONT_HERSHEY_SIMPLEX
        strXY = str(x)+", "+str(y)
        #cv2.putText(img, strXY, (x,y), font, 0.5, (255,255,0), 2)
        #cv2.imshow("image", img)
    
def getTransformParams(points,arena_size,a_dict):
    
    xa = a_dict['xmin']
    ya = a_dict['ymin']
    
    #correct for perspective distortion
    pts = {
    'back left'     : points[0],
    'back right'    : points[1],
    'front right'   : points[2],
    'front left'    : points[3],
    }
    
    for pt in pts:
        x,y = pts[pt]
        pts[pt][0] = pts[pt][0] - xa
        pts[pt][1] = pts[pt][1] - ya
    
    xform = {
    'x0'        : ( (pts['front right'][0] + pts['front left'][0])/2 + (pts['back right'][0] + pts['back left'][0])/2 )/2,
    'ymin'      : (pts['back left'][1] + pts['back right'][1])/2,
    'y0_max'    : ( (pts['front left'][1] - pts['back left'][1]) + (pts['front right'][1] - pts['back right'][1]) )/2,
    'mx1'       : arena_size[0]/(pts['back right'][0] - pts['back left'][0]),
    'mx2'       : arena_size[0]/(pts['front right'][0] - pts['front left'][0]),
    'my'        : arena_size[1]/( ( (pts['front left'][1] - pts['back left'][1]) + (pts['front right'][1] - pts['back right'][1]) )/2 ),    
    }
    
    return pts, xform

# def getDerivatives(df_slice,xform):
    # x0 = xform['x0']
    # ymin = xform['ymin']
    # y0_max = xform['y0_max']
    # mx1 = xform['mx1']
    # mx2 = xform['mx2']
    # my = xform['my']

    # df_slice.at[-1,'x-corr'] = (df_slice['xc'].iloc[-1] - x0) * (mx2 + (mx1-mx2)*(y0_max-((df_slice['y-pos'].iloc[-1] - ymin)))/y0_max)
    # df_slice.at[-1,'y-corr'] = (df_slice['y-pos'].iloc[-1] - ymin) * my
    # df_slice.at[-1,'x-vel'] = df_slice['x-corr'].iloc[-1] - df_slice['x-corr'].iloc[0]
    # df_slice.at[-1,'y-vel'] = df_slice['y-corr'].iloc[-1] - df_slice['y-corr'].iloc[0]
    # df_slice.at[-1,'speed'] = math.sqrt( df_slice['x-vel'].iloc[-1]**2 + df_slice['y-vel'].iloc[-1]**2 )
    
    # print(df_slice.head())
    # return df_slice

    
    
    
    
    
    
    
    
    
    
    
    
    
    
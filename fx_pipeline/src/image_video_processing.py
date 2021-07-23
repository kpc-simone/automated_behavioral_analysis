# image/video processing
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from skimage.measure import label, regionprops, regionprops_table
from skimage.morphology import disk, dilation, closing, binary_erosion, binary_dilation, binary_closing
import numpy as np
import math
import cv2

points = []

def generateBackgroundModel(vidcap,roi,pos_0,FPS):
    pos_p = vidcap.get(cv2.CAP_PROP_POS_FRAMES)
    
    vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(pos_0*FPS))
    success,bg_frame = vidcap.read()
    prev_frame = np.float32(getROI(bg_frame,roi))
    wa = 0.01 * prev_frame
    wa_mov = prev_frame

    print('generating background model ...')
    while vidcap.isOpened():
        success,frame = vidcap.read()

        if frame is None:
            break
        
        frame = np.float32(getROI(frame,roi))
        change = np.absolute(frame - wa_mov)
        
        weighting_factor = 0.05 * ( change.sum().sum().sum() / ( roi['width'] * roi['height'] * 765) )
        cv2.accumulateWeighted(frame,wa,alpha = weighting_factor)
        cv2.accumulateWeighted(frame,wa_mov,alpha = weighting_factor )
        diff = wa_mov - wa
        diff_metric = diff.mean().mean().mean()
        
        if abs(diff_metric) < 5.0:
            bg_frame = wa
            model_built = True
            
            t_built = vidcap.get(cv2.CAP_PROP_POS_MSEC)/1000
            print('built background model in {} s of video'.format(t_built-pos_0))
            
            # fig, ax = plt.subplots(1,1)
            # ax.imshow(cv2.convertScaleAbs(bg_frame))
            # ax.set_title('Background model generated:')
            # ax.set_axis_off()
            # plt.show(block=False)
            
            break
    vidcap.set(cv2.CAP_PROP_POS_FRAMES,int(pos_p*FPS))
    return bg_frame        

def getMethodParams(seg_method,config,bg_frame=None):
    if seg_method == 'ADLR':
        thresh_dict['animal'] = config.settings['topview_thresh_level']
        adaptive_level = 4
        blocksize = 121
        
        bg_frame = getROI(bg_frame,roi)
        data_bg_z = getZero(bg_frame,method='coarse-blur')
        ref_frame = bg_frame
        data_ref_z = data_bg_z

        # TODO: make a function for this
        bg_gray = cv2.cvtColor(bg_frame, cv2.COLOR_BGR2HLS)
        bg_gray = bg_gray[:,:,1]
        bg_blur = cv2.blur(bg_gray,(6,6))
        mask1_b = cv2.adaptiveThreshold(np.uint8(bg_blur),1,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,blocksize,adaptive_level)

        # DLR algorithm step -4: compute reference diff and reference intensity
        ref_diff = getDiff(data_ref_z,data_bg_z)
        ref_int1 = ref_diff[:200,:20].mean(axis=0).mean(axis=0).mean(axis=0)
        ref_int2 = ref_diff[:200,-20:].mean(axis=0).mean(axis=0).mean(axis=0)
        ref_int = (ref_int1+ref_int2)/2

        # DLR algorithm step -3: specify structuring elements for morphological filtering operations
        selem = disk(11)
        selem1 = disk(11)

        # DLR algorithm step -2: specify dynamic mask 
        mask0 = np.zeros( (roi['height'],roi['width']) ,dtype='uint8')
        data_bgz_gray = cv2.cvtColor(data_bg_z,cv2.COLOR_BGR2HLS)
        data_bgz_gray = data_bgz_gray[:,:,1] # extract luminance channel
        #data_bgz_gray = flood_fill(data_bgz_gray,(350,400),255,tolerance=12)               # potential future use
        ret,mask0 = cv2.threshold(data_bgz_gray,15,1,cv2.THRESH_BINARY_INV)
        mask0 = binary_closing(mask0,selem)

    elif seg_method == 'BSAT':
        k = 7
        inv_offset = 255
        #at_level = config.settings['topview_thresh_level']
        at_blocksize = config.settings['topview_thresh_blocksize']
        selem_e = disk(3)
        selem_d = disk(5)
        
        bg_blur = cv2.blur(cv2.cvtColor(bg_frame, cv2.COLOR_BGR2GRAY),(k,k)).astype(np.float32)
        
        method_args = {
        
            'k'             : k,
            'inv_offset'    : inv_offset,
            #'at_level'      : at_level,
            'at_blocksize'  : at_blocksize,
            'bg_blur'       : bg_blur,
            'selem_e'       : selem_e,
            'selem_d'       : selem_d,
        
        }
        
    elif seg_method == '3CAT':
        k = 7
        at_level = 0
        at_blocksize = 81
        bg_blur = cv2.blur(bg_frame,(7,7)).astype(np.float64)
        selem_e = disk(5)
        selem_d = disk(7)
        
        method_args = {
        
            'k'             : k,
            'at_level'      : at_level,
            'at_blocksize'  : at_blocksize,
            'bg_blur'       : bg_blur,
            'selem_e'       : selem_e,
            'selem_d'       : selem_d,
        
        }
    
    return method_args
    

def getROI(frame,roi):
    
    xmin = roi['xmin']
    ymin = roi['ymin']
    width = roi['width']
    height = roi['height']
    
    roi = frame[ymin:ymin+height,xmin:xmin+width]
    
    return roi

def subGradients(frame, method = 'coarse-blur', k = 161):
    if method == 'coarse-blur':
        blur = cv2.blur(frame,(k,k))
        frz = np.absolute(frame - blur)
        return frz


def getZero(frame, method = 'mean', k = None):
    if method == 'mean':    
        mean = frame.mean(axis=0).mean(axis=0)
        frz = frame - mean - 1
        frz = frz.astype(np.uint8)
        return frz
        
    elif method == 'coarse-blur':
        blur = cv2.blur(frame,(k,k))
        frz = frame - blur
        return frz
        
    else:   
        pass

def getDiff(frz,bgz):
    diff = frz - bgz
    return diff
    
def getCCZT(diff,selem,mask0,mask1,ref_int):
    k = 27
    
    # DLR Algorithm step 4: compute intensity of naturally-fluctuating high-intensity spots
    int1 = diff[:200,:20].mean(axis=0).mean(axis=0).mean(axis=0)
    int2 = diff[:200,-20:].mean(axis=0).mean(axis=0).mean(axis=0)
    int = (int1+int2)/2
    
    # DLR Algorithm step 5: generate weighted mask
    mask = np.ones(diff.shape[:2],dtype='uint8')
    weight = (np.absolute(ref_int - int)) / 255

    weighted_mask0 = mask0 * weight
    weighted_mask1 = mask1
    weighted_mask = 0.3*mask - 0.3*weighted_mask0 + 0.7*weighted_mask1
    
    # DLR algorithm step 6: scale difference matrix by weighted mask
    diff[:,:,0] = diff[:,:,0] * weighted_mask
    diff[:,:,1] = diff[:,:,1] * weighted_mask
    diff[:,:,2] = diff[:,:,2] * weighted_mask
    
    # DLR algorithm step 7: compute matrices for color channel mean (ccm) color channel noise (ccn), and a z-like metric (ccz)
    ccm = cv2.blur(diff,(k,k)).mean(axis=2)
    ccn = cv2.blur(diff,(k,k)).std(axis=2)
    ccz = ccm - ccn
    
    # DLR algorithm step 8: compute threshold ccz matrix
    level = ccz.max(axis=0).max(axis=0)*0.51
    ret, cczt = cv2.threshold(ccz,level,255,cv2.THRESH_BINARY_INV)
    
    return ccz, cczt, weighted_mask

def selectROIs(frame,xa,ya):
	
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

    return nest_corners

# TODO: figure out how kwargs work
def thresholdImage(method='BSAT',method_args=None):

    if method == 'BSAT':
        bg_blur = method_args['bg_blur']
        fr = method_args['fr']
        k = method_args['k']
        diff = method_args['diff']

        #at_level = method_args['at_level']
        at_blocksize = method_args['at_blocksize'] 
        selem_e = method_args['selem_e'] 
        selem_d = method_args['selem_d'] 
        
        #at2 = method_args['at2']
        #at  = method_args['at']
        #inv_offset = method_args['inv_offset']
        
        frame_blur = cv2.blur(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY),(k,k)).astype(np.float64)
        diff = (bg_blur - frame_blur) / bg_blur
        diff = np.absolute( ( ( diff - diff.mean().mean() ) / ( diff.max().max() - diff.mean().mean() ) ) * 255 )
        diff = subGradients(diff)
        #diff = getZero(diff, method = 'coarse-blur', k = int(at_blocksize/2))
        
        hist = cv2.calcHist([np.uint8(diff)],[0],None,[256],[0,256])
        hist_norm = hist.ravel()/hist.sum()
        Q = hist_norm.cumsum()
        bins = np.arange(256)
        fn_min = np.inf                         # assume arbitrarily high number initially
        otsu_level = 63
        for i in range(63,127):
            p1,p2 = np.hsplit(hist_norm,[i])    # probabilities
            q1,q2 = Q[i],Q[255]-Q[i]            # cum sum of classes
            if q1 < 1.e-6 or q2 < 1.e-6:
                continue
            b1,b2 = np.hsplit(bins,[i]) # weights
            # finding means and variances
            m1,m2 = np.sum(p1*b1)/q1, np.sum(p2*b2)/q2
            v1,v2 = np.sum(((b1-m1)**2)*p1)/q1,np.sum(((b2-m2)**2)*p2)/q2
            # calculates the minimization function
            fn = v1*q1 + v2*q2
            if fn < fn_min:
                fn_min = fn
                otsu_level = i
        
        ret,result = cv2.threshold(np.uint8(diff),otsu_level,255,cv2.THRESH_BINARY)        
        at = 255 - cv2.adaptiveThreshold(255-np.uint8(diff),255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,at_blocksize,otsu_level)
        at = binary_erosion(at,selem_e)
        lbl = label(at,background=0)
        
        regions = [region for region in sorted(regionprops(lbl), key=lambda r: r.area, reverse=True)]
        labels_to_discard = []
        tol = 100
        
        if len(regions) > 0:
            labels_to_merge = [regions[0].label]
            for region in regions:
                #print(region.label,region.centroid,region.area)
                
                if (np.linalg.norm(np.asarray(region.centroid)-regions[0].centroid) < tol):
                    labels_to_merge.append(region.label) 
                    
                    # TODO: perform some nonlinear scaling on confidence (e.g. sigmoidal function)
                    # TODO: include distance between pos_-1, and pos_0 as a factor in computing confidence
            confidence = regions[0].area / len(regions)                
        else:
            labels_to_merge = []
            confidence = 0.0  
        labels_to_discard = [label for label in range(1, lbl.max()+1) if label not in labels_to_merge]
        #print('labels to merge: {}, discard: {}'.format(labels_to_merge,labels_to_discard))

       # selem = disk(6)
        lbl = merge_labels(lbl,labels_to_discard,0)
        lbl = merge_labels(lbl,labels_to_merge,1)
        
        return lbl,at,confidence

    elif method == '3CAT':
        bg_blur = method_args['bg_blur']
        fr_blur = method_args['fr_blur']
        at_level = method_args['at_level']
        at_blocksize = method_args['at_blocksize'] 
        selem_e = method_args['selem_e'] 
        selem_d = method_args['selem_d'] 
        
        diff = np.zeros_like(bg_blur).astype(np.float64)
        at1 = np.zeros_like(bg_blur).astype(np.float64)
        at2 = np.zeros_like(bg_blur).astype(np.float64)
        #at = np.zeros_like(bg_blur).astype(np.uint8)
        
        #print(bg_blur.dtype,fr_blur.dtype,diff.dtype,at1.dtype,at2.dtype)
        for c in range(0,3):
            diff[:,:,c] = (bg_blur[:,:,c] - fr_blur[:,:,c]) / bg_blur[:,:,c]
            diff[:,:,c] = ( ( diff[:,:,c] - diff[:,:,c].min().min() ) / ( diff[:,:,c].max().max() - diff[:,:,c].min().min() ) ) * 255
            
            at1[:,:,c] = binary_erosion(cv2.adaptiveThreshold(np.uint8(diff[:,:,c]),1,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,at_blocksize,at_level),selem_e)
            at2[:,:,c] = binary_dilation(cv2.adaptiveThreshold(np.uint8(255-diff[:,:,c]),1,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,at_blocksize,at_level),selem_d)

        at1_mask = cv2.bitwise_and(cv2.bitwise_and(at1[:,:,0],at1[:,:,1]),at1[:,:,2])
        at2_mask = cv2.bitwise_and(cv2.bitwise_and(at2[:,:,0],at2[:,:,1]),at2[:,:,2])
        at = at1_mask - at2_mask
        at = at > 0    
        lbl = label(at,background=0)
        #print(bg_blur.dtype,fr_blur.dtype,diff.dtype,at1.dtype,at2.dtype,at.dtype,lbl.dtype)
        
        regions = [region for region in sorted(regionprops(lbl), key=lambda r: r.area, reverse=True)]
        centroid_r0 = regions[0].centroid
        labels_to_merge = []
        labels_to_discard = []
        tol = 500
        if regions[0].area > 500:
            for region in regions:
                #print(region.label,region.centroid,region.area)
                
                if (np.linalg.norm(np.asarray(region.centroid)-centroid_r0) < tol):
                    labels_to_merge.append(region.label) 
                    
                    # TODO: perform some nonlinear scaling on confidence (e.g. sigmoidal function)
                    # TODO: include distance between pos_-1, and pos_0 as a factor in computing confidence
                    confidence = regions[0].area / len(regions)                
                else:
                    confidence = 0.0  
        else:
            confidence = 0.0 
        labels_to_discard = [label for label in range(1, lbl.max()+1) if label not in labels_to_merge]
        #print('labels to merge: {}, discard: {}'.format(labels_to_merge,labels_to_discard))

       # selem = disk(6)
        lbl = merge_labels(lbl,labels_to_discard,0)
        lbl = merge_labels(lbl,labels_to_merge,1)
        
        # fig,axt = plt.subplots(1,1)
        # axt.imshow(lbl)
        # plt.show(block=False)
        # #plt.show()
        # plt.pause(50)
        # plt.close()
        
        return lbl,at,confidence

    elif method == 'ADLR':
    
        # ADLR Algorithm step 1: remove gradients in intensity within the ROI
        roi_z = getZero(roi,method='coarse-blur')
        
        # ADLR Algorithm step 2: compute the difference between current frame (zero'd ROI) vs. background frame (zero'd ROI)
        roi_diff = getDiff(roi_z,bgz_roi)
        
        # ADLR algorithm step 3: compute adaptive threshold
        #ret,mask1 = cv2.threshold(blur,level,1,cv2.THRESH_BINARY_INV) 
        mask1 = cv2.adaptiveThreshold(blur,1,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,blocksize,level) - mask1_b
        
        # ADLR algorithm steps 4 - 8
        roi_ccz, thresh, weighted_mask = getCCZT(roi_diff,selem,mask0,mask1,ref_int)
        
        # ADLR Algorithm step 9: Segment and label thresholded image
        lbl,num = label(thresh,background=255,return_num=True)
        # print(num)
        
        # fig,axt = plt.subplots(1,1)
        # axt.imshow(lbl)
        # plt.show(block=False)
        # plt.pause(0.5)
        # plt.close()
        
        # DLR Algorithm step 10 Identify key regions to merge, regions to discard, and assign a confidence metric
        regions = [region for region in sorted(regionprops(lbl), key=lambda r: r.area, reverse=True)]
        centroid_r0 = regions[0].centroid
        labels_to_merge = []
        labels_to_discard = []
        tol = 1000*(1+y_corr/500)
        for region in regions:
            #print(region.label,region.centroid,region.area)
            
            if (np.linalg.norm(np.asarray(region.centroid)-centroid_r0) < tol):
                labels_to_merge.append(region.label) 
                
                # TODO: perform some nonlinear scaling on confidence (e.g. sigmoidal function)
                # TODO: include distance between pos_-1, and pos_0 as a factor in computing confidence
                confidence = regions[0].area / len(regions)                
            else:
                confidence = 0.0  
       
        labels_to_discard = [label for label in range(1, lbl.max()+1) if label not in labels_to_merge]
        #print('labels to merge: {}, discard: {}'.format(labels_to_merge,labels_to_discard))

       # selem = disk(6)
        lbl = merge_labels(lbl,labels_to_discard,0)
        lbl = merge_labels(lbl,labels_to_merge,1)
          
    elif method == 'DLR':
    
        # DLR Algorithm step 1: remove gradients in intensity within the ROI
        roi_z = getZero(roi,method='coarse-blur')
        
        # DLR Algorithm step 2: compute the difference between current frame (zero'd ROI) vs. background frame (zero'd ROI)
        roi_diff = getDiff(roi_z,bgz_roi)
        
        # DLR algorithm step 3: compute simple threshold
        
        ret,mask1 = cv2.threshold(blur,level,1,cv2.THRESH_BINARY_INV) 
        
        # DLR algorithm steps 4 - 8
        roi_ccz, thresh, weighted_mask = getCCZT(roi_diff,selem,mask0,mask1,ref_int)
        
        # DLR Algorithm step 9: Segment and label thresholded image
        lbl,num = label(thresh,background=255,return_num=True)
        
        # fig,axt = plt.subplots(1,1)
        # axt.imshow(lbl)
        # plt.show(block=False)
        # plt.pause(0.5)
        # plt.close()
        
        # DLR Algorithm step 10 Identify key regions to merge, regions to discard, and assign a confidence metric
        regions = [region for region in sorted(regionprops(lbl), key=lambda r: r.area, reverse=True)]
        
        centroid_r0 = regions[0].centroid
        labels_to_merge = []
        labels_to_discard = []
        tol = 1000*(1+y_corr/500)
        for region in regions:
            #print(region.label,region.centroid,region.area)
            
            if (np.linalg.norm(np.asarray(region.centroid)-centroid_r0) < tol):
                labels_to_merge.append(region.label) 
                
                # TODO: perform some nonlinear scaling on confidence (e.g. sigmoidal function)
                # TODO: include distance between pos_-1, and pos_0 as a factor in computing confidence
                #confidence = regions[0].area / len(regions)                
            #else:
                #confidence = 0.0

        labels_to_discard = [label for label in range(1, lbl.max()+1) if label not in labels_to_merge]
        #print('labels to merge: {}, discard: {}'.format(labels_to_merge,labels_to_discard))

       # selem = disk(6)
        lbl = merge_labels(lbl,labels_to_discard,0)
        lbl = merge_labels(lbl,labels_to_merge,1)
    
    elif method == 'adaptive':
        thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,151,2)
        lbl = label(thresh,background=255)
        #confidence = 50
        
    elif method == 'dynamic':
        equ = cv2.equalizeHist(blur)
        ns, bins, = np.histogram(equ.ravel(), bins=511)
        sum_ns = np.cumsum(ns)
        counts_thresh = ((10000-3600)*(y_corr/500)+3600)
        for bin,sum_n in zip(bins[:-1],sum_ns):
            if sum_n > counts_thresh:
                level = bin
                #print('updated threshold: {}, difference: {}'.format(level, sum_n - counts_thresh))
                break
        ret,thresh = cv2.threshold(equ,level,255,cv2.THRESH_BINARY)
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
        #confidence = 50
        
        #print(lbl.max())

        # figt,axt = plt.subplots(1,1)
        # axt.imshow(lbl)
        # plt.show(block=False)
        # plt.pause(0.5)
        # plt.close()
    #elif double_masked:    
        
    elif method == 'simple':    
        roi = method_args['roi']
        level = method_args['level']
        
        gray = cv2.cvtColor(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB), cv2.COLOR_BGR2GRAY)
        blur = cv2.blur(gray,(6,6))
        ret,thresh = cv2.threshold(blur,level,255,cv2.THRESH_BINARY) 
        lbl,num = label(thresh,background=255,return_num=True)
        confidence = 50
    
        return lbl,thresh,level,confidence

def merge_labels(labels_image,labels_to_merge,label_after_merge):
    labels_map = np.arange(np.max(labels_image)+1)
    labels_map[labels_to_merge] = label_after_merge
    return labels_map[labels_image]
	
def getShadowStatus(lbl_sh):
    #print('checking shadow')
    for region in sorted(regionprops(lbl_sh), key=lambda r: r.area, reverse=True):
        # print(region.area)
        # fig,ax = plt.subplots(1,1)
        # ax.imshow(lbl_sh)
        # minr, minc, maxr, maxc = region.bbox
        # rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,fill=False, edgecolor='red', linewidth=2)
        # ax.add_patch(rect)
        # plt.show()
        
        if region.area >= 200 and region.solidity > 0.8:
            #print('shadow detected')
            shadow_detected = True
            return shadow_detected
        else:
            shadow_detected = False
            return shadow_detected
    shadow_detected = False
    return False   

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
    
def getPrimitives(lbl_a,df_slice,confidence,ymin=150,ymax=475,interval_type='other',lbl_sh=None,shadow_period_exact=None,relative_time = None):
    if interval_type == 'other':
        df_slice['shadow'] = False
    if interval_type == 'trials-userdefined':
        if relative_time > shadow_period_exact[0] and relative_time < shadow_period_exact[1]:
            df_slice['shadow'] = True
        else:
            df_slice['shadow'] = False
    elif interval_type == 'trials-automatic':
        shadow_detected = getShadowStatus(lbl_sh)
        if shadow_detected:
            df_slice['shadow'] = True
        else:    
            df_slice['shadow'] = False
        
    df_slice['confidence'] = confidence
    #for region in sorted(regionprops(lbl_a), key=lambda r: abs(r.centroid[0]-(ymax+ymin)/2), reverse=True):
    for region in regionprops(lbl_a):
        #if region.centroid[0] > ymin and region.centroid[0] < ymax:
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
    
    #print(points)
    
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

    
    
    
    
    
    
    
    
    
    
    
    
    
    
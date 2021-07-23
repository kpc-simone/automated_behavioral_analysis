# get_behaviors
def getRear(maj_ax,min_ax,r_thresh,orientation,o_thresh):
    if (maj_ax/min_ax > r_thresh) and (abs(orientation) < o_thresh):
        return 1.0, True
    else:
        return 0.0, False

def getFreeze(vel, vel_0, vel_00, vel_000,f_thresh, rear):
    if rear:
        return 0.0
    else:
        if (vel < f_thresh) and (vel_0 < f_thresh) and (vel_00 < f_thresh) and (vel_000 < f_thresh):
            return 1.0
        else:
            return 0.0    

def getEscape(shadow_detected,vel,v_thresh1,v_thresh2,escape,hide,rear):
    if shadow_detected:
        if hide or rear:
            return 0.0,False
        else:
            if escape:
                if (vel < v_thresh2):
                    return 0.0,False
                else:
                    #print('case1')
                    return 1.0,True
            else:
                if (vel > v_thresh1):
                    #print('case2')
                    return 1.0,True
                else:
                    return 0.0,False
    else:
        return 0.0,False
            

def getHide(x,y,nest_corners):
    xmin = nest_corners['xmin']
    width = nest_corners['width']
    ymin = nest_corners['ymin']
    height = nest_corners['height']
    if (x > xmin) and (y > ymin) and (x < xmin + width) and (y < ymin + height):
        return 1.0, True
    else:
        return 0.0, False
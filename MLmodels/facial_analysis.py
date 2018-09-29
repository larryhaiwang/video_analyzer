# In[]:
##################################################
## Set up environment and load facial recognition model
##################################################

import os
import dlib
import cv2
import numpy as np
from scipy.spatial import distance as dist
# import plotly
import matplotlib.pyplot as plt
import time


# give path to the trained shape predictor model: shape_predictor_68_face_landmarks.dat
#####  Download model from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
#####  Note that the license for the iBUG 300-W dataset excludes commercial use.
#####  So you should contact Imperial College London to find out if it's OK for you to use this model file in a commercial product.
from django.conf import settings
predictor_path = settings.BASE_DIR + "/MLmodels/shape_predictor_68_face_landmarks.dat"

# load face detector from dlib - identifying all faces on an image
detector = dlib.get_frontal_face_detector()
# load share predictor - identifying position 64 trackers on face
#####  see tracker index here: https://www.pyimagesearch.com/2017/04/10/detect-eyes-nose-lips-jaw-dlib-opencv-python/
predictor = dlib.shape_predictor(predictor_path)

# In[]:
##################################################
## Track the position of face and its details in a video
##################################################
''' 
Function face_68_tracker read a video file and return the coordinates of face positions for each frame.
Input:
    - video_path: full path of video for analysis.
    - verbose: a boolean with default value as False. If True, video with face trackers will be displayed.
    - allow_interupt: a boolean with default value as False. If True, video analysis can be interupted by press "q".
    - save_video: a boolean with default value as False. If True, then a copy of video with facial marks will be created.
    - save_path: Specify the full path (including filename and extension) to store the marked video. By default, the same directory of source video is used.
                Suffix '_marked' is added to the source video name. Video format is .mp4
Output:
    - summary: a dictionary that contains meta data of the video:
        * total_frame: number of frames in total
        * processed_frame: number of frames that have been processed
        * fps: frame per second   
        * width: width of the frame
        * height: height of the frame
        * interupt: whether the processing has been interupted
    - face_tracker: a dictionary that contains face details:
        * start_times: a list of the start time for each frame
        * head_positions: a list of dlib.rectangle object with (left, top, right, bottom) cordinate of the face for each frame
        * tracker_shapes: a list of dlib.full_object_detection object with 68 tracker postions of the face for each frame
        * tracker_coords: Each value in the list corresponds to a frame. The value is a list of tuples that covers the x-y coordinates of all trackers
    - errors: a list of errors generated during analysis
'''
def face_68_tracker(video_path, verbose=True, allow_interupt=False, save_video=False, save_path=None):
    
    t_start = time.time()
    if verbose:
        print("")
        print("Start processing video: %s" % video_path)
        print("...")
    
    # initialize output
    summary = {}
    face_tracker = {'start_times':[], 'head_positions':[], 'tracker_shapes':[],'tracker_coords':[]}
    errors = []
    interupt = False
    
    # capture the video for analysis
    cap = cv2.VideoCapture(video_path)
    
    # store the meta data of the video
    if(cap.isOpened()):
        total_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps= float(cap.get(cv2.CAP_PROP_FPS))
        width= int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height= int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    else:
        # return error message
        errors.append("Analysis failed. Video file cannot be accessed: %s" % video_path)
        return summary, face_tracker, errors
    
    # create a videoWriter if save value is true
    if save_video:
        if save_path is None:
            # split video path and file name
            source_path, source_name = os.path.split(video_path)
            # split source_name into video name and extension
            video_name, video_extension = os.path.splitext(source_name)
            # full path of saved video
            save_path = source_path + '/' + video_name + "_marked.mp4"
        else:
            # create directory for save_path
            save_dir, save_name = os.path.split(save_path)
            # makedirs() allows making multi-level directory
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
        # save video
        # MP4V for mp4; XVID for avi
#        fourcc = cv2.VideoWriter_fourcc(*'MP4V')
#        out = cv2.VideoWriter(save_path, fourcc, fps, (width,height))
        out = cv2.VideoWriter(save_path, 0x00000021, fps, (width,height))
    
    # initialize frame counter 
    f_count = 0
    
    while(cap.isOpened()):
        # initialize values
        pos = None
        shape = None
     
        # read each frame
        check, source_frame = cap.read() # frame is in BGR 
        if check:
            # make a copy of source_frame
            frame = source_frame
            
            # calculate frame start_time
            start_time = f_count / fps
            f_count += 1
                   
            # detect face area in the frame. the second parameter specifies number of times for upsampling. this will enlarge the frame to detect more faces
            dets = detector(frame, 0)
            
            # throw an error message when more than one face is dected.
            if len(dets) == 1:
                # detect facial trackers
                pos = dets[0]
                shape = predictor(frame, pos)
                
                # convert coordinates of tacker into tuple
                points=[]
                for i in range(68):
                    points.append((shape.part(i).x, shape.part(i).y))
                
            elif len(dets) == 0:
                pass

            else:
                raise Exception("More than one face is dected in video.")
            
            # store face trackers
            face_tracker['start_times'].append(start_time)
            face_tracker['head_positions'].append(pos)
            face_tracker['tracker_shapes'].append(shape)
            face_tracker['tracker_coords'].append(points)
            
            # display and save frame based on parameter
            if verbose or save_video:       
                # draw facial position on frame; color is BGR
                frame = draw_dets(frame, pos, color=(255,255,0), pt=2)            
                # draw facial tracker on frame
                frame = draw_shape(frame, shape, color=(255,0,0))
                
            if verbose:
                # display video
                cv2.imshow(video_path, frame)
                
            if save_video:
                # save video
                out.write(frame)
                
            # if interuption is allowed, then press 'q' to exit.
            if allow_interupt:
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    interupt = True
                    break
        else:
            break
    
    # Release everything if job is finished
    cap.release()
    if save_video:
        out.release()
    cv2.destroyAllWindows()
    
    # store output
    summary['total_frame'] = total_frame
    summary['processed_frame'] = f_count
    summary['fps'] = fps
    summary['width'] = width
    summary['height'] = height
    summary['interupt'] = interupt
    
    # print processing time
    t_end = time.time()
    if verbose:
        print("Process Completed")
        print("Total frames: %d; Length: %.2fs" % (total_frame, total_frame/fps))
        print("Processing time: %.2fs" % (t_end-t_start))
    
    return summary, face_tracker, errors

# In[]:
##################################################
## Use OpenCV to draw facial position and details on frame image
##################################################
'''
Function draw_dets draws a rectangle around the face in the frame image
Input:
    - img: targe frame image
    - dets: dlib.rectangle object for the target frame
    - color: BGR color of the rectangle
    - pt: thickness of line
Output:
    - out_img: post processed frame image
'''
def draw_dets(img, dets, color=(0,0,0), pt=1): # color is in BGR order
    out_img = img
    
    # return original image if dets is None
    if dets == None:
        return out_img
    
    # identify top-left and bottom-right corner of rectangle
    left_top = (dets.left(), dets.top())
    right_bottom = (dets.right(), dets.bottom())
    
    # add rectangle to image
    out_img = cv2.rectangle(img, left_top, right_bottom, color, pt)
    
    return out_img

'''
Function draw_shape draws the outline of face details on frame
Input:
    - img: targe frame image
    - shape: dlib.full_object_detection object for the target frame
    - color: BGR color of the rectangle
    - pt: thickness of line
Output:
    - out_img: post processed frame
'''
def draw_shape(img, shape, color=(0,0,0), pt=1):
    out_img = img
    
    # return original image if shape is None
    if shape == None:
        return out_img
    
    points=[]
    for i in range(68):
        # convert shape.part to tuple cordination
        points.append((shape.part(i).x, shape.part(i).y))
        
        # connect trackers in sequence
        if i in [0,17,22,27,36,42,48,60]:
            pass
        else:
            out_img = cv2.line(out_img, points[i-1], points[i], color, pt)

    # connect additional trackers that are not consecutive
    out_img = cv2.line(out_img, points[35], points[30], color, pt)
    out_img = cv2.line(out_img, points[41], points[36], color, pt)
    out_img = cv2.line(out_img, points[47], points[42], color, pt)
    out_img = cv2.line(out_img, points[59], points[48], color, pt)
    out_img = cv2.line(out_img, points[67], points[60], color, pt)

    return out_img

# In[]:
##################################################
##  Calculate eye_aspect_ratio for each frame, and accumulative counts of blink
##################################################

'''
Function eye_ratio_calc calculates eye_aspect_ratio given the coordinates of facial details
Input:
    - tracker_coord: a list of x-y coordinates for the 68 facial trackers
    - method: a string that specifies the method to calculate eye aspect ratio. "both" returns the average ratio of both eyes. "left" or "right"
              returns the ratio of a single. Default value is "both".
Output:
    - eye_ratio: the calculated eye aspect ratio
'''
def eye_ratio_calc(tracker_coord, method='both'):
    
    if method not in ['both', 'left','right']:
        raise ValueError("Invalid calculation method: %s" % method)
    
    # eye aspect ratio for right eye
    right_eye_height = (dist.euclidean(tracker_coord[37], tracker_coord[41]) + dist.euclidean(tracker_coord[38], tracker_coord[40])) * 0.5
    right_eye_width = dist.euclidean(tracker_coord[36], tracker_coord[39])
    right_eye_ratio = right_eye_height / right_eye_width
    
    if method == 'right':
        eye_ratio = right_eye_ratio
        return eye_ratio
    
    # eye aspect ratio for left eye
    left_eye_height = (dist.euclidean(tracker_coord[43], tracker_coord[47]) + dist.euclidean(tracker_coord[44], tracker_coord[46])) * 0.5
    left_eye_width = dist.euclidean(tracker_coord[42], tracker_coord[45])
    left_eye_ratio = left_eye_height / left_eye_width
    
    if method == 'left':
        eye_ratio = left_eye_ratio
        return eye_ratio
    
    eye_ratio = (right_eye_ratio + left_eye_ratio) * 0.5
    return eye_ratio

'''
Function detect_blink calculates the eye aspect ratio and accumulative blinking count for each frame of a video. 
If a threshold is given to identify closed eyes, then it will be used across whole video. Otherwise, the function dynamically identifies a threshold within
an adjacent window of each frame.

Input:
    - video_summary: the output from face_68_tracker()
    - face_tracker: the output from face_68_tracker()
    - method: a string that specifies the method to calculate eye aspect ratio. "both" returns the average ratio of both eyes. "left" or "right"
              returns the ratio of a single. Default value is "both".
    - blink_param: a dictionary that contains four possible values. The default value is {}.
        * ratio_thresh: the minimum eye aspect ratio below which the eyes are considered closed. If this argument is provided, the threshold will be used
                        universially and the two auto threshold arguments are ignored
        * auto_thresh_win: for a given frame at time t, the frames within time (t-auto_thresh_win, t+auto_thresh_win) are used to calculate a proper threshold for that frame.
                        This argument is used only when ratio_thresh is not provided. For example, auto_thresh_win = 4 means a 8s window is used for each frame (4s before and after).
                        Default value is 0, which means a universal window (full length of video) is used regardless of frame time t. 
        * auto_thresh_qt: for a timespan specified by auto_thresh_win, auto_thresh_qt specifies the lower quantile of eye aspect ratio within that window.
                        this arguement is used when ratio_thresh is not provided. default value is 0.4
        * consec_frame: the minimum number of consecutive frames with closed eyes that is considered a blink. default value is 3 frames.
Output:
    - eye_aspect_ratio: a list that consists of the eye aspect ratio of each frame
    - blink_count: a list that consists of accumulative count of blinking. this value is returned only when blink_param is provided as input
    - errors: a list of errors generated during analysis
'''
def detect_blink(video_summary, face_tracker, method="both", blink_param={}):

    # initialize values
    coords = face_tracker['tracker_coords']
    frame_N = len(coords)
    eye_aspect_ratio = []
    blink_count = []
    errors = []

    # loop through all frames to calculate eye_aspect_ratio
    for f in range(frame_N):
        ear = eye_ratio_calc(coords[f], method)
        eye_aspect_ratio.append(ear)  

    # check whether the proper arguments are provided in blink_param for blink counting
    param = blink_param
    ratio_thresh = param.pop('ratio_thresh', None)
    consec_frame = param.pop('consec_frame', 3)
    
    if ratio_thresh == None:
        auto_thresh_qt = param.pop('auto_thresh_qt', 0.4) 
        auto_thresh_win = param.pop('auto_thresh_win', 0)
        
        # identify a global threshold if time window is not provided 
        if auto_thresh_win == 0:
            ear_max = np.partition(eye_aspect_ratio,-10)[-10] # retrieve the 10th largest eye aspect ratio, in order to avoid outliers in maximum
            ear_min = np.min(eye_aspect_ratio)
            ratio_thresh = ear_min + (ear_max-ear_min)  * auto_thresh_qt

    # check whether the proper arguments are provided in blink_param    
    if len(param)>0:
        errors.append('Warning: there are unused arguments in blink_param:\n', param)
#   if ratio_thresh == None and consec_frame == None:
#       raise ValueError('Required parameters is missing in blink_param:\n', blink_param)   

    # count number of blinks
    acc_count = 0 # accumulative count of blinks
    f_count = 0 # count of consecutive frames
    
    for f in range(frame_N):
        if eye_aspect_ratio[f] < ratio_thresh:
            f_count += 1 # add one consecutive frame count when eye aspect ratio is below threshold
        else:
            if f_count >= consec_frame: # count one blink when consecutive frame count reaches threshold
                acc_count += 1
            f_count = 0 # reset consecutive frame count when eye aspect ratio is above threshold
        blink_count.append(acc_count)

    # process is completed here if ratio_thresh is used.
    if ratio_thresh != None:
        return eye_aspect_ratio, blink_count, errors
    
    # now, calculate dynamic threshold within each time window
    # loop through all frames again to calculate blink_param dynamically
    adj_f = int(video_summary['fps'] * auto_thresh_win) # number of adjacent frames within adjacent time window

#    print("adj_f: ", adj_f)
#    print("ear_min: ", ear_min)
    
    for f in range(frame_N):
        # lower and upper bound of frame indeces
        lb = np.maximum(0, f-adj_f) 
        ub = np.minimum(frame_N-1, f+adj_f)
        adj_ear = eye_aspect_ratio[lb:ub]
        
        # calculate the quantile as threshold within adjacent time window
        ''' the calculation can be further optimized across iterations '''
        adj_ear_max = np.partition(adj_ear,-10)[-10] # retrieve the 10th largest eye aspect ratio, in order to avoid outliers in maximum
        adj_ear_min = np.min(adj_ear)
        adj_ratio_thresh = adj_ear_min + (adj_ear_max-adj_ear_min)  * auto_thresh_qt
        
#        if f % 30 ==0:
#            print("adj_ear_max: ", adj_ear_max)
#            print("adj_ratio_thresh: ", adj_ratio_thresh)
            
        # after setting the threshold within the time window, use the same process to count blinks
        if eye_aspect_ratio[f] < adj_ratio_thresh:
            f_count += 1 
        else:
            if f_count >= consec_frame:
                acc_count += 1
            f_count = 0
        blink_count.append(acc_count)
    
    return eye_aspect_ratio, blink_count, errors
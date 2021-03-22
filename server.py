#server for collection, processing and detecting frames
from imutils import build_montages   #---> buiild montage of all incoming frames
from datetime import datetime    
import numpy as np
import imagezmq     #---> for streaming video from clients
import argparse
import imutils
import cv2


#construct arg parse and parse arguments
ap= argparse.ArgumentParser()
ap.add_arguement('-p', '--protxt', required= True,
                 help= 'path to Caffe "deploy prototxt file')
ap.add_argument('-m', '--model', required= True,
                help= 'path to Caffe pre-trained model')
ap.add_argument('-c', '--confidence', type=float, default= 0.2,
                help= 'minimum probability to filter weak detections')
ap.add_argument('-mw', 'montageW', required= True, type= int,
                help= 'montage frame width')
ap.add_argument('-mH', '--montageH', required= True, type= int,
                help= 'montage frame height')
args= vars(ap.parse_args())


#initialize the imagehub object
#alllows our server to accept connections from each client
imagehub= image.amq.ImageHub()

#initialize the list of class labels that mobile net was trained on
#then generate a set of bounding box colors for each image
CLASSES= ['background', 'aeroplane', 'bike', 'bird', 'boat', 
          'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 'dining_table', 'dog',
          'horse', 'motorbike', 'person', 'plotted_plant', 'sheep',
          'soft', 'train', 'tvmonitor']

#load our serialized mdels from disk
print('[INFO] loading model....')
net= cv2.dnn.readNetFromCaffe(args['prototxt'], args['model'])


#initialize the classes we care about labeling in our model, the object count dictionary and frame dict.
CONDSIDER= set(['dog', 'person', 'car'])
objcount= {obj: 0 for obj in CONDSIDER}      #---> tracks the count of the object classes
frameDict= {}   #--> will contain hostname key and the associated latest frame value

#initialize dictionay which will contain information regarding
#when a device was last active, then store the last time the check
#was made was now
lastactive= {}
lastActiveCheck= datetime.now()

#stores the estimated number of clients, active checking period, and
#calculates the durations seconds to wait before making a chec to 
#see if a device was active
ESTIMATED_NUM_OF_CLIENTS= 4       #---> 4 for this example
ACTIVE_CHECK_PERIOD= 10           #10 seconds
ACTIVE_CHECK_SECONDS= ESTIMATED_NUM_OF_CLIENTS * ACTIVE_CHECK_PERIOD

#assing montage width and heigth so that we can view all incoming frames
#in a single dashboard
mW= args['montageW']
mh= args['montageH']
print('[INFO] detecting {}...'.format(", ".join(obj for obj in CONSIDER)))


#start looping over all of the frames
while True:
    #receive client name and frame from the client
    #and acknowledge the receipt
    (rpiName, frame)= imageHub.recv_image()
    imageHub.send_reply(b'Ok')
    
    #if the device is not in the last active dictionary
    #then it means that this is a newly activated device
    if rpiName not in lastActive.keys():
        print('[INFO] receiving data from {}....'.format(rpiName))
        
    #record the last activate time for the device from which we just
    #received from a frame
    lastActive(rpiName)= datetime.now()
    
    
#performing model infernece on the frame (Using openCV)
#resize the frame to have maximum of 400 pixles
frame= imutils.resize(frame, width= 400)
(h, w)= frame.shape[:2]
blob= cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
                            0.007843, (300, 300), 127.5)

#pass the blog through the network and obtain the detections and predictions
net.setInput(blob)
detections= net.forward()

#reset the object count for each object in the CONSIDER set
objcount= {obj for obj in CONSIDER}


#lets over the detections with the goal of
#counting, and drawing boxes around the objects that we are considering
for i in np.arange(0, detections.shape[2]):
    #extract the confidence/prob associated with the probablity of the predictions
    confidence= detections[0, 0, i, 2]
    
    #filter out weak detections by ensuring the confidence is 
    #greater than than minimum confidence
    if confidence > args['confidence']:
        #extract the index of the class label from the detections
        idx= int(detections[0, 0, i, 1])
        
        #check to see if the predicted class is in the set of classes
        if CLASSES[idx] in CONSIDER:
            #increment the count of the particular object detected in the frame
            objcount[CLASSES[idx]] += 1
            
            #compute the x,y coordinates of the bounding boxes for the object
            box= detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startx, starty, endx, endy)= box.astype('int')
            
            #draw the bounding box around the detectes object in the frame
            cv2.rectangle(frame, (startx, starty), (endx, endy),
                          (255, 0, 0), 2)
            
            
#lets now annotate each frame with the hostname and obj counts
#we will also build a montage to display them....
#draw the sending device name on the frame
cv2.putText(frame, rpiName, (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

#draw the object count on the frame
label= ", ".join("{}: {}".format(obj, count) for (obj, count) in (obj.count.items))
cv2.putText(frame, label, (10, h -20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255.0), 2)

#update the new frame in the frame dictionary
montages= build_montages(frameDict.values(), (w, h), (mw, mh))

#display the montages on the screen
for (i, montage) in enumerate(montages):
    cv2.imshow("Location monitor ({})".format(i), montage)
    
    #detect any keypresses
    key= cv2.waitkey(1) & 0xFF
    

#lets check the last active timestamps for each client feed and
#remove frames from the montage that have stalled
if (datetime.now()- lastActiveCheck).seconds > ACTIVE_CHECK_SECONDS:
    #loop over all previous active devices
    for (rpiName, ts) in list(lastActive.items()):
        #remove the client from the last active and frame
        #dictionaries if the device hasn't been active recently
        
        if (datetime.now() - ts).seconds > ACTIVE_CHECK_SECONDS:
            print('[INFO] lost connection to {}'.format(rpiName))
            lastActive.pop(rpiName)
            frameDict.pop(rpiName)
            
    
    #check the last active checkpoint time to the current time
    lastActiveCheck= datetime.now()

#if the "q" key was pressed, break the loop
if key== ord('q'):
    break

#do a bit of cleanup
cv2.destroyAllWindows()
    
    
#----------------------Command Line Steps/ Things -------------------#        
#make sure that you are
#now all we have to do is upload our client file to each of the cameras using SCP:
# scp client.py <applicable ip address for our network>: ~ (use Pyimage search blog for further info)
#their can be more or less ip addresses to configure

#we also need to ensure that we install Imagezmq on each device 

#before starting the client, we must start the server using the following code:
# python server.py --prototxt MobileNetSSD_deploy.prototxt \
    #-- model MobileNetSSD_deploy.caffemodel --montageW 2 --montageH 2
    
#*Once the server is running, start each client point to the server. 
#Below are the steps we need too take:
#Open ssh client (example): ssh p@192.168.1.10
#start screen on the clinent: screen
#source your profile: source~/profile
#Activate environment: workon py3cv4
#------------------- Finished--------------------------------#
 
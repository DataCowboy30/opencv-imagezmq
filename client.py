#import the nexessary packages
from imutils.video import VideoStream
import imagezmq
import argparse
import socket   #----> used to grab the hostname of the client device (raspberry pi in this example)
import time    #---> allows camera to warm up prio to sending frames

#construct the argument parser and parse the arguments
ap= argparse.ArgumentParser()
ap.add_argument("-s", "--server-ip", required= True, help= "ip address of the server to which the client will connect to")
args= vars(ap.parse_args())

#initialize the Imagesender object with the socket address of the server
#below is an example
sender= imagezmq.ImageSender(connect_to= "tcp://{}.5555".format(args['server_ip']))  #notice that we are importing imagezmq in our client side script


#get the hostname, intiliaze the video stream, and 
#allowd the camera sensor to warm up
rpiName= socket.gethostname()
vs= VideoStream(usePiCamera=True).start()     #----> where we set camera resolution (add argument "resolution = (320, 240)") etc to change res.
#vs= Video Stream(src0).start()   #---> using webcam
time.sleep(2.0)

#grab and send the frames
while True:
    #read the frame from the camera and send it to the server
    frame= vs.read()
    sender.send_image(rpiName, frame)    #---> sends frames to the server based on the particular client device
    
    
    


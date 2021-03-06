#!/usr/bin/env python
import rospy 
import numpy as np
import cv2
import os
import time
import math
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import TwistStamped
from mavros_msgs.msg import *
from mavros_msgs.srv import *
from std_msgs.msg import String,Float32

from cv_bridge import CvBridge
from sensor_msgs.msg import Image

global_height = 2
c = 0
area = 0
center_errorx = 0
center_errory = 0
np_obs = 0
np_obs_left = 0
np_obs_right = 0
std = 0
bridge = CvBridge()

aruco_detected = 0
aruco_point_flag = 0

pose = PoseStamped()

def posCb(msg):

    global global_height,pose
    pose = msg
    global_height = pose.pose.position.z
    print(global_height)
    """quaternion = [ msg.pose.orientation.x, msg.pose.orientation.y,
        msg.pose.orientation.z, msg.pose.orientation.w ]
    # transforming orientation from quaternion to euler
    euler = transformations.euler_from_quaternion(quaternion)
    #print(euler,"euler")

    # getting third element from 1D euler matrix
    yaw = euler[2] 
    print(yaw,"yaw")"""

def callback(data):

    global center_errorx, center_errory, np_obs, np_obs_left, np_obs_right,c,area, std

    cv_image = bridge.imgmsg_to_cv2(data, desired_encoding=data.encoding)    
    img_c = np.nan_to_num(cv_image) #Convert all nan to 0
    std = img_c.std()
    mask = (img_c>0)*1 #mask with 0 in place of nan
    img1 = 255-img_c*255/10 #scale to 0-255;255 in place of nan
    img1 = mask*img1 #removes the nan part and makes it 0
    img_wm = np.uint8(img1)
    img1 = img_wm[100:, :]
    img_left = img_c[:, 0:200]
    img_right = img_c[:, 440:640]
    np_obs_left = np.sum(img_left < 2)
    np_obs_right = np.sum(img_right < 2)   
    np_obs = np_obs_left + np_obs_right
    velocity = TwistStamped()
    
    ret,thresh = cv2.threshold(img1,110,255,cv2.THRESH_BINARY_INV)
    
    cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


    
    if cnts is not None :

        cnts = cnts[0] if len(cnts) == 2 else cnts[1]


        # find the biggest countour (c) by the area
        c = max(cnts, key = cv2.contourArea)

    	# Obtain bounding rectangle to get measurements
    	x,y,w,h = cv2.boundingRect(c)

   	    # Find centroid
    	M = cv2.moments(c)
    	cX = int(M["m10"] / M["m00"])
    	cY = int(M["m01"] / M["m00"])
        
        
        cv2.rectangle(img1,(x,y),(x+w,y+h),(255,0,0), 4)
        cv2.circle(img1, (cX, cY), 10, (320, 159, 22), -1)
        img1 = cv2.circle(img1, (320,240), radius=10, color=(0, 0, 255), thickness=-1)
        
        area = w*h
        k_p = 50
        
        cv2.imshow('output',img1)
        
        if cv2.waitKey(1) & 0xFF ==ord('q'):
            cv2.destroyAllWindows()

        center_errorx = (cX-320)
        center_errory = cY
       

    
"""def dead_end():
    global std
    velocity.twist.linear.z = 0.1
    print("adjusting height....................................................................")
    vel_aruco.publish(velocity)
    
    if(std > 1.4):
        velocity.twist.linear.z = 0.0
        vel_aruco.publish(velocity)"""
        
    
    
        


def adjust_yaw():
    global aruco_detected,pose,area,center_errorx, center_errory, np_obs, np_obs_left, np_obs_right, global_height,c, std
    center_precisionx = 60
    center_precisiony = 50
    if(aruco_detected == 0):
       flag = 0
       print(np_obs_left, np_obs_right)
       print(np_obs)
       print(std)
    
       while(std < 1.42):
           print("std",std)
           print("deaddddddddddddddddddddddddddddddddddddddddddddddddddddddddd")
           velocity.twist.linear.z = 0.1
           print("adjusting   height....................................................................")
           vel_aruco.publish(velocity)       
           if(std > 1.42):
               velocity.twist.linear.z = 0.0
               vel_aruco.publish(velocity)
               break

       if np_obs > 70000:

           if(np.abs(np_obs_left - np_obs_right) > 1000):
               # if present slide accordingly
               if(np_obs_left > np_obs_right):
                   velocity.twist.linear.y = -0.1
                   velocity.twist.linear.x = 0
                   vel_aruco.publish(velocity)
                
               else:
                   velocity.twist.linear.y = 0.1
                   velocity.twist.linear.x = 0
                   vel_aruco.publish(velocity)

           velocity.twist.angular.z = 0
           velocity.twist.linear.x = 0
           velocity.twist.linear.y = 0
           vel_aruco.publish(velocity)


       else:
           while(abs(center_errorx) >= center_precisionx):
               print("std",std) 
               if (center_errorx > 0):
                   flag = 1
                   velocity.twist.angular.z = -0.2
                   vel_aruco.publish(velocity)    
               elif (center_errorx < 0):
                   flag = 2
                   velocity.twist.angular.z = 0.2
                   vel_aruco.publish(velocity)

               #print("adjusting yaw")
               #print("rectangel_area = ",area)
               print(center_errorx)

               if(abs(center_errorx) < center_precisionx):
                   velocity.twist.angular.z = 0.0
                   vel_aruco.publish(velocity)
                   print("std",std)
                   break
           #print("yaw adjusted")
           velocity.twist.angular.z = 0.0
           vel_aruco.publish(velocity)
    
           while((0< center_errory < 150) and (230< center_errory <380)):
               print("std",std)
                    
               velocity.twist.linear.z = -0.2 if (center_errory > 0) else 0.2
               #print("adjusting height")
               #print(cY)
               vel_aruco.publish(velocity)

               if(100 < center_errory < 280):
                   velocity.twist.linear.z = 0.0
                   vel_aruco.publish(velocity)
                   break
           #print("height adjusted")
           velocity.twist.linear.z = 0.0
           vel_aruco.publish(velocity)

           t0 = rospy.Time.now().to_sec()
           while(1):
               print("std",std)
               t1 = rospy.Time.now().to_sec()
               velocity.twist.linear.x = 0.2
               vel_aruco.publish(velocity)
            
            
               if((t1-t0) > 5):
                   break
           velocity.twist.linear.x = 0.0
           vel_aruco.publish(velocity)
    else:
        global aruco_point_flag,pose,aruco_pose
        if aruco_point_flag == 0:
            print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
            aruco_pose = pose.pose.position
            aruco_point_flag = 1
        elif aruco_point_flag == 1:
            aruco_pose_publish = PoseStamped()
            aruco_pose_publish.pose.position.x = aruco_pose.x
            aruco_pose_publish.pose.position.y = aruco_pose.y
            aruco_pose_publish.pose.position.z = aruco_pose.z
            arucopoint.publish(aruco_pose_publish)
            print("yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy")
            aruco_point_flag = 2
        else:
            pass        
def arucodetectcallback(data):
    global aruco_detected
    aruco_detected = data.data   

def listener():
    rospy.init_node('hari_ohm_aruco', anonymous=True)
    global vel_aruco,arucopoint,global_height
    rospy.Subscriber('mavros/local_position/pose', PoseStamped, posCb)
    
    rospy.Subscriber("/depth_camera/depth/image_raw", Image, callback)
    vel_aruco = rospy.Publisher("/mavros/setpoint_velocity/cmd_vel", TwistStamped, queue_size = 10)
    arucopoint = rospy.Publisher("mavros/setpoint_position/local", PoseStamped, queue_size = 10)
    rospy.Subscriber("/aruco/detected", Float32,arucodetectcallback)
    
    while not rospy.is_shutdown():
        adjust_yaw()
    rospy.spin()

if __name__ == '__main__':
    velocity = TwistStamped()
    listener()

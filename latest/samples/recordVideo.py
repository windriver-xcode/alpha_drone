#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, cv2
from threading import Thread
from djitellopy import Tello

tello = Tello()

tello.connect()

keepRecording = True
tello.streamon()
frame_read = tello.get_frame_read()

FRAME_RATE = 30.0
def videoRecorder():
    #time.sleep(2)
    # create a VideoWrite object, recoring to ./video.avi
    height, width, _ = frame_read.frame.shape
    video = cv2.VideoWriter('video.avi', cv2.VideoWriter_fourcc(*'XVID'), FRAME_RATE,
                            (width, height))

    while keepRecording:
        video.write(frame_read.frame)
        #cv2.imshow('f', frame_read.frame)
        time.sleep(1 / FRAME_RATE)

    video.release()
    #cv2.destroyWindow('f')


# we need to run the recorder in a seperate thread, otherwise blocking options
#  would prevent frames from getting added to the video
recorder = Thread(target=videoRecorder)
recorder.start()

# tello.takeoff()
# tello.move_up(100)
# tello.rotate_counter_clockwise(360)
# tello.land()
time.sleep(5)
keepRecording = False
recorder.join()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import time
from djitellopy import Tello

tello = Tello()
tello.connect()

tello.streamon()
frame_read = tello.get_frame_read()

#tello.takeoff()
time.sleep(1)
cv2.imwrite("picture.png", frame_read.frame)

#tello.land()
tello.end()
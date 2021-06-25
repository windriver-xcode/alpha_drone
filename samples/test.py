import cv2
import time
from djitellopy import Tello

tello = Tello()
tello.connect()
tello.takeoff()
time.sleep(1)

#tello.streamon()


tello.send_rc_control(0, 0, 0, 0)
time.sleep(2)

tello.land()

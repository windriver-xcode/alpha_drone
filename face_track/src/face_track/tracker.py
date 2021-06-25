# -*- coding: utf-8 -*-

import datetime
import logging
import math
import os
import threading
import time

import cv2
import numpy as np
#from face_track.mockdjitellopy import Tello
from djitellopy import Tello

from face_track.pid import PID

# import mediapipe as mp


class FaceTracker(object):
    HANDLER = logging.StreamHandler()
    FORMATTER = logging.Formatter(
        '[%(levelname)s] %(filename)s - %(lineno)d - %(message)s')
    HANDLER.setFormatter(FORMATTER)

    LOGGER = logging.getLogger('alpha')
    LOGGER.addHandler(HANDLER)
    LOGGER.setLevel(logging.INFO)

    MAX_COMMAND_SEC: int = 100  # throttle control, max number of commands per second
    OVERRIDE_PERIOD: float = 0.1  # key press override period in seconds
    RECORD_FRAME_RATE: float = 10.0  # the video record frame rate per second

    cv2_base_dir = os.path.dirname(os.path.abspath(cv2.__file__))
    default_face = os.path.join(cv2_base_dir, "data",
                                "haarcascade_frontalface_default.xml")
    face_cascade = cv2.CascadeClassifier(default_face)
    if face_cascade.empty():
        LOGGER.warn(f"Error loading face cascade {default_face}")
        exit(0)

    default_eyes = os.path.join(cv2_base_dir, "data",
                                "haarcascade_eye_tree_eyeglasses.xml")
    eye_cascade = cv2.CascadeClassifier(default_eyes)
    if eye_cascade.empty():
        LOGGER.warn(f"Error loading eye cascade {default_eyes}")
        exit(0)

    # mp_face_detection = mp.solutions.face_detection
    # #mp_drawing = mp.solutions.drawing_utils
    # face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)

    #Tello.LOGGER.setLevel(logging.DEBUG)
    #PID.LOGGER.setLevel(logging.DEBUG)

    def __init__(self, w: int = 640, h: int = 480) -> None:
        """Initialize a FaceTracker instance
        :param w: the image width in pixel (x)
        :param h: the image height in pizel (y)
        :return: None
        """
        super().__init__()

        self.drone = FaceTracker.initTello()
        self.prev_time = time.time()
        self.w: int = w  # image width in pixel
        self.h: int = h  # image height in pixel

        # terms for forward and backward speed control
        self.fb_pid = PID('fb',
                          kP=0.5,
                          kI=0.01,
                          kD=0.1,
                          SP=math.sqrt(w * h / 12))
        # terms for up and down speed control
        self.ud_pid = PID('ud', kP=0.5, kI=0.01, kD=0.1, SP=h / 2)
        # terms for left and right speed control
        self.lr_pid = PID('lr', kP=-0.5, kI=-0.01, kD=-0.1, SP=w / 2)
        # terms for yaw speed control
        self.yaw_pid = PID('yaw', kP=-0.5, kI=-0.01, kD=-0.1, SP=w / 2)
        self.pid_cv: tuple = (0, 0, 0, 0)

        self.fb_pid.reset()
        self.lr_pid.reset()
        self.ud_pid.reset()
        self.yaw_pid.reset()
        self.fps: int = 0
        self.track_count: int = 0

        self.fb_override: int = 0
        self.lr_override: int = 0
        self.ud_override: int = 0
        self.yaw_override: int = 0
        self.override_time: float = 0.0

        self.video = None
        self.recorder = None
        self.annotatedImage = None
        self.keepRecording: bool = False

    @staticmethod
    def initTello() -> Tello:
        drone = Tello(retry_count=1)
        drone.connect()
        FaceTracker.LOGGER.info("battery {}".format(drone.get_battery()))
        FaceTracker.LOGGER.info("temperature {}".format(
            drone.get_highest_temperature()))
        drone.streamoff()
        drone.streamon()
        drone.get_frame_read()
        drone.takeoff()
        drone.move_up(70)
        return drone

    def _throttle(self) -> bool:
        """Decide whether need to throttle commands to Tello.
        It reduce the command frequence up to FaceTracker.MAX_COMMAND_SEC commands per second.
        """
        t = self.fps <= FaceTracker.MAX_COMMAND_SEC
        if not t:
            interval = self.fps // FaceTracker.MAX_COMMAND_SEC
            t = self.track_count % interval == 0
        #FaceTracker.LOGGER.info(f"{self.track_count} {t} {self.fps}")
        self.track_count += 1
        return t

    def readFrame(self):
        """Return the latest image captured by Tello. And resize to (w, h).
        """
        frame = self.drone.get_frame_read()
        img = frame.frame
        img = cv2.resize(img, (self.w, self.h))
        return img

    def trackFace(self, info) -> tuple:
        area = info[1]
        cx, cy = info[0]

        def clip(x: int, lower: int = -100, upper: int = 100) -> int:
            return max(lower, min(upper, x))

        # lr_v = 0  left -100, right 100
        # fb_v = 0  backward -100, forward 100
        # ud_v = 0  down -100, up 100
        # yaw_v = 0 ccw -100, cw 100
        if time.time() - self.override_time < FaceTracker.OVERRIDE_PERIOD:
            lr_v = self.lr_override
            fb_v = self.fb_override
            ud_v = self.ud_override
            yaw_v = self.yaw_override
        elif area == 0 or cx == 0 or cy == 0:
            lr_v = 0
            fb_v = 0
            ud_v = 0
            yaw_v = 0
        else:
            # left_right_velocity
            # lr_v = int(self.lr_pid.update(cx))
            # lr_v = clip(lr_v, -5, 5)
            lr_v = 0

            # forward_backward_velocity
            pv = math.sqrt(area)
            fb_v = int(self.fb_pid.update(pv))
            fb_v = clip(fb_v, -30, 30)
            # fb_v = 0

            # up_down_velocity
            ud_v = int(self.ud_pid.update(cy))
            ud_v = clip(ud_v, -20, 20)
            # ud_v = 0

            # yaw_velocity
            yaw_v = int(self.yaw_pid.update(cx))
            yaw_v = clip(yaw_v, -30, 30)
            # yaw_v = 0

        #if self._throttle():
        self.drone.send_rc_control(lr_v, fb_v, ud_v, yaw_v)
        FaceTracker.LOGGER.debug(
            f"{lr_v:>3d} {fb_v:>3d} {ud_v:>3d} {yaw_v:>3d}")
        #print("fb", fb_v, "area", area, "error", error)
        self.pid_cv = (lr_v, fb_v, ud_v, yaw_v)
        return self.pid_cv

    def findFace(self, img):
        """detect front faces in the image. If multiple faces are detected, it returs the face with largest area.
        :param img: the image array in BGR
        :return: the detected face center and its area
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(image=gray,
                                                   scaleFactor=1.3,
                                                   minNeighbors=5,
                                                   minSize=(20, 20),
                                                   maxSize=(200, 200))

        faceListCenter = []
        faceListArea = []

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cx = x + w // 2
            cy = y + h // 2
            area = w * h

            faceListCenter.append([cx, cy])
            faceListArea.append(area)
            # cv2.circle(img, (cx, cy), 4, (0, 255, 0), cv2.FILLED)

            # roi_gray = gray[y:y + h, x:x + w]
            # roi_color = img[y:y + h, x:x + w]
            # eyes = self.eye_cascade.detectMultiScale(roi_gray)
            # for (ex, ey, ew, eh) in eyes:
            #     cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh),
            #                   (0, 255, 0), 2)

        if len(faceListArea) != 0:
            i = faceListArea.index(max(faceListArea))
            # Draw line from image center to face center
            iy, ix, _ = img.shape
            #face_center = (faceListCenter[i][0], faceListCenter[i][1])
            cv2.arrowedLine(img, (ix // 2, iy // 2),
                            tuple(faceListCenter[i]),
                            color=(0, 255, 0),
                            thickness=2)
            return img, [faceListCenter[i], faceListArea[i]]
        else:
            return img, [[0, 0], 0]

    def findFace_mp(self, img):
        # Convert the BGR image to RGB and process it with MediaPipe Face Detection.
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb)
        #print(results)

        if not results.detections:
            return img, [[0, 0], 0]

        faceListCenter = []
        faceListArea = []

        for detection in results.detections:
            #print(mp_face_detection.get_key_point(detection, mp_face_detection.FaceKeyPoint.NOSE_TIP))
            #mp_drawing.draw_detection(img, detection)
            box = detection.location_data.relative_bounding_box
            ih, iw, ic = img.shape
            (x, y, w, h) = (int(box.xmin * iw), int(box.ymin * ih),
                            int(box.width * iw), int(box.height * ih))
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(img, f"{int(detection.score[0]*100)}%", (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 0), 1,
                        cv2.LINE_AA)
            cx = int(x + w / 2)
            cy = int(y + h / 2)
            area = w * h
            faceListCenter.append([cx, cy])
            faceListArea.append(area)
            cv2.circle(img, (cx, cy), 5, (0, 255, 0), cv2.FILLED)

        if len(faceListArea) != 0:
            i = faceListArea.index(max(faceListArea))
            return img, [faceListCenter[i], faceListArea[i]]
        else:
            return img, [[0, 0], 0]

    def putFPS(self, img) -> None:
        cur_time = time.time()
        fps: int = int(1.0 / (cur_time - self.prev_time))
        self.prev_time = cur_time
        self.fps = fps
        cv2.putText(img, f"FPS: {fps}", (7, 30), cv2.FONT_HERSHEY_PLAIN, 1,
                    (100, 255, 0), 1, cv2.LINE_AA)

    def putFlight(self, img) -> None:
        #ih, iw, ic = img.shape
        #color = (100, 255, 0)
        cv2.putText(img, f"x': {self.drone.get_acceleration_x()}",
                    (7, 30 + 22), cv2.FONT_HERSHEY_PLAIN, 1, (100, 255, 0), 1,
                    cv2.LINE_AA)
        cv2.putText(img, f"y': {self.drone.get_acceleration_y()}",
                    (7, 30 + 22 + 22), cv2.FONT_HERSHEY_PLAIN, 1,
                    (100, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(img, f"z': {self.drone.get_acceleration_z()}",
                    (7, 30 + 22 + 22 + 22), cv2.FONT_HERSHEY_PLAIN, 1,
                    (100, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(img, f"h : {self.drone.get_distance_tof()}",
                    (7, 30 + 22 + 22 + 22 + 22), cv2.FONT_HERSHEY_PLAIN, 1,
                    (100, 255, 0), 1, cv2.LINE_AA)

    def putPID(self, img) -> None:
        ih, iw, ic = img.shape
        # (lr_v, fb_v, ud_v, yaw_v)
        color = (100, 255, 0)
        cv2.putText(img, f"L-R: {self.pid_cv[0]}", (iw - 90, 30 + 22),
                    cv2.FONT_HERSHEY_PLAIN, 1, color, 1, cv2.LINE_AA)
        cv2.putText(img, f"F+B: {self.pid_cv[1]}", (iw - 90, 30 + 22 + 22),
                    cv2.FONT_HERSHEY_PLAIN, 1, color, 1, cv2.LINE_AA)
        cv2.putText(img, f"U|D: {self.pid_cv[2]}",
                    (iw - 90, 30 + 22 + 22 + 22), cv2.FONT_HERSHEY_PLAIN, 1,
                    color, 1, cv2.LINE_AA)
        cv2.putText(img, f"YAW: {self.pid_cv[3]}",
                    (iw - 90, 30 + 22 + 22 + 22 + 22), cv2.FONT_HERSHEY_PLAIN,
                    1, color, 1, cv2.LINE_AA)

    def putBattery(self, img) -> None:
        ih, iw, ic = img.shape
        battery = self.drone.get_battery()
        color = (100, 255, 0) if battery > 20 else (100, 0, 255)
        cv2.putText(img, f"BAT: {battery}%", (iw - 90, 30),
                    cv2.FONT_HERSHEY_PLAIN, 1, color, 1, cv2.LINE_AA)

    def putTemperature(self, img) -> None:
        ih, iw, ic = img.shape
        temp = self.drone.get_highest_temperature()
        color = (100, 255, 0) if temp < 70 else (100, 0, 255)
        cv2.putText(img, f"TEMP: {temp}", (iw // 2 - 40, 30),
                    cv2.FONT_HERSHEY_PLAIN, 1, color, 1, cv2.LINE_AA)

    def setAnnotatedImage(self, img) -> None:
        self.annotatedImage = img

    def recordVideo(self):
        """record video to an unqiue avi file"""
        if self.video:
            return

        def uniq_filename() -> str:
            fn = f"vid-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
            return fn

        fn = uniq_filename()
        self.keepRecording = True
        self.video = cv2.VideoWriter(fn, cv2.VideoWriter_fourcc(*'XVID'),
                                     FaceTracker.RECORD_FRAME_RATE,
                                     (self.w, self.h))
        while self.keepRecording:
            if self.annotatedImage is not None:
                self.video.write(self.annotatedImage)
                time.sleep(1.0 / FaceTracker.RECORD_FRAME_RATE)
        self.video.release()

    def startVideoRecord(self):
        """create a thread to record video"""
        if self.recorder:
            return
        self.recorder = threading.Thread(target=self.recordVideo)
        self.recorder.start()

    def stopVideoRecord(self):
        self.keepRecording = False

    def end(self) -> None:
        FaceTracker.LOGGER.info("end")
        try:
            self.keepRecording = False
            self.drone.end()
        except AttributeError:
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        FaceTracker.LOGGER.info("exit")
        self.end()

    def __del__(self):
        FaceTracker.LOGGER.info("del")
        self.end()
        try:
            super().__del__(self)
        except AttributeError:
            pass

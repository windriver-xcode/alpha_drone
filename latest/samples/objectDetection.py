#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os

import cv2

cv2_base_dir = os.path.dirname(os.path.abspath(cv2.__file__))
KEY_ESC = 27
WIN_NAME = "Capture - Face detection"


def detectAndDisplay(frame):
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_gray = cv2.equalizeHist(frame_gray)

    # -- Detect faces
    faces = face_cascade.detectMultiScale(frame_gray)
    for (x, y, w, h) in faces:
        center = (x + w // 2, y + h // 2)
        frame = cv2.ellipse(frame, center, (w // 2, h // 2), 0, 0, 360,
                            (255, 0, 255), 4)

        faceROI = frame_gray[y:y + h, x:x + w]
        # -- In each face, detect eyes
        eyes = eyes_cascade.detectMultiScale(faceROI)
        for (x2, y2, w2, h2) in eyes:
            eye_center = (x + x2 + w2 // 2, y + y2 + h2 // 2)
            radius = int(round((w2 + h2) * 0.25))
            frame = cv2.circle(frame, eye_center, radius, (255, 0, 0), 4)

    cv2.imshow(WIN_NAME, frame)


parser = argparse.ArgumentParser(
    description="Code for Cascade Classifier tutorial.")
default_face = os.path.join(cv2_base_dir, "data",
                            "haarcascade_frontalface_alt.xml")
parser.add_argument("--face_cascade",
                    help="Path to face cascade.",
                    default=default_face)
default_eyes = os.path.join(cv2_base_dir, "data",
                            "haarcascade_eye_tree_eyeglasses.xml")
parser.add_argument("--eyes_cascade",
                    help="Path to eyes cascade.",
                    default=default_eyes)
parser.add_argument("--camera",
                    help="Camera divide number.",
                    type=int,
                    default=0)
args = parser.parse_args()

face_cascade_name = args.face_cascade
eyes_cascade_name = args.eyes_cascade

face_cascade = cv2.CascadeClassifier()
eyes_cascade = cv2.CascadeClassifier()

# -- 1. Load the cascades
if not face_cascade.load(cv2.samples.findFile(face_cascade_name)):
    print("--(!)Error loading face cascade")
    exit(0)
if not eyes_cascade.load(cv2.samples.findFile(eyes_cascade_name)):
    print("--(!)Error loading eyes cascade")
    exit(0)

camera_device = args.camera
# -- 2. Read the video stream
cap = cv2.VideoCapture(camera_device)
if not cap.isOpened:
    print("--(!)Error opening video capture")
    exit(0)

while cap.isOpened():
    ret, frame = cap.read()
    if frame is None:
        print("--(!) No captured frame -- Break!")
        break

    detectAndDisplay(frame)

    k = cv2.waitKey(10) & 0xFF
    if k == KEY_ESC or k == ord('q'):  # wait for ESC key or 'q' key to exit
        break

cv2.destroyWindow(WIN_NAME)
cap.release()
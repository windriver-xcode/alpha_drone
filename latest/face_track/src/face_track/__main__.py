#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys

import cv2

from face_track import tracker

request_run: bool = True


def main(args=None) -> int:
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    print(f"OpenCV version: {cv2.__version__}")
    cv_info = [
        re.sub('\s+', ' ', ci.strip())
        for ci in cv2.getBuildInformation().strip().split('\n')
        if len(ci) > 0 and re.search(r'(nvidia*:?)|(cuda*:)|(cudnn*:)',
                                     ci.lower()) is not None
    ]
    if cv_info:
        print(cv_info)

    alpha = tracker.FaceTracker()
    alpha.startVideoRecord()
    while request_run:
        img = alpha.readFrame()
        img, info = alpha.findFace(img)
        alpha.trackFace(info)
        alpha.putPID(img)
        alpha.putFPS(img)
        alpha.putBattery(img)
        alpha.putTemperature(img)
        alpha.putFlight(img)
        alpha.setAnnotatedImage(img)
        cv2.imshow("Alpha Drone", img)
        if cv2.waitKey(1) != -1:
            break

    cv2.destroyAllWindows()
    alpha.end()
    return 0


if __name__ == "__main__":
    sys.exit(main())

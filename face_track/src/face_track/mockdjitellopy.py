# -*- coding: utf-8 -*-
"""Mock library for interacting with DJI Ryze Tello drones.
"""

# coding=utf-8
import logging
import random
import socket
import time
from threading import Thread
from typing import Dict, Optional, Type, Union

import cv2  # type: ignore


class Tello:
    """Mock Python wrapper to interact with the Ryze Tello drone using the official Tello api.
    [original djitellopy](https://github.com/damiafuentes/DJITelloPy)

    Tello API documentation:
    [1.3](https://dl-cdn.ryzerobotics.com/downloads/tello/20180910/Tello%20SDK%20Documentation%20EN_1.3.pdf),
    [2.0 with EDU-only commands](https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf)
    """
    RESPONSE_TIMEOUT = 7  # in seconds
    TAKEOFF_TIMEOUT = 20  # in seconds
    TIME_BTW_COMMANDS = 0.1  # in seconds
    TIME_BTW_RC_CONTROL_COMMANDS = 0.001  # in seconds
    RETRY_COUNT = 3  # number of retries after a failed command
    TELLO_IP = '192.168.10.1'  # Tello IP address

    # Video stream, server socket
    VS_UDP_IP = '0.0.0.0'
    VS_UDP_PORT = 11111

    CONTROL_UDP_PORT = 8889
    STATE_UDP_PORT = 8890

    # Set up logger
    HANDLER = logging.StreamHandler()
    FORMATTER = logging.Formatter(
        '[%(levelname)s] %(filename)s - %(lineno)d - %(message)s')
    HANDLER.setFormatter(FORMATTER)

    LOGGER = logging.getLogger('tello')
    LOGGER.addHandler(HANDLER)
    LOGGER.setLevel(logging.INFO)
    # Use Tello.LOGGER.setLevel(logging.<LEVEL>) in YOUR CODE
    # to only receive logs of the desired level and higher

    # VideoCapture object
    cap: Optional[cv2.VideoCapture] = None
    background_frame_read: Optional['BackgroundFrameRead'] = None

    stream_on = False
    is_flying = False

    def __init__(self, host=TELLO_IP, retry_count=RETRY_COUNT):
        self.host = host
        self.retry_count = retry_count
        self.stream_on = False
        self.battery = 70
        self.temph = 46
        self.last_rc_control_timestamp = time.time()

    def connect(self, wait_for_state=True):
        """Enter SDK mode. Call this before any of the control functions.
        """
        pass

    def get_battery(self) -> int:
        """Get current battery percentage
        Returns:
            int: 0-100
        """
        return self.battery

    def get_highest_temperature(self) -> int:
        """Get highest temperature
        Returns:
            float: highest temperature (°C)
        """
        return self.temph

    def get_speed_x(self) -> int:
        """X-Axis Speed
        Returns:
            int: speed
        """
        return random.randrange(0, 101)

    def get_speed_y(self) -> int:
        """Y-Axis Speed
        Returns:
            int: speed
        """
        return random.randrange(0, 101)

    def get_distance_tof(self) -> int:
        """Get current distance value from TOF in cm
        Returns:
            int: TOF distance in cm
        """
        return random.randrange(0, 191)

    def get_speed_z(self) -> int:
        """Z-Axis Speed
        Returns:
            int: speed
        """
        return random.randrange(0, 101)

    def get_acceleration_x(self) -> float:
        """X-Axis Acceleration
        Returns:
            float: acceleration
        """
        return round(random.uniform(0.0, 100.0), 2)

    def get_acceleration_y(self) -> float:
        """Y-Axis Acceleration
        Returns:
            float: acceleration
        """
        return round(random.uniform(0.0, 100.0), 2)

    def get_acceleration_z(self) -> float:
        """Z-Axis Acceleration
        Returns:
            float: acceleration
        """
        return round(random.uniform(0.0, 100.0), 2)

    def send_control_command(self,
                             command: str,
                             timeout: int = RESPONSE_TIMEOUT) -> bool:
        """Send control command to Tello and wait for its response.
        Internal method, you normally wouldn't call this yourself.
        """
        self.LOGGER.debug("Command '{}' sent".format(command))
        return True

    def takeoff(self):
        """Automatic takeoff.
        """
        # Something it takes a looooot of time to take off and return a succesful takeoff.
        # So we better wait. Otherwise, it would give us an error on the following calls.
        self.send_control_command("takeoff", timeout=Tello.TAKEOFF_TIMEOUT)
        self.is_flying = True

    def land(self):
        """Automatic landing.
        """
        self.send_control_command("land")
        self.is_flying = False

    def streamon(self):
        """Turn on video streaming. Use `tello.get_frame_read` afterwards.
        Video Streaming is supported on all tellos when in AP mode (i.e.
        when your computer is connected to Tello-XXXXXX WiFi ntwork).
        Currently Tello EDUs do not support video streaming while connected
        to a WiFi-network.

        !!! Note:
            If the response is 'Unknown command' you have to update the Tello
            firmware. This can be done using the official Tello app.
        """
        self.send_control_command("streamon")
        self.stream_on = True

    def streamoff(self):
        """Turn off video streaming.
        """
        self.send_control_command("streamoff")
        self.stream_on = False

    def get_frame_read(self) -> 'BackgroundFrameRead':
        """Get the BackgroundFrameRead object from the camera drone. Then, you just need to call
        backgroundFrameRead.frame to get the actual frame received by the drone.
        Returns:
            BackgroundFrameRead
        """
        if self.background_frame_read is None:
            address = 0  #self.get_udp_video_address()
            self.background_frame_read = BackgroundFrameRead(
                self, address)  # also sets self.cap
            self.background_frame_read.start()
        return self.background_frame_read

    def get_udp_video_address(self) -> str:
        """Internal method, you normally wouldn't call this youself.
        """
        #address_schema = 'udp://@{ip}:{port}'  # + '?overrun_nonfatal=1&fifo_size=5000'
        #address = address_schema.format(ip=self.VS_UDP_IP, port=self.VS_UDP_PORT)
        #return address
        return "0"

    def get_video_capture(self):
        """Get the VideoCapture object from the camera drone.
        Users usually want to use get_frame_read instead.
        Returns:
            VideoCapture
        """

        if self.cap is None:
            self.cap = cv2.VideoCapture(self.get_udp_video_address())

        if not self.cap.isOpened():
            self.cap.open(self.get_udp_video_address())

        return self.cap

    def end(self):
        """Call this method when you want to end the tello object
        """
        if self.is_flying:
            self.land()
        if self.stream_on:
            self.streamoff()
        if self.background_frame_read is not None:
            self.background_frame_read.stop()
        if self.cap is not None:
            self.cap.release()

    def __del__(self):
        self.end()

    def send_rc_control(self, left_right_velocity: int,
                        forward_backward_velocity: int, up_down_velocity: int,
                        yaw_velocity: int):
        """Send RC control via four channels. Command is sent every self.TIME_BTW_RC_CONTROL_COMMANDS seconds.
        Arguments:
            left_right_velocity: -100~100 (left/right)
            forward_backward_velocity: -100~100 (forward/backward)
            up_down_velocity: -100~100 (up/down)
            yaw_velocity: -100~100 (yaw)
        """
        def clamp100(x: int) -> int:
            return max(-100, min(100, x))

        if time.time(
        ) - self.last_rc_control_timestamp > self.TIME_BTW_RC_CONTROL_COMMANDS:
            self.last_rc_control_timestamp = time.time()
            cmd = 'rc {} {} {} {}'.format(clamp100(left_right_velocity),
                                          clamp100(forward_backward_velocity),
                                          clamp100(up_down_velocity),
                                          clamp100(yaw_velocity))
        #self.send_command_without_return(cmd)
        self.send_control_command(cmd)

    def move(self, direction: str, x: int):
        """Tello fly up, down, left, right, forward or back with distance x cm.
        Users would normally call one of the move_x functions instead.
        Arguments:
            direction: up, down, left, right, forward or back
            x: 20-500
        """
        self.send_control_command("{} {}".format(direction, x))

    def move_up(self, x: int):
        """Fly x cm up.
        Arguments:
            x: 20-500
        """
        self.move("up", x)


class BackgroundFrameRead:
    """
    Mock This class read frames from a VideoCapture in background. Use
    backgroundFrameRead.frame to get the current frame.
    """
    def __init__(self, tello, address):
        tello.cap = cv2.VideoCapture(address)

        self.cap = tello.cap

        if not self.cap.isOpened():
            self.cap.open(address)

        self.grabbed, self.frame = self.cap.read()
        if not self.grabbed or self.frame is None:
            raise Exception('Failed to grab first frame from video stream')

        self.stopped = False
        self.worker = Thread(target=self.update_frame, args=(), daemon=True)

    def start(self):
        """Start the frame update worker
        Internal method, you normally wouldn't call this yourself.
        """
        self.worker.start()

    def update_frame(self):
        """Thread worker function to retrieve frames from a VideoCapture
        Internal method, you normally wouldn't call this yourself.
        """
        while not self.stopped:
            if not self.grabbed or not self.cap.isOpened():
                self.stop()
            else:
                self.grabbed, frame = self.cap.read()
                self.frame = frame.copy()

    def stop(self):
        """Stop the frame update worker
        Internal method, you normally wouldn't call this yourself.
        """
        self.stopped = True
        self.worker.join()

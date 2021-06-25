# -*- coding: utf-8 -*-
import logging
import time


class PID(object):
    """A simple PID control implementation
    """

    EPSILON = 1e-3  # the minium delta time in seconds
    LOST_TIME = 0.2  # the default time for lost face tracking time in seconds
    HANDLER = logging.StreamHandler()
    FORMATTER = logging.Formatter(
        '[%(levelname)s] %(filename)s - %(lineno)d - %(message)s')
    HANDLER.setFormatter(FORMATTER)

    LOGGER = logging.getLogger('pid')
    LOGGER.addHandler(HANDLER)
    LOGGER.setLevel(logging.INFO)

    def __init__(self,
                 name: str = '',
                 kP: float = 0.0,
                 kI: float = 0.0,
                 kD: float = 0.0,
                 SP: float = 0.0) -> None:
        """Initialize a PID instance
        :param name: The name of PID
        :param kP: the proportional gain
        :param kI: the integral gain
        :param kD: the derivative gain
        :param SP: the setpoint
        :return: None
        """
        super().__init__()
        self.name: str = name
        # initialize gains
        self.kP: float = kP
        self.kI: float = kI
        self.kD: float = kD
        self.SP: float = SP

        self.cP: float = 0.0
        self.cI: float = 0.0
        self.cD: float = 0.0
        self.cV: float = 0.0

        self.currTime: float = time.time()
        self.prevTime: float = self.currTime
        self.prevError: float = 0.0

    def reset(self) -> None:
        # reset the current and previous time
        self.currTime = time.time()
        self.prevTime = self.currTime

        # reset the previous error
        self.prevError = 0.0

        # reset the term result variables
        self.cP = 0.0
        self.cI = 0.0
        self.cD = 0.0
        self.cV = 0.0

    def update(self, pv: float) -> float:
        """ calculate the control value
        :param pv: the process variable, the error = SP - PV (SP is the setpoint, and PV(t) is the process variable)
        :return: the control variable
        """
        # grab the current time and calculate delta time
        self.currTime = time.time()
        deltaTime = min(self.currTime - self.prevTime, PID.LOST_TIME)

        # if deltaTime < PID.EPSILON:
        #     return self.cV
        error = self.SP - pv
        # calculate the delta error
        deltaError = error - self.prevError

        # calculate the proportional term
        self.cP = error

        # calculate the integral term
        self.cI += error * deltaTime

        # calculate the derivative term (and prevent divide by zero)
        self.cD = (deltaError / deltaTime) if deltaTime > 0.0 else 0.0

        # save previous time and error for the next update
        self.prevTime = self.currTime
        self.prevError = error

        # sum the terms and return
        self.cV = sum(
            [self.kP * self.cP, self.kI * self.cI, self.kD * self.cD])
        PID.LOGGER.debug(
            f"{self.name} {self.cP} {self.cI} {self.cD} {self.cV}")

        return self.cV

    def __str__(self) -> str:
        return f"{self.name} {self.cP} {self.cI} {self.cD} {self.cV}"

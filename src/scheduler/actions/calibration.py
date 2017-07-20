"""Run calibration routines."""

from commsensor import calibration
from commsensor.logging import log


def calRF1():
    log.info("starting calibration on RF1")
    calibration.runner.rf1()


def calRF2():
    log.info("starting calibration on RF2")
    calibration.runner.rf2()


def test_cal():
    log.info("starting test cal")
    raise NotImplementedError("TODO")

import pytest
from src.domain.entities.geometry import Point
from src.infrastructure.input.fail_safe import FailSafeManager, EmergencyStopException
from src.infrastructure.input.pynput_controller import PynputHumanController


def test_fail_safe_initial_state():
    fs = FailSafeManager(check_corner=False)
    assert not fs.is_aborted
    # check() should not raise
    fs.check()


def test_fail_safe_manual_trigger():
    fs = FailSafeManager(check_corner=False)
    fs._aborted = True
    assert fs.is_aborted

    with pytest.raises(EmergencyStopException, match="Kill switch activated"):
        fs.check()

    fs.reset()
    assert not fs.is_aborted
    fs.check()


def test_pynput_controller_emergency_stop():
    fs = FailSafeManager(check_corner=False)
    ctrl = PynputHumanController(fail_safe=fs)

    # Normal execution doesn't raise
    ctrl.sleep_random(0.01, 0.02)

    # Trigger emergency stop
    fs._aborted = True

    with pytest.raises(EmergencyStopException):
        ctrl.move_to(Point(100, 100))

    with pytest.raises(EmergencyStopException):
        ctrl.click()

    with pytest.raises(EmergencyStopException):
        ctrl.type_text("test")

    with pytest.raises(EmergencyStopException):
        ctrl.clear_input()

    with pytest.raises(EmergencyStopException):
        ctrl.scroll(2)

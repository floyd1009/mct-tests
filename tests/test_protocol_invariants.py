"""Tests for protocol-level invariants and state transitions.

These cover behaviours that are not strict acceptance criteria from the
brief but fall directly out of the application's contract. They also
demonstrate the growth axis of the suite: parametrised cases for input
ranges, and explicit transitions between the two visual states.
"""

import pytest

from tests.conftest import pump
from tests.helpers import udp_sender
from tests.helpers.screen_capture import (
    count_matching,
    grab,
    is_red,
    is_white,
)
from tests.test_failure_display import FAILURE_BOX_AREA, FAILURE_BOX_REGION
from tests.test_speed_display import DIGIT_REGION


@pytest.mark.parametrize("speed", [0, 1, 42, 99, 100, 142, 255])
def test_speed_renders_white_digits_for_full_input_range(qapp, speed_window, speed):
    """Speed values across the full byte range must render white digits.

    The application takes the speed byte modulo 100 before rendering, so
    142 displays as "42" and 100 displays as "00". This test does not
    assert which digits are drawn (that would require OCR), only that
    the OK rendering path is exercised end to end.
    """
    udp_sender.send(speed=speed, failure=False)
    pump(qapp)

    image = grab(speed_window)
    white_pixels = count_matching(image, DIGIT_REGION, is_white)

    assert white_pixels > 50, f"speed={speed} produced no visible digits"


@pytest.mark.parametrize("flag_byte", [0x01, 0x05, 0x80, 0xFF])
def test_any_nonzero_failure_byte_triggers_failure_state(qapp, speed_window, flag_byte):
    """Per the contract, byte[1] != 0 means failure, regardless of value."""
    udp_sender.send_raw(bytes((0x2A, flag_byte)))
    pump(qapp)

    image = grab(speed_window)
    red_pixels = count_matching(image, FAILURE_BOX_REGION, is_red)

    assert red_pixels > FAILURE_BOX_AREA * 0.6, (
        f"failure flag 0x{flag_byte:02X} did not trigger the red box"
    )


def test_state_recovers_from_failure_to_ok(qapp, speed_window):
    """After a failure packet, a subsequent OK packet must restore the digits."""
    udp_sender.send(speed=42, failure=True)
    pump(qapp)
    udp_sender.send(speed=42, failure=False)
    pump(qapp)

    image = grab(speed_window)
    white_pixels = count_matching(image, DIGIT_REGION, is_white)
    red_pixels = count_matching(image, FAILURE_BOX_REGION, is_red)

    assert white_pixels > 100, "OK state did not restore after failure"
    assert red_pixels == 0, "failure box still visible after OK packet"


def test_short_payload_is_ignored(qapp, speed_window):
    """Payloads shorter than 2 bytes must not change the display."""
    # The window starts in the OK state with speed=0. A 1-byte payload
    # must not crash the app or change the rendered output.
    udp_sender.send_raw(bytes((0x2A,)))
    pump(qapp)

    image = grab(speed_window)
    red_pixels = count_matching(image, FAILURE_BOX_REGION, is_red)

    assert red_pixels == 0, "short payload incorrectly triggered failure state"

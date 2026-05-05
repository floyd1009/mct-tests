"""Tests for protocol-level invariants and state transitions.

These cover behaviours that are not strict acceptance criteria from the
brief but fall directly out of the application's contract. They also
demonstrate the growth axis of the suite: parametrised cases for input
ranges, and explicit transitions between the two visual states.
"""

import pytest

from tests.conftest import settle
from tests.helpers import udp_sender
from tests.helpers.screen_capture import (
    capture_display,
    count_red_pixels,
    count_white_pixels,
    read_digits,
)
from tests.test_failure_display import EXPECTED_RED_PIXELS_MIN


@pytest.mark.parametrize(
    "speed,expected",
    [
        (0, "00"),
        (1, "01"),
        (42, "42"),
        (99, "99"),
        (100, "00"),
        (142, "42"),
        (255, "55"),
    ],
)
def test_speed_renders_correct_digits_after_modulo_100(running_app, speed, expected):
    """Speed values across the full byte range must render the byte modulo 100.

    The application formats `byte[0] % 100` as zero-padded two-digit
    text, so 100 displays as "00", 142 as "42", 255 as "55", etc.
    OCR confirms the exact rendered digits, not just that something
    was drawn.
    """
    udp_sender.send(speed=speed, failure=False)
    settle()

    image = capture_display()

    assert read_digits(image) == expected, (
        f"speed={speed} expected to render {expected!r}, got {read_digits(image)!r}"
    )


@pytest.mark.parametrize("flag_byte", [0x01, 0x05, 0x80, 0xFF])
def test_any_nonzero_failure_byte_triggers_failure_state(running_app, flag_byte):
    """Per the contract, byte[1] != 0 means failure, regardless of value."""
    udp_sender.send_raw(bytes((0x2A, flag_byte)))
    settle()

    image = capture_display()
    red_pixels = count_red_pixels(image)

    assert red_pixels > EXPECTED_RED_PIXELS_MIN, (
        f"failure flag 0x{flag_byte:02X} did not trigger the red box"
    )


def test_state_recovers_from_failure_to_ok(running_app):
    """After a failure packet, a subsequent OK packet must restore the digits."""
    udp_sender.send(speed=42, failure=True)
    settle()
    udp_sender.send(speed=42, failure=False)
    settle()

    image = capture_display()

    assert read_digits(image) == "42", (
        f"expected the digits to read '42' after recovery, got {read_digits(image)!r}"
    )
    assert count_red_pixels(image) == 0, "failure box still visible after OK packet"


def test_short_payload_is_ignored(running_app):
    """Payloads shorter than 2 bytes must not change the display."""
    # The window starts in the OK state with speed=0. A 1-byte payload
    # must not crash the app or change the rendered output.
    udp_sender.send_raw(bytes((0x2A,)))
    settle()

    image = capture_display()
    red_pixels = count_red_pixels(image)

    assert red_pixels == 0, "short payload incorrectly triggered failure state"

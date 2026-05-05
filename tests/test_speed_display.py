"""Tests for the OK rendering path: the application shows the speed value."""

from tests.conftest import settle
from tests.helpers import udp_sender
from tests.helpers.screen_capture import (
    capture_display,
    count_red_pixels,
    read_digits,
)


def test_speed_42_renders_two_digits(running_app):
    """Q2.1: UDP 0x2A.00 must show 42."""
    udp_sender.send(speed=0x2A, failure=False)
    settle()

    image = capture_display()

    assert read_digits(image) == "42", (
        f"expected the rendered digits to read '42', got {read_digits(image)!r}"
    )
    assert count_red_pixels(image) == 0, (
        "red pixels found in OK state; failure box must not be drawn"
    )

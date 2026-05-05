"""Tests for the OK rendering path: the application shows the speed value."""

from tests.conftest import settle
from tests.helpers import udp_sender
from tests.helpers.screen_capture import (
    capture_display,
    count_red_pixels,
    count_white_pixels,
)


def test_speed_42_renders_two_digits(running_app):
    """Q2.1: UDP 0x2A.00 must show 42."""
    udp_sender.send(speed=0x2A, failure=False)
    settle()

    image = capture_display()

    white_pixels = count_white_pixels(image)
    red_pixels = count_red_pixels(image)

    assert white_pixels > 100, (
        f"expected white digit pixels on screen, got {white_pixels}"
    )
    assert red_pixels == 0, (
        f"red pixels found in OK state; failure box must not be drawn ({red_pixels} red pixels)"
    )

"""Tests for the OK rendering path: the application shows the speed value."""

from tests.conftest import pump
from tests.helpers import udp_sender
from tests.helpers.screen_capture import (
    count_matching,
    grab,
    is_red,
    is_white,
)


# Region of the 128x128 window where the digits are drawn. The font is
# Consolas 44pt bold, centered, so a wide horizontal band in the middle
# captures both digits with margin.
DIGIT_REGION = (15, 35, 100, 60)


def test_speed_42_renders_two_digits(qapp, speed_window):
    """Q2.1: UDP 0x2A.00 must show 42."""
    udp_sender.send(speed=0x2A, failure=False)
    pump(qapp)

    image = grab(speed_window)

    white_pixels = count_matching(image, DIGIT_REGION, is_white)
    red_pixels = count_matching(image, DIGIT_REGION, is_red)

    assert white_pixels > 100, (
        f"expected white digit pixels in the centre band, got {white_pixels}"
    )
    assert red_pixels == 0, (
        f"red pixels found in OK state; failure box must not be drawn ({red_pixels} red pixels)"
    )

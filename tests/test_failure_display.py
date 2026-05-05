"""Tests for the failure rendering path: the application shows a red box."""

from tests.conftest import settle
from tests.helpers import udp_sender
from tests.helpers.screen_capture import capture_display, count_red_pixels

# The failure box is 88 by 88 pixels filled red, with a black X drawn
# through it. The X consumes some pixels but the red region dominates.
EXPECTED_RED_PIXELS_MIN = 88 * 88 * 0.6


def test_failure_renders_red_box(running_app):
    """Q2.2: UDP 0x2A.01 must show a red box."""
    udp_sender.send(speed=0x2A, failure=True)
    settle()

    image = capture_display()

    red_pixels = count_red_pixels(image)

    assert red_pixels > EXPECTED_RED_PIXELS_MIN, (
        f"expected the failure box to be predominantly red on screen, "
        f"got {red_pixels} red pixels"
    )

"""Tests for the failure rendering path: the application shows a red box."""

from tests.conftest import pump
from tests.helpers import udp_sender
from tests.helpers.screen_capture import count_matching, grab, is_red


# The application draws the failure square at (20, 20) with side 88.
FAILURE_BOX_REGION = (20, 20, 88, 88)
FAILURE_BOX_AREA = 88 * 88


def test_failure_renders_red_box(qapp, speed_window):
    """Q2.2: UDP 0x2A.01 must show a red box."""
    udp_sender.send(speed=0x2A, failure=True)
    pump(qapp)

    image = grab(speed_window)

    red_pixels = count_matching(image, FAILURE_BOX_REGION, is_red)

    # The box is filled red with a black X drawn through it. The X is at
    # most a few hundred pixels wide across the diagonals, so the red
    # region must dominate by a wide margin.
    assert red_pixels > FAILURE_BOX_AREA * 0.6, (
        f"expected the failure box region to be predominantly red, "
        f"got {red_pixels} of {FAILURE_BOX_AREA} pixels"
    )

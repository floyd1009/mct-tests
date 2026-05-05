"""Shared pytest fixtures.

The application under test is treated as a true black box: it runs in
its own subprocess, the test process never imports it, and verification
happens by capturing pixels from the host display rather than reading
widget state.

Inputs go in over UDP. Outputs are read off the screen. Nothing else.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.helpers import udp_sender
from tests.helpers.screen_capture import capture_display, count_red_pixels

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = REPO_ROOT / "app" / "main.py"

# Maximum time to wait for the app to become responsive after launch.
# The fixture probes for readiness by sending a known UDP packet and
# observing the rendered output, so this is a worst-case bound rather
# than a fixed sleep. Generous on cold start.
READINESS_TIMEOUT_SECONDS = 8.0
READINESS_POLL_SECONDS = 0.3

# Time to wait between sending a UDP packet and capturing pixels, so the
# datagram is delivered, the readyRead signal fires, and the paint event
# completes.
PAINT_SETTLE_SECONDS = 0.5


def _probe_until_responsive(proc: subprocess.Popen) -> None:
    """Send a failure packet and wait until the red box appears on screen.

    This is a readiness probe: it confirms the app's window is up, its
    UDP socket is bound, and its paint pipeline is delivering pixels to
    the display. Without this probe, fast machines pass and slow
    machines flake on the first test of a cold suite.
    """
    deadline = time.monotonic() + READINESS_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"application exited prematurely with code {proc.returncode}"
            )
        udp_sender.send(speed=0, failure=True)
        time.sleep(READINESS_POLL_SECONDS)
        if count_red_pixels(capture_display()) > 1000:
            return
    raise RuntimeError(
        f"application did not become responsive within {READINESS_TIMEOUT_SECONDS}s"
    )


@pytest.fixture
def running_app():
    """Launch app/main.py as a subprocess for the duration of one test."""
    env = os.environ.copy()
    proc = subprocess.Popen(
        [sys.executable, str(APP_PATH)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _probe_until_responsive(proc)
    except Exception:
        proc.terminate()
        proc.wait(timeout=5)
        raise

    # Reset to a known OK state so the test starts clean.
    udp_sender.send(speed=0, failure=False)
    time.sleep(PAINT_SETTLE_SECONDS)

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def settle():
    """Wait for the app to process the most recent UDP packet and repaint."""
    time.sleep(PAINT_SETTLE_SECONDS)

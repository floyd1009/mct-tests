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

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = REPO_ROOT / "app" / "main.py"

# Time to wait for the app's window to appear after spawning the process.
# Generous because Qt initialisation includes platform plugin loading
# and font cache warmup on a cold container.
WINDOW_APPEAR_SECONDS = 1.5

# Time to wait between sending a UDP packet and capturing pixels, so the
# datagram is delivered, the readyRead signal fires, and the paint event
# completes.
PAINT_SETTLE_SECONDS = 0.5


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
    time.sleep(WINDOW_APPEAR_SECONDS)

    if proc.poll() is not None:
        raise RuntimeError(
            f"application process exited prematurely with code {proc.returncode}"
        )

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

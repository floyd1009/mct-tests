"""Shared pytest fixtures.

Design notes:

* The application is treated as a black box. We import the SpeedWindow
  class only to instantiate it inside the test process; we never call its
  internal methods or read private state. The contract under test is
  "UDP packets in, rendered pixels out".

* QApplication is session-scoped. Qt does not allow more than one
  QApplication per process, and recreating it between tests is slow and
  fragile.

* SpeedWindow is function-scoped. Each test gets a fresh instance so
  state from one test cannot leak into another. The UDP socket bound to
  port 3000 is closed on teardown to free the port for the next test.

* `pump` waits for queued Qt events (UDP datagram delivery, paint events)
  to be processed. It is bounded by a timeout so a misbehaving test
  cannot hang the suite.
"""

import sys
import time
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

# Make the SUT importable without modifying the app/ folder.
APP_DIR = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

from main import SpeedWindow  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.fixture
def speed_window(qapp):
    window = SpeedWindow()
    window.show()
    qapp.processEvents()
    yield window
    window.socket.close()
    window.close()
    window.deleteLater()
    qapp.processEvents()


def pump(qapp, milliseconds: int = 200) -> None:
    """Process pending Qt events for up to `milliseconds`.

    UDP delivery on localhost is fast but not synchronous from the
    sender's perspective. A short pump window lets the readyRead signal
    fire and the paint event run before we sample pixels.
    """
    deadline = time.monotonic() + milliseconds / 1000.0
    while time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.005)

# MCT Working Example: Automated Tests

Automated test suite for the AVILUS Mission Control Engineer working
example. The system under test is a small Qt application that listens
on UDP port 3000 and renders either a speed value or a failure
indicator on a 128 by 128 window.

The suite treats the application as a true black box: the application
runs as a subprocess, the test process never imports it, inputs are
sent over UDP, and outputs are read off the host display via screen
capture.

## Quick start

The canonical way to run the suite is in the container, since that
matches CI and removes any host-OS variance:

```bash
docker build -t mct-tests .
docker run --rm mct-tests
```

Local execution is supported but requires a working display. On Linux
that means running under an X server (or `xvfb-run` for headless). On
macOS the native run additionally needs Screen Recording permission
granted to the terminal application, since mss reads the actual screen.
For day-to-day development on macOS the simplest path is to use Docker:

```bash
docker run --rm mct-tests
```

15 tests, around 30 seconds.

## What the application does

Treated as a black box, the application accepts 2-byte UDP packets on
port 3000 and renders one of two visual states:

| Input                        | Rendered state                                                       |
|------------------------------|----------------------------------------------------------------------|
| `byte[1] == 0`               | The speed value `byte[0] mod 100` as zero-padded white digits.       |
| `byte[1] != 0`               | A red square at (20, 20)-(108, 108) with a black X drawn through it. |
| Payload shorter than 2 bytes | Silently ignored. Last good state is preserved.                      |

Tests verify these states by sending UDP packets and inspecting the
rendered pixels on the host display.

## Concept for automated testing

### Q1.1 Tools

| Tool                | Why it is here                                                      |
|---------------------|---------------------------------------------------------------------|
| `pytest`            | Fixtures, parametrisation, markers, plugin ecosystem.               |
| `mss`               | Cross-platform screen capture. Works under Xvfb in the container and against the real display locally. |
| `numpy`             | Vectorised pixel-region operations are an order of magnitude faster than per-pixel Python loops. |
| Standard library `socket` and `subprocess` | Sending UDP packets is two lines. Spawning the application is two lines. No wrapper library needed. |
| `Xvfb` (system)     | Provides a virtual X display in the container so the application has somewhere to render headlessly. |

OCR was considered for verifying that the digits read "42" but rejected.
`pytesseract` adds a heavy native dependency, slows the suite, and is
flaky on small bold fonts. Pixel sampling against colour predicates is
deterministic and fast. The trade-off is that the suite asserts the OK
state was rendered, not that the specific digits "4" and "2" appear.
Given that the application draws digits via `QPainter.drawText` with a
single code path, this is acceptable for the contract under test. If
digit-level verification ever becomes a hard requirement, an OCR-based
test can be added behind a `@pytest.mark.slow` marker without changing
the rest of the suite.

### Q1.2 Structure for growth

```
mct-tests/
├── app/                              # System under test, unchanged.
│   ├── main.py
│   ├── send_test.py
│   └── requirements.txt
├── tests/
│   ├── conftest.py                   # Subprocess fixture, settle helper.
│   ├── helpers/
│   │   ├── udp_sender.py             # send(speed, failure), send_raw(bytes)
│   │   └── screen_capture.py         # capture_display(), count_red_pixels(), count_white_pixels()
│   ├── test_speed_display.py         # OK path acceptance test.
│   ├── test_failure_display.py       # Failure path acceptance test.
│   └── test_protocol_invariants.py   # Modulo, non-zero flag, recovery, malformed input.
├── Dockerfile
├── pytest.ini
└── requirements-test.txt
```

Three principles drive this layout:

1. **Black-box discipline is structural.** The `app/` folder is treated
   as read-only by the test code. The test process never imports the
   application. The only inputs are UDP packets, the only outputs are
   pixels read from the host display. The suite is therefore valid
   against any UDP-driven visual application with the same protocol,
   not just this one.
2. **One file per visual state.** Today there are two states (digits,
   red box) and one file each. A new state means a new file, not a
   500-line monolith.
3. **Helpers are composable, not opinionated.** `count_red_pixels` and
   `count_white_pixels` take colour predicates internally. Adding a new
   visual element (an icon, a warning border) only needs a new
   predicate, not a new helper module.

Extension points already in place:

- `udp_sender.send_raw(bytes)` for malformed-packet tests.
- `pytest.mark.slow` is registered in `pytest.ini` for tests that
  should be excluded from fast CI runs.
- The `running_app` fixture is function-scoped so each test gets a
  clean application instance and tests cannot leak state into each
  other.

### Q1.3 Running headless in Docker

Qt applications need a display to render into. The container provides
one with **Xvfb**, a virtual X server that draws to memory rather than
to a screen. The Dockerfile installs `xvfb` and Qt's xcb runtime
dependencies, and the container `CMD` wraps `pytest` with `xvfb-run`,
which starts Xvfb on a free display, sets `DISPLAY`, runs the command,
and tears Xvfb down on exit.

The screen size is configured at 400x400 with 24-bit colour, which
gives the 128x128 application window margin on every side and matches
what `mss` returns when the test asks for the primary display.

An alternative considered was `QT_QPA_PLATFORM=offscreen`. That keeps
the dependency footprint smaller because Xvfb is not needed, but it
renders into Qt's offscreen platform plugin rather than to a real
display, which means the test process cannot use OS-level screen
capture for verification. That breaks the black-box discipline of the
suite, so Xvfb plus xcb is the chosen path.

## Test design notes

### App lifecycle

Each test gets a fresh `app/main.py` subprocess. The fixture in
`conftest.py` spawns the process, waits for the window to appear,
yields to the test, then terminates the process. This guarantees no
state leakage between tests at the cost of about two seconds of fixed
overhead per test.

### Verification

Pixel sampling instead of OCR or image diff. Two predicates do most of
the work: `count_white_pixels` and `count_red_pixels`. Region
selection is implicit because the only thing rendered on the virtual
display is the application's window, so counts are taken across the
full captured frame and compared against thresholds chosen with margin.

### Timing

UDP delivery on localhost is fast but not synchronous, and Qt's paint
event runs on the next iteration of its event loop. After sending a
packet the test calls `settle()`, which sleeps long enough for the
delivery and repaint to complete before the screen is captured.

## What is not covered, and why

A few things were considered and explicitly left out.

- **Image-diff testing against a reference PNG.** Brittle across
  platforms because of font rendering. Adds a maintenance burden
  whenever the application's appearance changes.
- **Stress and fuzz testing.** Worth doing eventually; the suite has
  the hooks (`send_raw`, the `slow` marker) but the work is out of
  scope for this exercise.
- **CI configuration files.** The Dockerfile is enough to demonstrate
  the approach. A real GitHub Actions or GitLab CI file would just
  call `docker build` and `docker run`.

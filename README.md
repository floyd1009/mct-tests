# MCT Working Example: Automated Tests

Automated test suite for the AVILUS Mission Control Engineer working example.
The system under test is a small Qt application that listens on UDP port 3000
and renders either a speed value or a failure indicator on a 128 by 128 window.

## Quick start

Local:

```bash
pip install -r requirements-test.txt
QT_QPA_PLATFORM=offscreen pytest
```

In Docker:

```bash
docker build -t mct-tests .
docker run --rm mct-tests
```

The suite runs in under four seconds and currently has 15 tests.

## What the application does

Treated as a black box, the application accepts 2-byte UDP packets on
port 3000 and renders one of two visual states:

| Input                 | Rendered state                                                       |
|-----------------------|----------------------------------------------------------------------|
| `byte[1] == 0`        | The speed value `byte[0] mod 100` as zero-padded white digits.       |
| `byte[1] != 0`        | A red square at (20, 20)-(108, 108) with a black X drawn through it. |
| Payload shorter than 2 bytes | Silently ignored. Last good state is preserved.               |

Tests verify these states by sending UDP packets and inspecting the rendered
pixels.

## Concept for automated testing

### Q1.1 Tools

The dependency footprint is intentionally small. Adding more would add noise
without buying coverage.

| Tool                | Why it is here                                                      |
|---------------------|---------------------------------------------------------------------|
| `pytest`            | Fixtures, parametrisation, markers, plugin ecosystem.               |
| `PySide6`           | Already required by the application. Reusing it avoids a duplicate Qt stack and gives access to `QImage.pixelColor` for verification. |
| Standard library `socket` | Sending UDP packets is two lines. No need for a wrapper library. |

OCR was considered for verifying that the digits read "42" but rejected.
`pytesseract` adds a heavy native dependency, slows the suite, and is flaky
on small bold fonts. Pixel sampling against a known region is deterministic
and fast. The trade-off is that the suite asserts the OK state was rendered,
not that the specific digits "4" and "2" appear. Given that the application
draws digits via `QPainter.drawText` with a single code path, this is an
acceptable level of confidence for the contract under test. If digit-level
verification ever becomes a hard requirement, an OCR-based test can be added
behind a `@pytest.mark.slow` marker without changing the rest of the suite.

### Q1.2 Structure for growth

```
mct-tests/
├── app/                              # System under test, unchanged.
│   ├── main.py
│   ├── send_test.py
│   └── requirements.txt
├── tests/
│   ├── conftest.py                   # Fixtures and event-loop pump.
│   ├── helpers/
│   │   ├── udp_sender.py             # send(speed, failure), send_raw(bytes)
│   │   └── screen_capture.py         # grab(widget), count_matching(image, region, predicate)
│   ├── test_speed_display.py         # OK path acceptance test.
│   ├── test_failure_display.py       # Failure path acceptance test.
│   └── test_protocol_invariants.py   # Modulo, non-zero flag, recovery, malformed input.
├── Dockerfile
├── pytest.ini
└── requirements-test.txt
```

Three principles drive this layout:

1. **One file per visual state.** Today there are two states (digits, red box)
   and one file each. A new state means a new file, not a 500-line monolith.
2. **Helpers are composable, not opinionated.** `count_matching` takes a
   colour predicate and a region. Adding a new visual element (an icon, a
   warning border) only needs a new predicate, not a new helper module.
3. **Black-box discipline is structural.** The `app/` folder is treated as
   read-only by the test code. The only entry points are UDP packets in and
   pixels out. Tests do not import private methods or reach into widget
   internals. This keeps the suite valid even if the rendering implementation
   changes.

Extension points already in place:

- `udp_sender.send_raw(bytes)` for malformed-packet tests.
- `pytest.mark.slow` is registered in `pytest.ini` for tests that should be
  excluded from fast CI runs (for example, OCR-based or fuzz tests).
- The fixtures in `conftest.py` are scoped so additional widgets, ports, or
  protocol variants can be added without restructuring existing tests.

### Q1.3 Running headless in Docker

Qt applications normally need a display server. Two ways to remove that
requirement:

1. **`QT_QPA_PLATFORM=offscreen`** (used here). Qt ships an offscreen platform
   plugin that renders widgets to memory. No X server, no virtual framebuffer
   process, no DISPLAY environment variable. Just an environment variable.
2. **`xvfb-run pytest`** (alternative). Xvfb is a virtual X server that draws
   to memory instead of a screen. Slightly more moving parts because it spawns
   a separate process, but useful if a future test needs platform features
   that the offscreen plugin does not implement (clipboard, drag-and-drop,
   real font hinting).

The Dockerfile uses the offscreen approach. It is set as an environment
variable at image build time, so `pytest` runs headless without any extra
flags. The base image is `python:3.12-slim` plus the minimum set of system
libraries Qt loads at startup (`libgl1`, `libegl1`, `libxkbcommon0`,
`libdbus-1-3`, `libfontconfig1`, `libfreetype6`).

## Test design notes

### App lifecycle

`SpeedWindow` is instantiated in-process inside the test, not spawned as a
subprocess. This is faster (no process startup per test), deterministic (the
QApplication event loop is driven explicitly by the test), and still
black-box because the public contract (UDP in, pixels out) is the only
surface the tests touch.

### Event-loop pumping

UDP delivery on localhost is fast but not synchronous. After sending a packet,
the test calls `pump()`, which spins the QApplication event loop for up to
200 ms and processes any pending events (`readyRead`, `paintEvent`). Tests
finish well within that budget; the bound exists to fail fast if the
application stops responding.

### Verification

Pixel sampling instead of OCR or image diff. Two predicates do most of the
work: `is_white` (R, G, B all above 200) and `is_red` (R high, R minus G and
R minus B both above 100). Region-of-interest counts are then asserted
against thresholds chosen with margin, not against exact pixel counts.
This tolerates anti-aliasing and font-hinting differences across platforms.

## What is not covered, and why

A few things were considered and explicitly left out.

- **Image-diff testing against a reference PNG.** Brittle across platforms
  because of font rendering. Adds a maintenance burden whenever the
  application's appearance changes.
- **Mocking the UDP socket.** The application opens a real socket; mocking
  would force the tests to bypass that, which weakens the integration story.
- **Stress and fuzz testing.** Worth doing eventually; the suite has the
  hooks (`send_raw`, the `slow` marker) but the work is out of scope for
  this exercise.
- **CI configuration files.** The Dockerfile is enough to demonstrate the
  approach. A real GitHub Actions or GitLab CI file would just call
  `docker build` and `docker run`.

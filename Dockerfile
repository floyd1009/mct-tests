FROM python:3.12-slim

# Qt's offscreen platform plugin still needs a small set of system
# libraries to load, even though it never opens a display. These are
# the minimum required for PySide6 widgets to render to memory.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libegl1 \
    libglib2.0-0 \
    libxkbcommon0 \
    libdbus-1-3 \
    libfontconfig1 \
    libfreetype6 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt

COPY app/ ./app/
COPY tests/ ./tests/
COPY pytest.ini .

# Render Qt widgets to memory instead of a display server. This is the
# simplest way to run GUI tests in CI; an alternative is xvfb-run, which
# spawns a virtual X server.
ENV QT_QPA_PLATFORM=offscreen

CMD ["pytest"]

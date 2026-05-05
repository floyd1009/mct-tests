FROM python:3.12-slim

# System libraries:
#   - Xvfb provides a virtual X display so the application has somewhere
#     to render. The test process captures pixels from this display.
#   - The libxcb-* and libxkbcommon-x11-0 packages are Qt's runtime
#     dependencies for the xcb platform plugin.
#   - libgssapi-krb5-2 is loaded dynamically by Qt's network module.
#   - The remaining libraries are baseline OpenGL, fonts, and DBus.
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    xauth \
    tesseract-ocr \
    libgl1 \
    libegl1 \
    libglib2.0-0 \
    libdbus-1-3 \
    libfontconfig1 \
    libfreetype6 \
    libgssapi-krb5-2 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-sync1 \
    libxcb-xfixes0 \
    libxcb-xkb1 \
    libx11-xcb1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt

COPY app/ ./app/
COPY tests/ ./tests/
COPY pytest.ini .

# Run pytest under xvfb-run so the application has a virtual X display
# to render into. The screen size is set generously so the 128x128
# window is rendered with margin to spare.
CMD ["xvfb-run", "-a", "--server-args=-screen 0 400x400x24", "pytest"]

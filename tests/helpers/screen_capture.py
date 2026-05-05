"""Screen capture helpers.

Pixels are captured from the host display via mss. The display is the
real screen (locally) or the Xvfb virtual display (in the container).
The application's 128x128 window is the only thing rendered on that
display in either case, so we capture the full frame and either count
pixels matching colour predicates or run OCR on the full frame.
"""

import mss
import numpy as np
import pytesseract
from PIL import Image


def capture_display() -> np.ndarray:
    """Capture the full primary display.

    Returns a numpy array of shape (height, width, 4) in BGRA order,
    matching what mss returns directly.
    """
    with mss.MSS() as sct:
        monitor = sct.monitors[1]  # index 0 is "all monitors", 1 is primary
        raw = sct.grab(monitor)
        return np.array(raw)


def read_digits(image: np.ndarray) -> str:
    """Run OCR on the captured frame and return whatever digits it sees.

    Uses Tesseract in single-line mode with a digits-only character
    whitelist, since the application only ever renders two zero-padded
    digits in the OK state.
    """
    rgb = image[:, :, [2, 1, 0]]  # BGRA -> RGB
    pil_image = Image.fromarray(rgb)
    text = pytesseract.image_to_string(
        pil_image,
        config="--psm 7 -c tessedit_char_whitelist=0123456789",
    )
    return text.strip()


def count_red_pixels(image: np.ndarray, dominance: int = 80) -> int:
    """Count red-dominant pixels in the image.

    A pixel counts as red when the red channel is high and clearly
    exceeds both green and blue by `dominance`. This rejects the black
    pixels of the failure-state X drawn through the red box.
    """
    b = image[:, :, 0].astype(int)
    g = image[:, :, 1].astype(int)
    r = image[:, :, 2].astype(int)
    mask = (r >= 150) & ((r - g) >= dominance) & ((r - b) >= dominance)
    return int(mask.sum())


def count_white_pixels(image: np.ndarray, threshold: int = 200) -> int:
    """Count near-white pixels in the image."""
    b = image[:, :, 0]
    g = image[:, :, 1]
    r = image[:, :, 2]
    mask = (r >= threshold) & (g >= threshold) & (b >= threshold)
    return int(mask.sum())

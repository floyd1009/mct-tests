"""Grab a widget's rendered output and inspect pixel regions.

We deliberately avoid OCR. The application has only two visual states
(centered digits, or red square with a black X), and both can be verified
by counting pixels matching a colour predicate in a region of interest.
This is faster than OCR, has no native dependencies, and is deterministic.
"""

from typing import Callable, Tuple

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QWidget


Region = Tuple[int, int, int, int]  # (x, y, width, height)
Rgb = Tuple[int, int, int]
Predicate = Callable[[Rgb], bool]


def grab(widget: QWidget) -> QImage:
    """Render the widget into a QImage."""
    widget.repaint()
    return widget.grab().toImage()


def count_matching(image: QImage, region: Region, predicate: Predicate) -> int:
    """Count pixels in `region` whose colour matches `predicate`."""
    x, y, w, h = region
    count = 0
    for j in range(y, y + h):
        for i in range(x, x + w):
            color = image.pixelColor(i, j)
            if predicate((color.red(), color.green(), color.blue())):
                count += 1
    return count


def is_white(rgb: Rgb, threshold: int = 200) -> bool:
    r, g, b = rgb
    return r >= threshold and g >= threshold and b >= threshold


def is_red(rgb: Rgb, dominance: int = 100) -> bool:
    """True for clearly red-dominant pixels.

    `dominance` is the minimum gap between the red channel and each of
    green and blue. This rejects washed-out reds and pure black pixels
    from the failure-state X.
    """
    r, g, b = rgb
    return r >= 150 and (r - g) >= dominance and (r - b) >= dominance


def is_black(rgb: Rgb, threshold: int = 40) -> bool:
    r, g, b = rgb
    return r <= threshold and g <= threshold and b <= threshold

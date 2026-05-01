import atexit
import ctypes
from ctypes import wintypes
from dataclasses import dataclass

import cv2
import numpy

from .r_client import get_geometry, get_roblox_hwnd
from .r_input import Click, RightClick

# dlls
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# cache
cached_images = {}
cached_sregion = {}


screen_bitmap = None
old_bitmap = None


# classes
@dataclass
class Box:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> tuple[int, int]:
        """
        Get the center point of the box.

        Returns:
            tuple[int, int]:
                The (x, y) center coordinate of the box.
        """
        return (self.x + self.w // 2, self.y + self.h // 2)

    @property
    def top_left(self) -> tuple[int, int]:
        """
        Get the top-left corner of the box.

        Returns:
            tuple[int, int]:
                The (x, y) coordinate of the top-left corner.
        """
        return (self.x, self.y)

    @property
    def bottom_right(self) -> tuple[int, int]:
        """
        Get the bottom-right corner of the box.

        Returns:
            tuple[int, int]:
                The (x, y) coordinate of the bottom-right corner.
        """
        return (self.x + self.w, self.y + self.h)

    def as_tuple(self) -> tuple[int, int, int, int]:
        """
        Convert the box into a tuple.

        Returns:
            tuple[int, int, int, int]:
                The box as (x, y, w, h).
        """
        return (self.x, self.y, self.w, self.h)


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


# funcs
def imageExists(
    path: str,
    confidence: float,
    grayscale: bool | None = None,
    threshold: tuple[int, int] | None = None,
    region: tuple[int, int, int, int] | None = None,
    matchTemplate: int = cv2.TM_CCOEFF_NORMED,
) -> bool:
    """
    Check whether a template image exists within the Roblox window or a
    specified region of it.

    Args:
        path (str):
            File path to the template image.
        confidence (float):
            Minimum template match confidence required for a successful match.
        grayscale (bool | None):
            Whether to convert both images to grayscale before matching.
            Defaults to True when None is provided.
        threshold (tuple[int, int] | None):
            Optional binary threshold as (threshold_value, max_value).
            Defaults to (0, 255), which disables thresholding.
        region (tuple[int, int, int, int] | None):
            Optional search region relative to the Roblox window in
            (x, y, w, h) format. If None, the full Roblox window is used.
        matchTemplate (int):
            OpenCV template matching method. Defaults to cv2.TM_CCOEFF_NORMED.

    Returns:
        bool:
            True if the image is found at or above the given confidence,
            otherwise False.

    Notes:
        Template images are cached after first load to reduce disk reads and
        improve repeated search performance.
    """
    grayscale = True if grayscale is None else grayscale
    threshold = threshold or (0, 255)

    rect = get_geometry(get_roblox_hwnd())
    region = (
        (rect.x, rect.y, rect.w + rect.x, rect.h + rect.y)
        if region is None
        else (
            rect.x + region[0],
            rect.y + region[1],
            rect.x + region[0] + region[2],
            rect.y + region[1] + region[3],
        )
    )
    template = cached_images.get(path)

    if template is None:
        template_cv2 = cv2.imread(path)
        cached_images[path] = template_cv2
        template = template_cv2

    template = template.copy()

    comparison_cv2 = captureRegion(region=(region[0], region[1], region[2], region[3]))
    h_img, w_img = comparison_cv2.shape[:2]
    h_temp, w_temp = template.shape[:2]

    if w_img < w_temp or h_img < h_temp:
        return False
    if grayscale:
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        comparison_cv2 = cv2.cvtColor(comparison_cv2, cv2.COLOR_BGR2GRAY)

    if threshold != (0, 255):
        _, template = cv2.threshold(
            template, threshold[0], threshold[1], cv2.THRESH_BINARY_INV
        )
        _, comparison_cv2 = cv2.threshold(
            comparison_cv2, threshold[0], threshold[1], cv2.THRESH_BINARY_INV
        )

    result = cv2.matchTemplate(
        image=comparison_cv2, templ=template, method=matchTemplate
    )
    _, max_val, _, _ = cv2.minMaxLoc(result)
    if max_val >= confidence:
        return True
    return False


def imageLocation(
    path: str,
    confidence: float,
    grayscale: bool | None = None,
    threshold: tuple[int, int] | None = None,
    region: tuple[int, int, int, int] | None = None,
    matchTemplate: int = cv2.TM_CCOEFF_NORMED,
) -> Box | None:
    """
    Find the location of a template image within the Roblox window or a
    specified region of it.

    Args:
        path (str):
            File path to the template image.
        confidence (float):
            Minimum template match confidence required for a successful match.
        grayscale (bool | None):
            Whether to convert both images to grayscale before matching.
            Defaults to True when None is provided.
        threshold (tuple[int, int] | None):
            Optional binary threshold as (threshold_value, max_value).
            Defaults to (0, 255), which disables thresholding.
        region (tuple[int, int, int, int] | None):
            Optional search region relative to the Roblox window in
            (x, y, w, h) format. If None, the full Roblox window is used.
        matchTemplate (int):
            OpenCV template matching method. Defaults to cv2.TM_CCOEFF_NORMED.

    Returns:
        Box | None:
            A Box representing the matched image location if found at or above
            the given confidence, otherwise None.

    Notes:
        Template images are cached after first load to reduce disk reads and
        improve repeated search performance.
    """
    grayscale = True if grayscale is None else grayscale
    threshold = threshold or (0, 255)
    rect = get_geometry(get_roblox_hwnd())
    region = (
        (rect.x, rect.y, rect.w + rect.x, rect.h + rect.y)
        if region is None
        else (
            rect.x + region[0],
            rect.y + region[1],
            rect.x + region[0] + region[2],
            rect.y + region[1] + region[3],
        )
    )
    template = cached_images.get(path)
    if template is None:
        template_cv2 = cv2.imread(path)
        cached_images[path] = template_cv2
        template = template_cv2

    template = template.copy()

    comparison_cv2 = captureRegion(region=(region[0], region[1], region[2], region[3]))
    h_img, w_img = comparison_cv2.shape[:2]
    h_temp, w_temp = template.shape[:2]

    if w_img < w_temp or h_img < h_temp:
        return False
    if grayscale:
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        comparison_cv2 = cv2.cvtColor(comparison_cv2, cv2.COLOR_BGR2GRAY)

    if threshold != (0, 255):
        _, template = cv2.threshold(
            template, threshold[0], threshold[1], cv2.THRESH_BINARY_INV
        )
        _, comparison_cv2 = cv2.threshold(
            comparison_cv2, threshold[0], threshold[1], cv2.THRESH_BINARY_INV
        )

    result = cv2.matchTemplate(
        image=comparison_cv2, templ=template, method=matchTemplate
    )
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= confidence:
        geometry = list((*max_loc, *template.shape[:2]))
        # swap h,w so its x,y,w,h
        geometry[2] = geometry[2] ^ geometry[3]
        geometry[3] = geometry[2] ^ geometry[3]
        geometry[2] = geometry[2] ^ geometry[3]
        return Box(*geometry)
    return None


def clickImage(
    click: int,
    delay: float,
    path: str,
    confidence: float,
    grayscale: bool | None = None,
    threshold: tuple[int, int] | None = None,
    region: tuple[int, int, int, int] | None = None,
    matchTemplate: int = cv2.TM_CCOEFF_NORMED,
) -> bool:
    """
    Locate a template image and click its center point.

    Args:
        click (int):
            Click type selector. Use 0 for left click, any other value for
            right click.
        delay (float):
            Delay to pass into the click function.
        path (str):
            File path to the template image.
        confidence (float):
            Minimum template match confidence required for a successful match.
        grayscale (bool | None):
            Whether to convert both images to grayscale before matching.
            Defaults to True when None is provided.
        threshold (tuple[int, int] | None):
            Optional binary threshold as (threshold_value, max_value).
            Defaults to (0, 255), which disables thresholding.
        region (tuple[int, int, int, int] | None):
            Optional search region relative to the Roblox window in
            (x, y, w, h) format. If None, the full Roblox window is used.
        matchTemplate (int):
            OpenCV template matching method. Defaults to cv2.TM_CCOEFF_NORMED.

    Returns:
        bool:
            True if the image was found and clicked successfully, otherwise False.
    """
    result = imageLocation(
        path=path,
        confidence=confidence,
        grayscale=grayscale,
        threshold=threshold,
        region=region,
        matchTemplate=matchTemplate,
    )
    if result is None:
        return False
    result = result.center
    if click == 0:
        Click(x=result[0], y=result[1], delay=delay)
    else:
        RightClick(x=result[0], y=result[1], delay=delay)
    return True


def pixel(x: int, y: int, relative=True) -> tuple[int, int, int]:
    sdc = user32.GetDC(0)
    """
    Get the RGB color of a pixel within the Roblox window.

    Args:
        x (int):
            X-coordinate
        y (int):
            Y-coordinate
        relative (bool):
            Whether the provided coordinates are relative to the Roblox window.

    Returns:
        tuple[int, int, int]:
            The pixel color as (r, g, b).

    Notes:
        Coordinates are automatically offset relative to the Roblox window's
        top-left corner.
    """
    if relative:
        rect = get_geometry(get_roblox_hwnd())
        x += rect.x
        y += rect.y
    color = gdi32.GetPixel(sdc, x, y)
    rgbRed = 0x000000FF
    rgbGreen = 0x0000FF00
    rgbBlue = 0x00FF0000
    r = color & rgbRed
    g = (color & rgbGreen) >> 8
    b = (color & rgbBlue) >> 16
    user32.ReleaseDC(0, sdc)
    return (r, g, b)


def pixelMatchesColor(
    x: int, y: int, expectedRGB: tuple[int, int, int], tolerance: int = 0
) -> bool:
    """
    Check whether a pixel within the Roblox window matches an expected RGB
    color within a given tolerance.

    Args:
        x (int):
            X-coordinate relative to the Roblox window.
        y (int):
            Y-coordinate relative to the Roblox window.
        expectedRGB (tuple[int, int, int]):
            The expected color as (r, g, b).
        tolerance (int):
            Allowed deviation per color channel. Defaults to 0.

    Returns:
        bool:
            True if the pixel matches within tolerance, otherwise False.
    """
    r, g, b = pixel(x, y)
    return all(
        [
            r >= expectedRGB[0] - tolerance and r <= expectedRGB[0] + tolerance,
            g >= expectedRGB[1] - tolerance and g <= expectedRGB[1] + tolerance,
            b >= expectedRGB[2] - tolerance and b <= expectedRGB[2] + tolerance,
        ]
    )


def captureRegion(region: tuple[int, int, int, int]) -> numpy.ndarray:
    sdc = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(sdc)

    global screen_bitmap, old_bitmap

    width = region[2] - region[0]
    height = region[3] - region[1]

    if len(cached_sregion) == 0:
        screen_bitmap = gdi32.CreateCompatibleBitmap(sdc, width, height)
        old_bitmap = gdi32.SelectObject(hdc_mem, screen_bitmap)
        cached_sregion["region"] = region

    else:
        if (
            cached_sregion["region"][2] != region[2]
            or cached_sregion["region"][3] != region[3]
        ):
            gdi32.SelectObject(hdc_mem, old_bitmap)
            gdi32.DeleteObject(screen_bitmap)

            screen_bitmap = gdi32.CreateCompatibleBitmap(sdc, width, height)
            old_bitmap = gdi32.SelectObject(hdc_mem, screen_bitmap)

            cached_sregion["region"] = region
        else:
            gdi32.SelectObject(hdc_mem, screen_bitmap)

    # Capture
    gdi32.BitBlt(hdc_mem, 0, 0, width, height, sdc, region[0], region[1], 0x00CC0020)

    # Prepare buffer
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buffer = ctypes.create_string_buffer(width * height * 4)
    gdi32.GetDIBits(hdc_mem, screen_bitmap, 0, height, buffer, ctypes.byref(bmi), 0)

    arr = numpy.frombuffer(buffer, dtype=numpy.uint8).reshape((height, width, 4))[
        :, :, :3
    ]

    user32.ReleaseDC(0, sdc)
    gdi32.DeleteDC(hdc_mem)

    return arr


def pixelInRegion(
    pixelColor: tuple[int, int, int],
    region: tuple[int, int, int, int],
    tolerance: int = 0,
) -> tuple[bool, int, int]:
    """
    Check whether a pixel of a specific RGB color exists within a given region
    of the Roblox window.

    Args:
        pixelColor (tuple[int, int, int]):
            The expected color as (r, g, b).
        region (tuple[int, int, int, int]):
            The search region relative to the Roblox window in (x, y, w, h) format.
        tolerance (int):
            Allowed deviation per color channel. Defaults to 0.

    Returns:
        tuple[bool, int, int]:
            A tuple containing a boolean indicating if a matching pixel is found,
            and the coordinates (x, y) of the first matching pixel, or (-1, -1) if none is found.
    """
    rect = get_geometry(get_roblox_hwnd())
    comparison_bgr = captureRegion(
        region=(
            rect.x + region[0],
            rect.y + region[1],
            rect.x + region[0] + region[2],
            rect.y + region[1] + region[3],
        )
    )
    for y in range(comparison_bgr.shape[0]):
        for x in range(comparison_bgr.shape[1]):
            b, g, r = comparison_bgr[y, x]
            if all(
                [
                    r >= pixelColor[0] - tolerance and r <= pixelColor[0] + tolerance,
                    g >= pixelColor[1] - tolerance and g <= pixelColor[1] + tolerance,
                    b >= pixelColor[2] - tolerance and b <= pixelColor[2] + tolerance,
                ]
            ):
                return (True, region[0] + x, region[1] + y)
    return (False, -1, -1)


def allPixelsInRegion(
    pixelColor: tuple[int, int, int],
    region: tuple[int, int, int, int],
    tolerance: int = 0,
) -> list[tuple[int, int]]:
    """
    Find all pixels of a specific RGB color within a given region of the Roblox

    Args:
        pixelColor (tuple[int, int, int]):
            The expected color as (r, g, b).
        region (tuple[int, int, int, int]):
            The search region relative to the Roblox window in (x, y, w, h) format.
        tolerance (int):
            Allowed deviation per color channel. Defaults to 0.

    Returns:
        list[tuple[int, int]]:
            A list of coordinates (x, y) of all matching pixels, or an empty list if none are found.
    """
    pixels = []
    rect = get_geometry(get_roblox_hwnd())
    comparison_bgr = captureRegion(
        region=(
            rect.x + region[0],
            rect.y + region[1],
            rect.x + region[0] + region[2],
            rect.y + region[1] + region[3],
        )
    )
    for y in range(comparison_bgr.shape[0]):
        for x in range(comparison_bgr.shape[1]):
            b, g, r = comparison_bgr[y, x]
            if all(
                [
                    r >= pixelColor[0] - tolerance and r <= pixelColor[0] + tolerance,
                    g >= pixelColor[1] - tolerance and g <= pixelColor[1] + tolerance,
                    b >= pixelColor[2] - tolerance and b <= pixelColor[2] + tolerance,
                ]
            ):
                pixels.append((region[0] + x, region[1] + y))
    return pixels

from PIL import Image
from config import PALETTE


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


_PALETTE_RGB: list[tuple[int, int, int]] = [hex_to_rgb(c) for c in PALETTE]


def nearest_color(r: int, g: int, b: int) -> str:
    """Return the palette hex string closest to (r, g, b) by Euclidean distance."""
    best_hex, best_dist = PALETTE[0], float("inf")
    for i, (pr, pg, pb) in enumerate(_PALETTE_RGB):
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < best_dist:
            best_dist, best_hex = d, PALETTE[i]
    return best_hex


def load_target(path: str, w: int, h: int) -> dict[tuple[int, int], str]:
    """Load a PNG, resize to (w, h), and quantize each pixel to the 8-color palette.

    Returns a dict mapping (x, y) -> hex_color string.
    """
    img = Image.open(path).convert("RGB").resize((w, h), Image.LANCZOS)
    pixels: dict[tuple[int, int], str] = {}
    for y in range(h):
        for x in range(w):
            r, g, b = img.getpixel((x, y))
            pixels[(x, y)] = nearest_color(r, g, b)
    return pixels

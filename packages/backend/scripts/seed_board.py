"""
Seed the PolyPlace board from an image.

Writes straight to the `pixels` table in bulk, then invalidates the Redis
board cache. Deliberately bypasses the WebSocket layer: the rate limiters
live in `handle_place`, not in `place_pixel`, so seeding is an operator
action rather than gameplay and is not throttled.

Run from packages/backend/ so that `app.*` imports resolve.

    uv run python scripts/seed_board.py art/logo.png --dry-run
    uv run python scripts/seed_board.py art/logo.png --clear
    uv run python scripts/seed_board.py art/logo.png --width 120 --at 200,180

See SEEDING.md for the full walkthrough.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from PIL import Image
from sqlalchemy import delete, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import get_settings
from app.core.redis import redis_client
from app.db.models.pixel import Pixel
from app.db.session import AsyncSessionLocal
from app.services.board_service import BOARD_CACHE_KEY

settings = get_settings()

# r/place-style 32 colour palette, used when --palette is not given.
# Replace this with whatever palette your frontend actually offers: seeding
# colours the client cannot reproduce makes the board look subtly broken as
# soon as real users paint over it.
DEFAULT_PALETTE = [
    "#6D001A", "#BE0039", "#FF4500", "#FFA800", "#FFD635", "#FFF8B8",
    "#00A368", "#00CC78", "#7EED56", "#00756F", "#009EAA", "#00CCC0",
    "#2450A4", "#3690EA", "#51E9F4", "#493AC1", "#6A5CFF", "#94B3FF",
    "#811E9F", "#B44AC0", "#E4ABFF", "#DE107F", "#FF3881", "#FF99AA",
    "#6D482F", "#9C6926", "#FFB470", "#000000", "#515252", "#898D90",
    "#D4D7D9", "#FFFFFF",
]

CHUNK = 5000

RESAMPLE = {
    "nearest": Image.Resampling.NEAREST,
    "lanczos": Image.Resampling.LANCZOS,
}


# --------------------------------------------------------------------------
# image -> rows
# --------------------------------------------------------------------------

def hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    if len(v) != 6:
        raise ValueError(f"bad hex colour: {value!r}")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def load_palette(path: str | None) -> list[str]:
    if path is None:
        return DEFAULT_PALETTE
    data = json.loads(Path(path).read_text())
    if not isinstance(data, list) or not data:
        raise ValueError("--palette must be a JSON array of hex strings")
    palette = [str(c).upper() for c in data]
    for c in palette:
        hex_to_rgb(c)  # validate early
    return palette


def build_palette_image(palette: list[str]) -> tuple[Image.Image, list[str]]:
    """
    Pillow needs a 256-entry palette. Repeating the real colours to fill the
    unused slots means every index quantize() can return maps back to a real
    colour, so there is no index-out-of-range or accidental-black case.
    """
    full = (palette * (256 // len(palette) + 1))[:256]
    flat: list[int] = []
    for colour in full:
        flat.extend(hex_to_rgb(colour))
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette(flat)
    return pal_img, full


def image_to_rows(
    path: str,
    target_w: int,
    target_h: int,
    origin_x: int,
    origin_y: int,
    palette: list[str],
    resample: str,
    dither: bool,
    skip_transparent: bool,
    owner: str | None,
) -> tuple[list[dict], Image.Image]:
    img = Image.open(path).convert("RGBA")
    img = img.resize((target_w, target_h), RESAMPLE[resample])

    alpha = img.getchannel("A")
    pal_img, index_to_hex = build_palette_image(palette)
    quantized = img.convert("RGB").quantize(
        palette=pal_img,
        dither=Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE,
    )

    idx = quantized.load()
    a = alpha.load()

    rows: list[dict] = []
    preview = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    pv = preview.load()

    for y in range(target_h):
        board_y = origin_y + y
        in_y = 0 <= board_y < settings.board_height
        for x in range(target_w):
            if skip_transparent and a[x, y] < 128:
                continue
            colour = index_to_hex[idx[x, y]]
            pv[x, y] = hex_to_rgb(colour)

            board_x = origin_x + x
            if in_y and 0 <= board_x < settings.board_width:
                rows.append(
                    {"x": board_x, "y": board_y, "color": colour, "userid": owner}
                )

    return rows, preview


# --------------------------------------------------------------------------
# rows -> database
# --------------------------------------------------------------------------

async def write_rows(rows: list[dict], clear: bool) -> None:
    stmt = pg_insert(Pixel)
    stmt = stmt.on_conflict_do_update(
        index_elements=["x", "y"],
        set_={
            "color": stmt.excluded.color,
            "userid": stmt.excluded.userid,
            "updated_at": func.now(),
        },
    )

    async with AsyncSessionLocal() as session:
        if clear:
            result = await session.execute(delete(Pixel))
            print(f"cleared {result.rowcount} existing pixels")

        for i in range(0, len(rows), CHUNK):
            await session.execute(stmt, rows[i : i + CHUNK])
            done = min(i + CHUNK, len(rows))
            print(f"  writing {done:>7} / {len(rows)}", end="\r", flush=True)

        await session.commit()

    print(f"\nwrote {len(rows)} pixels")

    # Patching the cached JSON here would mean a linear scan per pixel.
    # Dropping the key is O(1) and the next get_board_state() rebuilds it.
    await redis_client.delete(BOARD_CACHE_KEY)
    print("board cache invalidated")


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------

def parse_at(value: str) -> tuple[int, int]:
    try:
        x, y = value.split(",")
        return int(x), int(y)
    except ValueError:
        raise argparse.ArgumentTypeError("--at expects X,Y (for example 170,170)")


def resolve_size(args, board_w: int, board_h: int) -> tuple[int, int]:
    if args.width and args.height:
        return args.width, args.height
    with Image.open(args.image) as src:
        ratio = src.height / src.width
    if args.width:
        return args.width, max(1, round(args.width * ratio))
    if args.height:
        return max(1, round(args.height / ratio)), args.height
    return board_w, board_h


async def main() -> int:
    p = argparse.ArgumentParser(
        description="Seed the PolyPlace board from an image.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("image", help="path to a PNG/JPG source image")
    p.add_argument("--width", type=int, help="target width; height follows aspect ratio")
    p.add_argument("--height", type=int, help="target height; width follows aspect ratio")
    p.add_argument("--at", type=parse_at, default=(0, 0), metavar="X,Y",
                   help="board coordinate of the image's top-left corner")
    p.add_argument("--owner", default=None,
                   help="userid to attribute the pixels to (default: unowned)")
    p.add_argument("--palette", default=None,
                   help="JSON file containing an array of hex colours")
    p.add_argument("--resample", choices=list(RESAMPLE), default="lanczos",
                   help="lanczos for photos, nearest for pixel art (default: lanczos)")
    p.add_argument("--dither", action="store_true",
                   help="Floyd-Steinberg dithering; better gradients, noisier look")
    p.add_argument("--keep-transparent", action="store_true",
                   help="paint transparent areas instead of leaving them untouched")
    p.add_argument("--clear", action="store_true",
                   help="delete every existing pixel before writing")
    p.add_argument("--dry-run", action="store_true",
                   help="do not touch the database")
    p.add_argument("--preview", default=None, metavar="PATH",
                   help="write a PNG of the quantized result for inspection")
    args = p.parse_args()

    if not Path(args.image).exists():
        print(f"no such file: {args.image}", file=sys.stderr)
        return 1

    palette = load_palette(args.palette)
    w, h = resolve_size(args, settings.board_width, settings.board_height)

    rows, preview = image_to_rows(
        path=args.image,
        target_w=w,
        target_h=h,
        origin_x=args.at[0],
        origin_y=args.at[1],
        palette=palette,
        resample=args.resample,
        dither=args.dither,
        skip_transparent=not args.keep_transparent,
        owner=args.owner,
    )

    print(f"board      {settings.board_width}x{settings.board_height}")
    print(f"image      {args.image} -> {w}x{h} at {args.at}")
    print(f"palette    {len(palette)} colours ({args.resample}"
          f"{', dithered' if args.dither else ''})")
    print(f"pixels     {len(rows)}")

    if args.preview:
        scale = max(1, 512 // max(w, h))
        preview.resize((w * scale, h * scale), Image.Resampling.NEAREST).save(args.preview)
        print(f"preview    {args.preview}")

    if not rows:
        print("\nnothing to write - check --at and --width against the board size")
        return 1

    if args.dry_run:
        print("\ndry run, database untouched")
        return 0

    await write_rows(rows, clear=args.clear)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
import asyncio
import json
import random
import requests
import websockets
from websockets.exceptions import ConnectionClosed

from config import CANVAS_W, CANVAS_H, RATE_LIMIT_PIXELS, RATE_LIMIT_WINDOW_SEC
from src.image_utils import load_target


class Bot:
    def __init__(self, cfg: dict, auth_url: str, ws_url: str) -> None:
        self.name = cfg["name"]
        self.username = cfg["username"]
        self.password = cfg["password"]
        self.email = cfg["email"]
        self.image_path = cfg["image"]
        self.auth_url = auth_url
        self.ws_url = ws_url

        self.token: str | None = None
        self.canvas: dict[tuple[int, int], str] = {}   # live canvas state
        self.target: dict[tuple[int, int], str] = {}   # desired pixel state

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def register_or_login(self) -> None:
        requests.post(
            f"{self.auth_url}/register",
            json={"username": self.username, "password": self.password, "email": self.email},
        )
        # Whether registration succeeded or the account already exists, log in.
        resp = requests.post(
            f"{self.auth_url}/login",
            json={"username": self.username, "password": self.password},
        )
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"[{self.name}] login failed: {data}")
        self.token = data["token"]
        print(f"[{self.name}] authenticated")

    # ------------------------------------------------------------------
    # Pixel strategy
    # ------------------------------------------------------------------

    def get_priority_pixels(self, n: int) -> list[tuple[int, int, str]]:
        """Return up to *n* (x, y, color) tuples to place this window.

        Tier 1 — opponent pixels: canvas has a color that differs from our target.
        Tier 2 — unset pixels: canvas has no color where we need one.
        Both tiers are shuffled so bots spread coverage rather than clustering.
        """
        tier1: list[tuple[int, int, str]] = []
        tier2: list[tuple[int, int, str]] = []

        for (x, y), want in self.target.items():
            have = self.canvas.get((x, y))
            if have == want:
                continue
            if have is not None:
                tier1.append((x, y, want))   # opponent's pixel — highest priority
            else:
                tier2.append((x, y, want))   # empty slot

        random.shuffle(tier1)
        random.shuffle(tier2)
        return (tier1 + tier2)[:n]

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    async def run(self, start_delay: float = 0) -> None:
        self.register_or_login()
        self.target = load_target(self.image_path, CANVAS_W, CANVAS_H)
        print(f"[{self.name}] target image loaded ({len(self.target)} pixels)")

        if start_delay:
            await asyncio.sleep(start_delay)

        while True:
            try:
                await self._connect_and_play()
            except (ConnectionClosed, OSError) as exc:
                print(f"[{self.name}] connection lost ({exc}), reconnecting in 10s")
                await asyncio.sleep(10)
            except Exception as exc:
                print(f"[{self.name}] unexpected error: {exc}, reconnecting in 10s")
                await asyncio.sleep(10)

    # ------------------------------------------------------------------
    # WebSocket session
    # ------------------------------------------------------------------

    async def _connect_and_play(self) -> None:
        uri = f"{self.ws_url}/?token={self.token}"
        async with websockets.connect(uri, max_size=None) as ws:
            print(f"[{self.name}] connected to canvas")

            # Wait for the initial canvas state
            raw = await ws.recv()
            msg = json.loads(raw)
            if msg.get("type") == "init":
                for p in msg.get("pixels", []):
                    self.canvas[(p["x"], p["y"])] = p["color"]
                print(f"[{self.name}] canvas synced ({len(self.canvas)} pixels)")

            # Run listener and placement loop concurrently
            await asyncio.gather(
                self._listen(ws),
                self._placement_loop(ws),
            )

    async def _listen(self, ws) -> None:
        async for raw in ws:
            msg = json.loads(raw)
            if msg.get("type") == "update":
                self.canvas[(msg["x"], msg["y"])] = msg["color"]
            elif msg.get("type") == "error" and msg.get("message") == "rate_limit_exceeded":
                print(f"[{self.name}] rate limited by server — will retry next window")

    async def _placement_loop(self, ws) -> None:
        while True:
            picks = self.get_priority_pixels(RATE_LIMIT_PIXELS)
            if picks:
                print(f"[{self.name}] placing {len(picks)} pixel(s) this window")
            for x, y, color in picks:
                await ws.send(json.dumps({"type": "place", "x": x, "y": y, "color": color}))
                # await asyncio.sleep(0.2)   # brief gap to avoid flooding
            await asyncio.sleep(RATE_LIMIT_WINDOW_SEC)

import asyncio
import os

from dotenv import load_dotenv

from config import BOTS
from src.bot import Bot

load_dotenv()

AUTH_URL = os.getenv("AUTH_URL", "http://localhost:3000")
WS_URL = os.getenv("WS_URL", "ws://localhost:8765")


async def main() -> None:
    bots = [Bot(cfg, AUTH_URL, WS_URL) for cfg in BOTS]
    # Stagger each bot's start by 30 s so their 5-minute windows don't all fire
    # at the same instant, spreading canvas activity more evenly.
    tasks = [bot.run(start_delay=i * 30) for i, bot in enumerate(bots)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())

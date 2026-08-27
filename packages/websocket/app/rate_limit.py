import time


class CooldownTracker:
    """Per-userId placement cooldown. `check` is fully synchronous with no
    `await` inside its body — under asyncio's single-threaded event loop
    that makes the read-then-write on `_last_place` atomic with respect to
    other coroutines, so no lock is needed. Do not make this async or call
    anything awaitable from within it; doing so would reintroduce a race.

    Entries are keyed by userId, not by connection, and are intentionally
    never removed on disconnect so the cooldown survives reconnects/multiple
    tabs. The dict grows with the number of distinct users who have ever
    placed a pixel during this process's lifetime; that's an accepted
    limitation for a single-process deployment. If this service is ever
    horizontally scaled, this in-memory tracker would need to move to a
    shared store (e.g. Redis) since state is not shared across instances.
    """

    def __init__(self, cooldown_seconds: float) -> None:
        self.cooldown_seconds = cooldown_seconds
        self._last_place: dict[str, float] = {}

    def check(self, user_id: str) -> float | None:
        """Returns None if placement is allowed (and records now as the new
        last-placement time), otherwise the number of seconds remaining
        until the next allowed placement."""
        now = time.monotonic()
        last = self._last_place.get(user_id)
        if last is not None:
            remaining = self.cooldown_seconds - (now - last)
            if remaining > 0:
                return round(remaining, 1)
        self._last_place[user_id] = now
        return None

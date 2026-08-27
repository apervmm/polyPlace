# packages/websocket

FastAPI reimplementation of the real-time pixel-placement WebSocket server (`packages/server`). Runs as a standalone service alongside the existing Node server, against the same Neon Postgres database.

Protocol is compatible with the existing React client (`packages/client`) and the bots (`packages/bots`): same `?token=<jwt>` query-string auth, same `init`/`place`/`update` message shapes. It additionally:
- Rejects `place` from unauthenticated (no/invalid JWT) connections with a `type: "error", code: "unauthenticated"` message, instead of silently allowing guest placement.
- Enforces a per-user placement cooldown (`PLACE_COOLDOWN_SECONDS`, default 4s), rejecting early repeats with `type: "error", code: "rate_limited"`.

Guests can still connect and view the board (`init` + `update` broadcasts) — only placement is gated.

## Setup

```bash
cd packages/websocket
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt        # add requirements-dev.txt instead if you also want to run tests
cp .env.example .env                   # then fill in JWT_SECRET / DATABASE_URL (copy from packages/server/.env)
```

## Run

```bash
source .venv/bin/activate
uvicorn app.main:app --port ${WEBSOCKET_SERVER_PORT:-8766} --reload
```

- `GET /` — plain-text `OK` health check (parity with the Node service's health probe).
- `GET /health` — JSON DB-connectivity check (`{"status":"ok"}` / 503 `{"status":"degraded",...}`).
- `WS /?token=<jwt>` — the pixel-placement socket.

The Node server (port 8765, from `packages/server/.env`) and this service (port 8766 by default) can run at the same time against the same DB without conflict.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

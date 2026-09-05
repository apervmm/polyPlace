# poly/Place

A real-time, multiplayer pixel canvas inspired by r/place. Users claim pixels on a shared 540×540 board and every placement is broadcasted live to everyone connected.

***Prod:*** https://pplace.vercel.app/ 


## Stack
 
| Layer | Tech |
| --- | --- |
| Client | React 18, Vite, Canvas 2D (`createImageData`) |
| Backend | FastAPI (Python 3.13), Uvicorn, managed with `uv` |
| Database | PostgreSQL via SQLAlchemy 2.0 (async, `asyncpg`), migrations with Alembic |
| Cache / Pub-Sub | Redis |
| Auth | JWT (HS256), password hashing with bcrypt/passlib |
| Dev infra | Docker Compose |


## Architecture
 
The backend was consolidated into a **single FastAPI service** that handles both authentication and WebSocket traffic. The previous split (an Express auth server plus a separate `ws` Node server) is now legacy.


### How a pixel placement flows
 
1. Client sends `{"type": "place", "x", "y", "color"}` over the WebSocket.
2. `handle_place` rejects guests, then checks the IP and user Redis cooldowns.
3. The payload is validated against `PlaceMessage` and bounds-checked against `BOARD_WIDTH`/`BOARD_HEIGHT`.
4. `place_pixel` upserts into `pixels` (unique on `x,y`), appends an immutable row to `actions`, and patches the single pixel inside the cached board.
5. The update is **published to Redis**, not broadcast directly. Every API instance subscribes to `polyplace:updates` and re-broadcasts to its own local sockets.


### Caching
 
The full board is cached in Redis under `polyplace:board`. New connections are served from cache; only a cold cache hits Postgres. Placements patch the cached list in place.
 

### Rate limiting
 
Redis `SET NX EX` cooldown keys, currently 5s per user and 3s per IP.

 
### `packages/client` — React app
 
Vite + React. The board lives in an offscreen canvas written through `createImageData`; the visible canvas is a zoom/pan viewport (zoom 0.1×–40×) drawn from it. The socket connects with `?token=<jwt>` when logged in; without a token you can still watch the board, just not place.
 

### Legacy packages

`packages/auth` (Express) and `packages/server` (Node `ws`) are the pre-migration services. They are kept for reference only and are no longer part of the running system.
 

## API
 
Base URL in dev: `http://localhost:8000`
 
| Method | Path | Body | Returns |
| --- | --- | --- | --- |
| `GET` | `/` | — | service status |
| `GET` | `/api/v1/health` | — | `{"status": "ok"}` |
| `POST` | `/api/v1/auth/register` | `{username, email, password}` | `201` + public user |
| `POST` | `/api/v1/auth/login` | `{username, password}` | `{"token": "<jwt>"}` |
| `WS` | `/ws?token=<jwt>` | see below | live board events |
 
Interactive docs are at `http://localhost:8000/docs`.
 

### WebSocket protocol
 
**Server → client**
 
```jsonc
{ "type": "init",   "pixels": [{"x": 0, "y": 0, "color": "#ff0000"}], "userId": "..." }
{ "type": "update", "x": 12, "y": 40, "color": "#0000ff", "userId": "...", "timestamp": "..." }
{ "type": "error",  "message": "..." }
```

## Running locally
 
### Prerequisites
 
- Docker + Docker Compose (recommended path), or Python 3.13 + [uv](https://docs.astral.sh/uv/) + a local Redis
- Node 18+
- A PostgreSQL database (Supabase, Neon, or local Postgres all work)
### 1. Clone and configure
 
```bash
git clone <your-fork-url>
cd polyplace
```
 
Create `packages/backend/.env`:
 
```env
# Must use the asyncpg driver
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<db>
 
JWT_SECRET=<any long random string>
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=60
 
BOARD_WIDTH=540
BOARD_HEIGHT=540
 
CORS_ORIGINS=http://localhost:5173
 
# Use redis://redis:6379/0 when running under Docker Compose
REDIS_URL=redis://localhost:6379/0
```
 
If you're on Supabase, grab the **Transaction Pooler** connection string and swap the scheme to `postgresql+asyncpg://`.
 
### 2. Run the database migrations
 
Alembic owns the schema — do not create tables by hand.
 
```bash
cd packages/backend
uv sync
uv run alembic upgrade head
```
 
Alembic runs synchronously and rewrites the URL to `psycopg` internally, so the single `DATABASE_URL` above is all you need.
 
### 3. Start the backend
 
**With Docker Compose** (brings up the API, Redis, and RedisInsight):
 
```bash
cd packages/backend
docker compose up --build
```
 
- API → http://localhost:8000
- Docs → http://localhost:8000/docs
- RedisInsight → http://localhost:5540
**Without Docker** (needs Redis running locally):
 
```bash
cd packages/backend
uv run fastapi dev app/main.py
```
 
### 4. Start the client
 
```bash
cd packages/client
npm install
npm run dev
```
 
Opens at http://localhost:5173.
 
> The client currently points at `http://localhost:8000/api/v1/auth` and `ws://localhost:8000/ws` via constants in `src/Auth.jsx` and `src/PolyPlace.jsx`. Change those (or lift them into `import.meta.env`) when pointing at a deployed backend.
 
### Testing multi-instance broadcasting
 
`docker-compose.yml` ships a commented-out `api2` service on port 8001. Uncomment it, connect one browser to each port, and place a pixel — it should appear in both. That's the Redis pub/sub layer doing its job.
 

## Contributing
 
Contributions are welcome — bug fixes, tests, docs, features, and performance work especially.

from fastapi import WebSocket


def get_client_ip(websocket: WebSocket) -> str | None:
    forwarded = websocket.headers.get("x-forwarded-for")
    if forwarded:
        # Left-most entry is the original client; the rest are proxy hops.
        return forwarded.split(",")[0].strip()
    return websocket.client.host if websocket.client else None
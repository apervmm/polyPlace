from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.services.board_service import get_board_state
from app.ws.connection_manager import manager
from app.ws.handlers import handle_place

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    user_id = decode_access_token(token) if token else None

    await manager.connect(websocket)

    async with AsyncSessionLocal() as session:
        pixels = await get_board_state(session)
        await websocket.send_json({
            "type": "init",
            "pixels": [p.model_dump() for p in pixels],
            "userId": user_id,
        })

        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "place":
                    await handle_place(session, data, user_id)
        except WebSocketDisconnect:
            manager.disconnect(websocket)
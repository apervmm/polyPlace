import asyncio
import websockets
import json
import ably
import os
from dotenv import load_dotenv

load_dotenv()


ABLY_API = os.getenv('ABLY_API_KEY')
ably_client = ably.AblyRest(ABLY_API)
channel = ably_client.channels.get("polyplace")

GRID_SIZE = 100
DEFAULT_COLOR = "white"
grid = [DEFAULT_COLOR] * (GRID_SIZE * GRID_SIZE)

clients = set()

async def broadcast(index, color):
    message = json.dumps({"type": "update", "index": index, "color": color})
    await asyncio.gather(*(client.send(message) for client in clients))

async def publish(index, color):
    print(f"index={index}, color={color}")
    await channel.publish("update", {"index": index, "color": color}) 


async def websocket_handler(websocket):
    clients.add(websocket)

    try:
        await websocket.send(json.dumps({"type": "grid", "data": grid}))
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "place":
                
                index = data["index"]
                color = data["color"]

                x = index % GRID_SIZE
                y = index // GRID_SIZE

                if 0 <= index < len(grid):
                    grid[index] = color 
                    asyncio.create_task(broadcast(index, color))
                    asyncio.create_task(publish(index, color)) 

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)



async def start():
    server = await websockets.serve(websocket_handler, "0.0.0.0", 8765)
    print("Running on port 8765")
    await server.wait_closed()


def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())


if __name__ == "__main__":
    run()

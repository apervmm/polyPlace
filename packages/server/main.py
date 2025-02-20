import json
import threading
import socketserver
import http.server
import websockets
import asyncio

# Constants
GRID_SIZE = 100
DEFAULT_COLOR = "white"
PORT = 8000
WS_PORT = 8765

# Global grid state
grid = [DEFAULT_COLOR] * (GRID_SIZE * GRID_SIZE)

# Store connected WebSocket clients
clients = set()

# HTTP Handler to serve REST API
class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/grid":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"grid": grid}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/place_pixel":
            content_length = int(self.headers["Content-Length"])
            post_data = json.loads(self.rfile.read(content_length))

            index = post_data.get("index")
            color = post_data.get("color")

            if 0 <= index < len(grid):
                grid[index] = color

                # Notify all WebSocket clients
                asyncio.run(broadcast_update(index, color))

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Pixel placed", "index": index, "color": color}).encode())
            else:
                self.send_response(400)
                self.end_headers()

# WebSocket server
async def websocket_handler(websocket, path):
    clients.add(websocket)
    try:
        # Send initial grid state
        await websocket.send(json.dumps({"type": "grid", "data": grid}))

        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "place_pixel":
                index = data["index"]
                color = data["color"]
                if 0 <= index < len(grid):
                    grid[index] = color
                    await broadcast_update(index, color)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)

# Function to broadcast updates
async def broadcast_update(index, color):
    if clients:
        message = json.dumps({"type": "update", "index": index, "color": color})
        await asyncio.gather(*(client.send(message) for client in clients))

# Run HTTP Server in a separate thread
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

def run_http_server():
    server = ThreadedHTTPServer(("0.0.0.0", PORT), RequestHandler)
    print(f"HTTP Server running on port {PORT}")
    server.serve_forever()

# Start WebSocket Server
async def start_ws_server():
    server = await websockets.serve(websocket_handler, "0.0.0.0", WS_PORT)
    print(f"WebSocket Server running on port {WS_PORT}")
    await server.wait_closed()

# Start HTTP server in a separate thread
threading.Thread(target=run_http_server, daemon=True).start()

# Start WebSocket Server (main event loop)
asyncio.run(start_ws_server())

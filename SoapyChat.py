import asyncio
import websockets
import json
import socket
import http.server
import socketserver
import threading
import os

# ======================
# SETTINGS
# ======================
HTTP_PORT = 8000
WS_PORT = 8765

# ======================
# LAN IP DETECTION
# ======================
def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

LAN_IP = get_lan_ip()

# ======================
# SIMPLE HTTP SERVER
# ======================
class SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def start_http():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with socketserver.TCPServer(("", HTTP_PORT), SilentHandler) as httpd:
        httpd.serve_forever()

# ======================
# WEBSOCKET CHAT SERVER
# ======================
clients = set()
users = {}
messages = []

async def ws_handler(ws):
    clients.add(ws)

    # Send history
    await ws.send(json.dumps({
        "type": "history",
        "messages": messages
    }))

    try:
        async for data in ws:
            msg = json.loads(data)

            if msg["type"] == "join":
                users[ws] = msg["name"]

            elif msg["type"] in ("message", "image"):
                payload = {
                    "type": msg["type"],
                    "name": users.get(ws, "Anonymous"),
                    "content": msg["content"]
                }
                messages.append(payload)

                for client in clients:
                    await client.send(json.dumps(payload))

    except websockets.ConnectionClosed:
        pass
    finally:
        clients.remove(ws)
        users.pop(ws, None)

# ======================
# MAIN
# ======================
async def main():
    print("\n🫧 Soapy Chat is running!")
    print("\n👉 Open this link on other devices:\n")
    print(f"   http://{LAN_IP}:{HTTP_PORT}\n")

    async with websockets.serve(
        ws_handler,
        "0.0.0.0",
        WS_PORT,
        max_size=10_000_000
    ):
        await asyncio.Future()

# Start HTTP server in background
threading.Thread(target=start_http, daemon=True).start()

# Start WebSocket server
asyncio.run(main())

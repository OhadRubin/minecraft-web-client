import asyncio
import json
from typing import Set
import websockets

class CrossModeServer:
    def __init__(self, host: str = "localhost", port: int = 8767) -> None:
        self.host = host
        self.port = port
        self.bot_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.mcp_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.pygame_clients: Set[websockets.WebSocketServerProtocol] = set()
        self._server = None

    async def start(self) -> None:
        self._server = await websockets.serve(self._handler, self.host, self.port)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handler(self, websocket):
        try:
            async for raw in websocket:
                message = json.loads(raw)
                if message.get("init") == "bot":
                    self.bot_clients.add(websocket)
                    continue
                if message.get("init") == "mcp":
                    self.mcp_clients.add(websocket)
                    continue
                if message.get("init") == "pygame":
                    self.pygame_clients.add(websocket)
                    continue
                if websocket in self.bot_clients:
                    for client in list(self.mcp_clients):
                        if client.open:
                            await client.send(raw)
                elif websocket in self.mcp_clients or websocket in self.pygame_clients:
                    for client in list(self.bot_clients):
                        if client.open:
                            await client.send(raw)
        finally:
            for s in (self.bot_clients, self.mcp_clients, self.pygame_clients):
                s.discard(websocket)


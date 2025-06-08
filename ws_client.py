import asyncio
import json
import websockets

class WebSocketClient:
    """Minimal async WebSocket client used for tests."""

    def __init__(self, url: str, on_disconnect=None):
        self.url = url
        self.on_disconnect = on_disconnect
        self._ws = None
        self._task = None

    def start(self):
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._connect())

    async def _connect(self):
        try:
            async with websockets.connect(self.url) as ws:
                self._ws = ws
                async for _ in ws:
                    pass
        finally:
            if self.on_disconnect:
                self.on_disconnect()

    def send(self, data):
        if self._ws:
            asyncio.create_task(self._ws.send(json.dumps(data)))

    async def stop(self):
        if self._ws:
            await self._ws.close()
        if self._task:
            await self._task

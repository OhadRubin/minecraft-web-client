import asyncio
import json
import threading
import websockets


class WebSocketClient:
    """Minimal async WebSocket client used for tests."""

    def __init__(self, url: str, on_connect=None, on_disconnect=None) -> None:
        self.url = url
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.ws = None

    def start(self) -> None:
        self.thread.start()
        asyncio.run_coroutine_threadsafe(self._connect(), self.loop)

    async def _connect(self) -> None:
        self.ws = await websockets.connect(self.url)
        if self.on_connect:
            self.on_connect()

    def send(self, data) -> None:
        if not self.ws:
            raise RuntimeError("WebSocket not connected")
        msg = json.dumps(data)
        asyncio.run_coroutine_threadsafe(self.ws.send(msg), self.loop)

    async def stop(self) -> None:
        if self.ws is not None:
            await self.ws.close()
        if self.on_disconnect:
            self.on_disconnect()
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

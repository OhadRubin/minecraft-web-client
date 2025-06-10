import asyncio
import json
import threading
import websockets


class WebSocketClient:
    """Simple asynchronous WebSocket client used for tests."""

    def __init__(self, uri: str, on_connect=None, on_message=None, on_disconnect=None):
        self.uri = uri
        self.on_connect = on_connect
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        self._loop = None
        self._thread = None
        self._ws = None

    def start(self):
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect_loop())

    async def _connect_loop(self):
        async with websockets.connect(self.uri) as ws:
            self._ws = ws
            if self.on_connect:
                self.on_connect()
            try:
                async for message in ws:
                    if self.on_message:
                        self.on_message(json.loads(message))
            finally:
                if self.on_disconnect:
                    self.on_disconnect()

    def send(self, data):
        if self._loop and self._ws:
            asyncio.run_coroutine_threadsafe(self._ws.send(json.dumps(data)), self._loop)

    async def stop(self):
        if self._ws:
            await self._ws.close()
        if self._loop:
            self._loop.stop()
        if self._thread:
            self._thread.join(timeout=1)

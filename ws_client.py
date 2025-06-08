import asyncio
import json
from threading import Thread

import websockets

class WebSocketClient:
    """Very small websocket client used for tests."""

    def __init__(self, url, on_connect=None, on_message=None, on_disconnect=None):
        self.url = url
        self.on_connect = on_connect
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        self._loop = None
        self._ws = None
        self._thread = None

    async def _run(self):
        async with websockets.connect(self.url) as ws:
            self._ws = ws
            if self.on_connect:
                self.on_connect()
            try:
                async for msg in ws:
                    if self.on_message:
                        self.on_message(json.loads(msg))
            finally:
                if self.on_disconnect:
                    self.on_disconnect()

    def start(self):
        self._loop = asyncio.new_event_loop()
        self._thread = Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        asyncio.run_coroutine_threadsafe(self._run(), self._loop)

    def send(self, data):
        if not self._ws:
            return
        asyncio.run_coroutine_threadsafe(
            self._ws.send(json.dumps(data)), self._loop
        )

    async def stop(self):
        if self._ws:
            fut = asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)
            await asyncio.wrap_future(fut)
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join()

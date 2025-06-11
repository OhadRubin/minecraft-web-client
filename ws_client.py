import asyncio
import json
import threading
import websockets

class WebSocketClient:
    def __init__(self, url, on_connect=None, on_disconnect=None):
        self.url = url
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self._loop = asyncio.new_event_loop()
        self._thread = None
        self._ws = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect())

    async def _connect(self):
        async with websockets.connect(self.url) as ws:
            self._ws = ws
            if self.on_connect:
                self.on_connect()
            try:
                async for _ in ws:
                    pass
            finally:
                if self.on_disconnect:
                    self.on_disconnect()

    def send(self, data):
        if self._ws:
            asyncio.run_coroutine_threadsafe(self._ws.send(json.dumps(data)), self._loop)

    async def stop(self):
        if self._ws:
            await self._ws.close()
        if self._loop.is_running():
            self._loop.stop()
        if self._thread:
            self._thread.join()

import asyncio
import json
import threading
from typing import Callable, Optional, Any, List

import websockets

class WebSocketClient:
    """Reusable WebSocket client with reconnection and callbacks."""

    def __init__(
        self,
        uri: str,
        on_connect: Optional[Callable[[], Any]] = None,
        on_disconnect: Optional[Callable[[], Any]] = None,
    ) -> None:
        self.uri = uri
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self._pending: List[dict] = []
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stop = threading.Event()

    def start(self) -> None:
        if not self._thread.is_alive():
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread.is_alive():
            self._thread.join(timeout=1)

    def send(self, message: dict) -> None:
        if self.connected and self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps(message)), self._loop
            )
        else:
            self._pending.append(message)

    def reconnect(self) -> None:
        self.stop()
        self.start()

    # Internal methods
    async def _connect(self) -> None:
        delay = 1
        while not self._stop.is_set():
            try:
                self.websocket = await websockets.connect(self.uri)
                self.connected = True
                if self.on_connect:
                    self.on_connect()
                await self._flush_pending()
                delay = 1
                await self._wait_forever()
            except Exception as exc:
                print(f"WebSocket error: {exc}")
            finally:
                if self.connected and self.on_disconnect:
                    self.on_disconnect()
                self.connected = False
                if self.websocket:
                    try:
                        await self.websocket.close()
                    except Exception:
                        pass
                    self.websocket = None
            if self._stop.is_set():
                break
            await asyncio.sleep(delay)
            delay = min(delay * 2, 10)

    async def _wait_forever(self) -> None:
        while not self._stop.is_set():
            await asyncio.sleep(0.1)

    async def _flush_pending(self) -> None:
        while self._pending and self.websocket and not self.websocket.closed:
            msg = self._pending.pop(0)
            try:
                await self.websocket.send(json.dumps(msg))
            except Exception as exc:
                print(f"Send error: {exc}")
                self._pending.insert(0, msg)
                break

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect())
        self._loop.close()

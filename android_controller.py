import asyncio
import json
import math
import os
import argparse

from ws_client import WebSocketClient

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

DEFAULT_WS_URI = os.environ.get("MINECRAFT_WS_URI", "ws://localhost:8081")
DEFAULT_LEFT_HANDED = os.environ.get("LEFT_HANDED", "0") == "1"

class JoystickWidget(Widget):
    """Simple on-screen joystick."""

    def __init__(self, callback, **kwargs) -> None:
        super().__init__(**kwargs)
        self.callback = callback
        self.radius = 80
        self.active = False
        with self.canvas:
            Color(0.5, 0.5, 0.5)
            self.circle = Line(circle=(0, 0, self.radius), width=2)
            Color(0.8, 0.8, 0.2)
            self.knob = Ellipse(size=(40, 40))
        self._center_knob()

    def on_size(self, *args) -> None:
        self._center_knob()

    def _center_knob(self) -> None:
        self.circle.circle = (self.center_x, self.center_y, self.radius)
        self.knob.pos = (self.center_x - 20, self.center_y - 20)

    def _update_knob(self, pos) -> None:
        dx = pos[0] - self.center_x
        dy = pos[1] - self.center_y
        dist = math.hypot(dx, dy)
        if dist > self.radius:
            angle = math.atan2(dy, dx)
            pos = (
                self.center_x + math.cos(angle) * self.radius,
                self.center_y + math.sin(angle) * self.radius,
            )
        self.knob.pos = (pos[0] - 20, pos[1] - 20)
        self.callback((pos[0] - self.center_x) / self.radius, (pos[1] - self.center_y) / self.radius)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.active = True
            self._update_knob(touch.pos)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.active:
            self._update_knob(touch.pos)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.active:
            self.active = False
            self._center_knob()
            self.callback(0, 0)
            return True
        return super().on_touch_up(touch)


class CameraWidget(Widget):
    """Drag area to control camera look."""

    def __init__(self, callback, **kwargs) -> None:
        super().__init__(**kwargs)
        self.callback = callback
        self.last = None
        with self.canvas:
            Color(0.2, 0.2, 0.2)
            self.rect = Line(rectangle=(0, 0, 0, 0), width=1)

    def on_size(self, *args) -> None:
        self.rect.rectangle = (self.x, self.y, self.width, self.height)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.last = touch.pos
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.last is not None:
            dx = touch.x - self.last[0]
            dy = touch.y - self.last[1]
            self.last = (touch.x, touch.y)
            self.callback(dx * 2, dy * 2)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.last is not None:
            self.last = None
            return True
        return super().on_touch_up(touch)


class ControllerApp(App):
    """Kivy app providing touch controls for the Minecraft Web Client."""
    def __init__(self, ws_uri: str = DEFAULT_WS_URI, left_handed: bool = DEFAULT_LEFT_HANDED, **kwargs) -> None:
        super().__init__(**kwargs)
        self.ws_uri = ws_uri
        self.left_handed = left_handed

    def build(self):
        self.client = WebSocketClient(
            self.ws_uri, on_connect=self.update_status, on_disconnect=self.update_status
        )
        self.client.start()

        root = FloatLayout()
        self.status_label = Label(text="Connecting...", size_hint=(None, None), size=(150, 30))
        root.add_widget(self.status_label)
        self.joystick = JoystickWidget(self.send_move, size=(200, 200))
        root.add_widget(self.joystick)

        self.camera = CameraWidget(self.send_look, size=(300, 250))
        root.add_widget(self.camera)

        btn_left = Button(text="Left", size=(80, 40))
        btn_left.bind(on_press=lambda *_: self.send_click(True, 0), on_release=lambda *_: self.send_click(False, 0))
        root.add_widget(btn_left)
        self.btn_left = btn_left

        btn_right = Button(text="Right", size=(80, 40))
        btn_right.bind(on_press=lambda *_: self.send_click(True, 2), on_release=lambda *_: self.send_click(False, 2))
        root.add_widget(btn_right)
        self.btn_right = btn_right

        btn_jump = Button(text="Jump", size=(80, 40))
        btn_jump.bind(on_press=lambda *_: self.send_control("jump", True), on_release=lambda *_: self.send_control("jump", False))
        root.add_widget(btn_jump)
        self.btn_jump = btn_jump

        self.btn_sneak = ToggleButton(text="Sneak", size=(80, 40))
        self.btn_sneak.bind(on_press=lambda inst: self.send_control("sneak", inst.state == "down"))
        root.add_widget(self.btn_sneak)

        self.btn_sprint = ToggleButton(text="Sprint", size=(80, 40))
        self.btn_sprint.bind(on_press=lambda inst: self.send_control("sprint", inst.state == "down"))
        root.add_widget(self.btn_sprint)

        btn_inv = Button(text="Inv", size=(80, 40))
        btn_inv.bind(on_press=lambda *_: self.send_inventory())
        root.add_widget(btn_inv)
        self.btn_inv = btn_inv
        
        self._update_positions()
        Window.bind(on_resize=self._on_resize)
        Window.bind(on_rotate=self._on_resize)
        Window.bind(on_key_down=self._on_key_down)
        from kivy.clock import Clock
        Clock.schedule_interval(lambda *_: self.update_status(), 0.5)

        return root

    def _on_resize(self, *_):
        self._update_positions()

    def _update_positions(self) -> None:
        orientation = "landscape" if Window.width > Window.height else "portrait"
        center_camera = (Window.width / 2 - 150, Window.height / 2 - 125)
        if orientation == "portrait":
            center_camera = (Window.width / 2 - 150, Window.height - 300)
        self.camera.pos = center_camera
        if self.left_handed:
            joy_x = Window.width - 220
            btn_x = 20
            status_x = Window.width - 160
        else:
            joy_x = 20
            btn_x = Window.width - 180
            status_x = 10

        joy_y = 20 if orientation == "landscape" else 40
        btn_y = 20 if orientation == "landscape" else 40

        self.joystick.pos = (joy_x, joy_y)
        self.btn_left.pos = (btn_x, btn_y)
        self.btn_right.pos = (btn_x + 90, btn_y)
        self.btn_jump.pos = (btn_x, btn_y + 50)
        self.btn_sneak.pos = (btn_x + 90, btn_y + 50)
        self.btn_sprint.pos = (btn_x, btn_y + 100)
        self.btn_inv.pos = (btn_x + 90, btn_y + 100)
        self.status_label.pos = (status_x, Window.height - 40)

    def _on_key_down(self, _window, key, *_args):
        if key in (27, 1001):  # escape/back
            self.stop()
        elif key == ord('r'):
            self.client.reconnect()

    def on_stop(self):
        self.client.stop()

    def update_status(self):
        status = "Connected" if self.client.connected else "Disconnected"
        self.status_label.text = status

    # WebSocket helpers
    def send_move(self, x: float, y: float) -> None:
        self.client.send({"type": "move", "x": x, "z": y})

    def send_look(self, dx: float, dy: float) -> None:
        self.client.send({"type": "look", "movementX": dx, "movementY": dy})

    def send_click(self, pressed: bool, button: int) -> None:
        action = "down" if pressed else "up"
        self.client.send({"type": "documentMouseEvent", "button": button, "action": action, "updateMouse": pressed})

    def send_control(self, control: str, state: bool) -> None:
        self.client.send({"type": "control", "control": control, "state": state})

    def send_inventory(self) -> None:
        self.client.send({"type": "control", "control": "inventory", "state": True})
        self.client.send({"type": "control", "control": "inventory", "state": False})


def parse_args() -> argparse.Namespace:
    """Parse command line options for the Android controller."""

    parser = argparse.ArgumentParser(description="Minecraft Android Controller")
    parser.add_argument("--uri", default=DEFAULT_WS_URI, help="WebSocket URI")
    parser.add_argument(
        "--left-handed",
        action="store_true",
        default=DEFAULT_LEFT_HANDED,
        help="Flip layout for left-handed use",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for running the Kivy Android controller."""

    args = parse_args()
    ControllerApp(ws_uri=args.uri, left_handed=args.left_handed).run()


if __name__ == "__main__":
    main()

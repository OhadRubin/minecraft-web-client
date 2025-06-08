# mc_pygame_controller/camera_drag_handler.py
from mc_pygame_controller.look_path import LookPathTracker

class CameraDragHandler:
    def __init__(self, look_path_tracker: LookPathTracker):
        self.look_path_tracker = look_path_tracker
        self._was_dragging: bool = False

    def update(self, is_in_camera_area: bool, is_mouse_pressed: bool) -> None:
        is_dragging_now = is_in_camera_area and is_mouse_pressed

        if is_dragging_now and not self._was_dragging:
            # Start of drag
            self.look_path_tracker.start_mouse_tracking()
        elif not is_dragging_now and self._was_dragging:
            # End of drag
            self.look_path_tracker.stop_mouse_tracking()

        self._was_dragging = is_dragging_now

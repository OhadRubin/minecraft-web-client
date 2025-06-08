from importlib.machinery import SourceFileLoader
from importlib.util import spec_from_loader, module_from_spec

# Load ActionConverter without executing package __init__
import os

# Resolve path relative to this file so script works from any CWD
AC_PATH = os.path.join(os.path.dirname(__file__), '..', 'mc_pygame_controller', 'action_converter.py')
loader = SourceFileLoader('action_converter', AC_PATH)
spec = spec_from_loader(loader.name, loader)
module = module_from_spec(spec)
loader.exec_module(module)
ActionConverter = module.ActionConverter

test_movements = [
    {"type": "move", "x": 0.5, "z": 0.0},
    {"type": "move", "x": 1.0, "z": 0.0},
    {"type": "move", "x": 0.5, "z": 0.5},
    {"type": "move", "x": 0.11, "z": 0.0},
]

for movement in test_movements:
    result = ActionConverter.convert_pygame_action(movement)
    print(f"Input: {movement} -> Output: {result}")

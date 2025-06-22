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

test_looks = [
    {"type": "look", "movementX": 50, "movementY": 0},
    {"type": "look", "movementX": 0, "movementY": 25},
    {"type": "look", "movementX": 100, "movementY": -50},
    {"type": "look", "movementX": 5, "movementY": 5},
]

for look in test_looks:
    result = ActionConverter.convert_pygame_action(look)
    print(f"Input: {look} -> Output: {result}")

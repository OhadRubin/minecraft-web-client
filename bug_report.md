## Bug Report

Unable to run movement action verification tests.

### Description of problem
Missing dependencies (`openai`, `mcp` package) and package import issues prevent running `test_phase1.py`.

### Steps to reproduce
1. Install requirements.
2. Run `python3 mc_pygame_controller/test_phase1.py`.
3. Observe `ModuleNotFoundError` for `mcp` and other modules.

### Expected vs actual behavior
Expected: Tests execute and validate movement actions.
Actual: Import errors stop execution.

### Console error logs
See attached console output excerpt below.
Traceback (most recent call last):
  File "/workspace/minecraft-web-client/mc_pygame_controller/mode_strategy.py", line 15, in <module>
    from .async_mcp_executor import AsyncMCPExecutor, MCPActionRequest
ImportError: attempted relative import with no known parent package

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/workspace/minecraft-web-client/mc_pygame_controller/async_mcp_executor.py", line 8, in <module>
    from .mcp_client import Server
ImportError: attempted relative import with no known parent package

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/workspace/minecraft-web-client/mc_pygame_controller/test_phase1.py", line 14, in <module>
    from mode_strategy import PygameModeStrategy
  File "/workspace/minecraft-web-client/mc_pygame_controller/mode_strategy.py", line 22, in <module>
    from async_mcp_executor import AsyncMCPExecutor, MCPActionRequest
  File "/workspace/minecraft-web-client/mc_pygame_controller/async_mcp_executor.py", line 10, in <module>

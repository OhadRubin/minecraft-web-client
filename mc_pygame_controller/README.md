# mc_pygame_controller
A sophisticated pygame-based controller for Minecraft Web Client that provides both manual control and AI-driven autonomous gameplay through MCP (Model Context Protocol) integration. **Core component of the 3D Visual SKETCHPAD research project for collecting spatial reasoning training data.**

## Research Context

This controller is part of a larger research pipeline aimed at **collecting 50K Visual SKETCHPAD trajectories for 3D spatial reasoning** and demonstrating transfer to web agents and other domains. The system captures human demonstrations of 3D spatial reasoning tasks in Minecraft, converting them into training data for AI agents.

**Research Pipeline**:
- **Phase 0**: Implement 3D Visual SKETCHPAD tools (MVP) ✅
- **Phase 1**: Collect 50 manual examples 
- **Phase 2**: Finetune GPT-4.1-nano on examples
- **Phase 3**: Use finetuned model to collect 1K trajectories
- **Phase 4-7**: Scale to 50K trajectories and evaluate transfer

**Core Hypothesis**: 3D spatial reasoning skills learned in Minecraft will transfer to web agent tasks and other domains.

## Overview

The `mc_pygame_controller` is a dual-mode interface that bridges human input and AI control for Minecraft gameplay. It supports:

- **pygame mode**: Direct WebSocket communication with Minecraft Web Client for human control
- **MCP mode**: AI-driven autonomous gameplay using Model Context Protocol servers
- **3D annotation development**: Core `annotate_3d_position` tool implementation

## Architecture

### Complete System Architecture

The mc_pygame_controller operates within a larger ecosystem of interconnected services:

```
┌─────────────────────┐    ┌─────────────────────┐    ┌──────────────────────┐
│  pygame Controller  │    │   minecraft-mcp-    │    │   Minecraft Web      │
│  (This Module)      │◄──►│   server.ts         │◄──►│   Client (Browser)   │
│                     │    │   (MCP Tools)       │    │   (Three.js/WebGL)   │
└─────────────────────┘    └─────────────────────┘    └──────────────────────┘
           │                          │                          │
           └──────────────────────────┼──────────────────────────┘
                                      ▼
                            ┌─────────────────────┐
                            │    server.js        │
                            │  (WebSocket Relay)  │
                            │   Port 8081         │
                            └─────────────────────┘
```

**Key Components:**

1. **server.js (WebSocket Relay Server)**: Central message routing hub
   - Manages three client types: `bot`, `pygame`, `mcp`
   - Routes messages between pygame controller ↔ Minecraft client
   - Routes messages between MCP server ↔ Minecraft client
   - Runs on port 8081 (WebSocket) + 8080 (HTTP)

2. **minecraft-mcp-server.ts (MCP Tools)**: Provides AI control capabilities
   - Tools: `walk`, `lookAngle`, `leftClick`, `rightClick`, `getBotStatus`, `wait`
   - **3D Visual SKETCHPAD tool**: `annotate_3d_position` (in development)
   - Screenshot capture with status overlay
   - Connects as `mcp` client to WebSocket server

3. **Minecraft Web Client (Browser)**: The actual game interface
   - Three.js WebGL renderer with scene access (`window.world.scene`)
   - Receives commands via WebSocket, executes in game world
   - Registers as `bot` client to WebSocket server
   - Provides visual feedback and screenshots

4. **mc_pygame_controller (This Module)**: Human interface and demonstration capture
   - Registers as `pygame` client to WebSocket server
   - Captures human spatial reasoning demonstrations
   - Converts to PygameMCPAsyncMessageChain format for AI training

### Message Flow Architecture

```
Human Input → pygame Controller → WebSocket Server → Minecraft Client → Visual Feedback
     ↑                                    ↕                              ↓
Agent Loop ← MCP Server ← MCP Tools ←─────┘                        Screenshots
     ↑                     ↓
Training Data ←─── Trajectory Recording
```

**Data Flow Steps:**
1. **Human demonstrates** spatial reasoning task via pygame interface
2. **pygame controller** sends WebSocket commands to Minecraft client  
3. **Minecraft client** executes actions and updates visual scene
4. **Screenshots captured** showing results of spatial reasoning
5. **Trajectory recorded** in PygameMCPAsyncMessageChain format
6. **Training data** used to teach AI agents spatial reasoning skills

### Three-Client-Type System

The WebSocket server manages three distinct client types:

- **`bot` clients**: Minecraft Web Client instances that execute commands
- **`pygame` clients**: This pygame controller for human demonstrations  
- **`mcp` clients**: MCP servers providing AI control tools

**Message Routing Rules:**
- `pygame` → `bot`: Human commands forwarded to Minecraft
- `mcp` → `bot`: AI tool calls forwarded to Minecraft  
- `bot` → `mcp`: Game state/screenshots sent to AI tools
- `bot` → `pygame`: Status updates sent to human interface

### Core Components

The controller is built on a modular architecture that separates concerns like state management, UI, and mode-specific logic.

#### 1. State Management (`controller_state.py`)
- **`ControllerState`**: A centralized dataclass that holds all runtime state for the controller. This includes the current mode (`pygame` or `mcp`), connection status, hotbar selection, movement values, and detailed states for all actions (e.g., button presses, toggles). This provides clean state sharing between components.

#### 2. UI Layer (`ui_manager.py`, `ui_elements.py`, `ui_layout_config.py`)
- **`UIManager`**: Manages all UI components, input processing, and rendering. It acts as a single point of contact for the UI, decoupling the main controller from the complexities of drawing and event handling. It processes user inputs and returns a list of intended actions.
- **`ui_elements.py`**: A library of custom Pygame widgets, including `Button`, `ToggleButton`, `VirtualJoystick`, `KeyboardMovement`, and `TouchArea`.
- **`ui_layout_config.py`**: A data-driven configuration file that defines the position, size, and properties of all UI elements. This allows for easy layout customization without modifying the core logic.

#### 3. Action Processing Layer (`action_handler.py`)
- **`ActionHandler`**: Dedicated class for processing all user actions. Contains the action dispatch dictionary and all `handle_*` methods (movement, clicks, jumps, inventory, etc.). This separation allows the main controller to focus purely on orchestration while the ActionHandler manages the specifics of each game action.
- **Dispatch Pattern**: Uses a clean dictionary-based dispatch system to route actions to appropriate handlers, eliminating complex conditional logic.

#### 4. Controller & Strategy Layer (`controller_base.py`, `mode_strategy.py`)
- **`MinecraftController` (`controller_base.py`)**: The main orchestration class. Initializes all components (State, UI, ActionHandler, Strategy) and runs the main game loop (`_process_frame`). Delegates all mode-specific behavior to its current strategy object.
- **`ModeStrategy` (`mode_strategy.py`)**: Implements the Strategy Pattern to completely eliminate mode-specific `if/else` statements.
    - **`PygameModeStrategy`**: Handles real-time continuous streaming for `pygame` mode, sending WebSocket commands directly to Minecraft client. Includes continuous movement streaming and button hold processing.
    - **`MCPModeStrategy`**: Handles discrete action processing for `mcp` mode, converting actions into MCP tool calls for data collection and AI control.

#### 5. Demonstration & AI Integration Layer (`interface.py`, `chain.py`, `conversation.py`)
- **`MinecraftControllerInterface` (`interface.py`)**: The primary bridge for capturing human demonstrations. In MCP mode, it receives actions, executes them via the `tools_mapping`, and records them.
- **`TrajectoryStorage` (`interface.py`)**: Stores the captured sequences of human actions as structured JSON trajectories, ready for use as AI training data.
- **`PygameMCPAsyncMessageChain` (`chain.py`)**: A data structure for managing the conversation with an AI model. It's designed to be compatible with the OpenAI API format, supporting tool calls and multimodal content.
- **`ConversationPanel` (`conversation.py`)**: Manages the sequence of messages. Crucially, it can convert a series of captured human actions into a "mock" LLM response containing `tool_calls`, which is the core mechanism for generating training data from demonstrations.

#### 6. MCP Client Layer (`mcp_client.py`)
- **`Server`**: Manages the lifecycle of an MCP server subprocess, communicating via `stdio`. It handles server initialization, tool discovery, and cleanup.
- **`create_tool_functions`**: A key utility that inspects an MCP server's available tools and dynamically creates asynchronous Python functions to call them. This provides a clean programming interface for interacting with AI tools.

#### 7. Specialized Logic (`look_path.py`)
- **`LookPathTracker`**: A sophisticated system for analyzing camera movement. It captures mouse drag gestures, calculates total rotation in degrees, and generates discrete `lookAngle` MCP tool calls. This translates continuous human input into a meaningful, trainable AI action.
- **`LookPathVisualizationArea`**: A real-time UI component that visualizes the path and statistics of a camera drag operation.

#### 8. Entrypoint (`controller.py`)
- This script serves as the main entrypoint for running the controller. It parses command-line arguments (like `--mcp` and `--sensitivity`), initializes the necessary servers for MCP mode, and launches the appropriate controller session.


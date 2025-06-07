# Changes from Zardoy Fork

This document lists all files that have been added, modified, or deleted in this fork compared to the original [zardoy/minecraft-web-client](https://github.com/zardoy/minecraft-web-client) repository.

## Files Added (A)

### Documentation Files
- `2d_visual_sketchpad_tools.md` - Documentation for 2D visual sketchpad tools
- `3d_visual_sketchpad_lit_review.md` - Literature review for 3D visual sketchpad
- `ANNOTATE_3D_POSITION_ADDITIONAL_FEATURES.md` - Additional features for 3D position annotation
- `ANNOTATE_3D_POSITION_MCP_IMPLEMENTATION.md` - MCP implementation for 3D position annotation
- `ANNOTATE_3D_POSITION_SPEC.md` - Specification for 3D position annotation
- `CLAUDE.md` - Claude-specific documentation
- `DOCUMENT_MOUSE_EVENTS_PLAN.md` - Plan for documenting mouse events
- `MCP_README.md` - MCP (Model Context Protocol) README
- `MC_TO_THREEJS_POSITION_MAPPING.md` - Mapping between Minecraft and Three.js positions
- `RENDERER_DRAWING_GUIDE.md` - Guide for renderer drawing
- `WEBSOCKET_FLOW.md` - WebSocket flow documentation
- `goal.md` - Project goals
- `plan.md` - Project plan
- `tasks.md` - Task list
- `useful_files.md` - Documentation of useful files
- `trace.txt` - Trace file

### Documentation Subdirectory
- `docs/android/README.md` - Android-specific README
- `docs/android/USAGE.md` - Android usage documentation
- `docs/gamepad-flow-explanation.md` - Gamepad flow explanation
- `docs/websocket-drag-drop-plan.md` - WebSocket drag-drop plan

### Python Modules
#### mc_pygame_controller package
- `mc_pygame_controller/__init__.py` - Package initialization
- `mc_pygame_controller/chain.py` - Chain functionality
- `mc_pygame_controller/chain_utils.py` - Chain utilities
- `mc_pygame_controller/constants.py` - Constants
- `mc_pygame_controller/controller.py` - Main controller
- `mc_pygame_controller/controller_base.py` - Controller base class
- `mc_pygame_controller/conversation.py` - Conversation handling
- `mc_pygame_controller/idea.md` - Ideas documentation
- `mc_pygame_controller/interface.py` - Interface definitions
- `mc_pygame_controller/look_path.py` - Look path functionality
- `mc_pygame_controller/mcp_client.py` - MCP client
- `mc_pygame_controller/message_chain.py` - Message chain handling
- `mc_pygame_controller/ui_elements.py` - UI elements

#### mcp_agent package
- `mcp_agent/__init__.py` - MCP agent package initialization

### Scripts and Configuration
- `go.sh` - Go script
- `setup.sh` - Setup script
- `requirements_kivy.txt` - Kivy requirements
- `requirements_pygame.txt` - Pygame requirements
- `minecraft-mcp-server.ts` - TypeScript MCP server
- `wsLogger.js` - WebSocket logger

### React Components and Notes
- `src/react/WsCursor.tsx` - WebSocket cursor component
- `src/react/notes.md` - React notes
- `src/wsCommandClient.ts` - WebSocket command client

### Tests
- `tests/test_ws_client.py` - WebSocket client tests

## Files Modified (M)

### Configuration Files
- `.gitignore` - Git ignore rules
- `config.json` - Configuration file
- `package.json` - Node.js package configuration
- `pnpm-lock.yaml` - PNPM lock file

### Documentation
- `README.MD` - Main README file

### Frontend Files
- `index.html` - Main HTML file
- `server.js` - Server file

### Source Code
- `src/controls.ts` - Controls logic
- `src/index.ts` - Main entry point
- `src/mineflayer/plugins/mouse.ts` - Mouse plugin
- `src/optionsGuiScheme.tsx` - Options GUI scheme
- `src/optionsStorage.ts` - Options storage
- `src/react/DebugOverlay.tsx` - Debug overlay component
- `src/react/MobileTopButtons.tsx` - Mobile top buttons component
- `src/react/button.module.css` - Button styles
- `src/reactUi.tsx` - React UI main component
- `src/watchOptions.ts` - Watch options functionality

### Renderer
- `renderer/viewer/lib/worldrendererCommon.ts` - Common world renderer
- `renderer/viewer/three/worldrendererThree.ts` - Three.js world renderer

## Files Deleted (D)

- `src/react/RendererDebugMenu.tsx` - Renderer debug menu component
- `src/react/rendererDebugMenu.module.css` - Renderer debug menu styles
- `src/react/rendererDebugMenu.module.css.d.ts` - Renderer debug menu style types

## Summary

**Total Changes:**
- **Added:** 49 files
- **Modified:** 18 files  
- **Deleted:** 3 files

**Key Areas of Development:**
1. **MCP (Model Context Protocol) Integration** - Extensive work on MCP server and agent functionality
2. **3D Position Annotation System** - Complete specification and implementation
3. **Python Controller Modules** - Comprehensive pygame-based controller system
4. **Documentation** - Extensive documentation for various features and systems
5. **WebSocket Enhancements** - Improved WebSocket handling and logging
6. **UI/UX Improvements** - Various React component modifications and additions
7. **Android Support** - Documentation and setup for Android functionality

This fork represents a significant expansion of the original minecraft-web-client with focus on advanced control systems, 3D annotation capabilities, and comprehensive documentation. 
# Screenshot Timeout Issue - Investigation & Solution

## Problem Statement

The `walkForward` MCP tool is failing with the error:
```
Tool 'walkForward' execution failed: Screenshot timeout
```

This affects any MCP tool that captures screenshots (`walkForward`, `jump`, `leftClickAndHold`, etc.).

## System Architecture

```
MCP Client (Claude) ↔ MCP Server (minecraft-mcp-server.ts) ↔ WebSocket Server (port 8081) ↔ Minecraft Web Client
```

The screenshot capture flow:
1. MCP tool calls `captureScreenshot()`
2. MCP server sends `{type: "getScreenshot"}` via WebSocket
3. Web client receives command and captures canvas screenshot
4. Web client sends `{type: "screenshot", data: "base64..."}` back
5. MCP server resolves promise with screenshot data

## Root Cause Analysis

### Issue 1: Client-Side Screenshot Capture (FIXED)
**File:** `src/wsCommandClient.ts` (lines ~376-420)

**Problem:** The original screenshot capture was synchronously calling `canvas.toDataURL()` which could block or timeout during active rendering.

**Evidence:** Console logs showed:
```
[WsCommandClient] Capturing screenshot
[WsCommandClient] Screenshot captured successfully
```

**Solution Applied:** 
- Added `requestAnimationFrame()` wait for render completion
- Implemented Promise.race() with 5-second timeout
- Added proper error handling with fallback responses
- Reduced PNG quality to 0.8 for faster processing

### Issue 2: MCP Server Message Handling (PARTIALLY FIXED)
**File:** `minecraft-mcp-server.ts` (lines ~89-144)

**Problem:** Race conditions and improper cleanup in WebSocket message listeners.

**Original Issues:**
- No cleanup of event listeners (memory leaks)
- Race conditions with multiple screenshot requests
- Short 5-second timeout
- Poor error handling

**Solution Applied:**
- Added proper cleanup function to remove listeners
- Implemented resolved flag to prevent multiple resolutions
- Increased timeout to 10 seconds
- Enhanced error handling and logging
- Added 100ms delay before sending command

### Issue 3: Message Routing Problem (CURRENT ISSUE)
**Status:** UNRESOLVED

**Evidence:** Client console shows:
```javascript
{type: 'screenshot', data: 'iVBORw0KGgoAAAANSUhEUgAAA4wAAAUOCAYAAAA2Yr1LAAAAA...'}
```

But this appears to be the client receiving its own response rather than the `getScreenshot` command from the MCP server.

**Hypothesis:** The WebSocket server on port 8081 may have message routing issues between:
- MCP server connection (init: 'mcp')
- Bot client connection (init: 'bot')

## Files Modified

### 1. `src/wsCommandClient.ts`
- **Lines ~376-420:** Enhanced `getScreenshot` case in TouchEvaluator.execute()
- **Key changes:** Added async/await, timeout handling, proper error responses

### 2. `minecraft-mcp-server.ts`
- **Lines ~89-144:** Rewrote `captureScreenshot()` function
- **Key changes:** Proper listener cleanup, race condition prevention, better error handling

## Current Status

✅ **Fixed:** Client-side screenshot capture timing and error handling
✅ **Fixed:** MCP server message listener management
❌ **Unresolved:** WebSocket message routing between MCP server and client

## Next Steps for Resolution

### 1. Investigate WebSocket Server Implementation
**Files to examine:**
- Look for WebSocket server setup (likely in `src/` or root directory)
- Check how it handles different client types (`init: 'mcp'` vs `init: 'bot'`)
- Verify message routing logic between connections

### 2. Debug Message Flow
**Add logging to trace:**
- MCP server → WebSocket server: `{type: "getScreenshot"}`
- WebSocket server → Bot client: Should forward the command
- Bot client → WebSocket server: `{type: "screenshot", data: "..."}`
- WebSocket server → MCP server: Should forward the response

### 3. Potential WebSocket Server Issues
- Message broadcasting instead of targeted routing
- Connection identification problems
- Buffer/timing issues in message forwarding

## Test Commands

To reproduce the issue:
```bash
# Start MCP server
PORT=4000 pnpm mcp-server

# Test via MCP client
# Use walkForward tool and observe timeout
```

## Expected Behavior

When working correctly:
1. MCP server logs: `MCP Server requesting screenshot...`
2. Client logs: `[WsCommandClient] Received command: {type: "getScreenshot"}`
3. Client logs: `[WsCommandClient] Capturing screenshot`
4. Client logs: `[WsCommandClient] Screenshot captured successfully`
5. MCP server logs: `MCP Server received message: screenshot`
6. Tool returns successfully with image data

## Current Behavior

1. ✅ MCP server logs: `MCP Server requesting screenshot...`
2. ❌ Client logs: Shows receiving screenshot response instead of getScreenshot command
3. ❌ MCP server times out after 10 seconds
4. ❌ Tool fails with timeout error

## Architecture Notes

- **Canvas ID:** `viewer-canvas` (set in `renderer/viewer/three/documentRenderer.ts:66`)
- **WebGL Config:** Uses `preserveDrawingBuffer: true` for screenshot capability
- **WebSocket Port:** 8081 (hardcoded in both client and server)
- **MCP Server Port:** 4000 (configurable via PORT env var) 
# Lessons Learned: "If It's Broken, Don't Fix It"

## **Prerequisites: Read These Files Before You Start**

Before diving into debugging similar issues, you **must** understand the dual-mode architecture and why the reference implementation works. This case study only makes sense if you grasp the fundamental patterns involved.

### **1. Understand the Dual-Mode Architecture**

**File:** `mc_pygame_controller/controller.py`
**Lines:** `~220-280` (Main entry point and mode selection)
**What to Look For:**
- Line `~228-234`: Pygame mode startup (synchronous, bypasses server init)
- Line `~235-278`: MCP mode startup (async, proper server initialization)
- **Key Insight:** MCP mode calls `initialize_servers()` and creates unified async context, pygame mode does not.

**File:** `mc_pygame_controller/mode_strategy.py`  
**Lines:** `~85-110` (`PygameModeStrategy.__init__`)
**What to Look For:**
- How `mcp_server` parameter gets passed (or not)
- The conditional `AsyncMCPExecutor` creation based on server availability
- **Key Insight:** If no server is initialized, data collection silently fails.

### **2. Trace the Working Reference (MCP Mode)**

**File:** `mc_pygame_controller/controller.py`
**Lines:** `~249-255` (MCP mode `async def runner()`)
**What to Look For:**
- `await initialize_servers(servers)` - This is the crucial initialization step
- `await run_chat_session(config, args.sensitivity)` - Uses initialized servers

**File:** `mc_pygame_controller/interactive_session.py`
**Lines:** `~45-65` (`handle_interactive_session`)
**What to Look For:**
- `await controller.test_get_bot_status_startup(chain)` - The working getBotStatus test
- Everything runs in the same async context
- **Key Insight:** No threads, no cross-event-loop communication, just clean async flow.

### **3. Understand MCP Server Initialization**

**File:** `mc_pygame_controller/mcp_client.py`
**Lines:** `~69-100` (`Server.initialize`)
**What to Look For:**
- External MCP server subprocess creation via `stdio_client`
- `create_tool_functions` that builds the `tool_mapping`
- **Key Insight:** This step is **mandatory** - without it, `tool_mapping` is empty and MCP calls fail.

### **4. Understand Event Loop Context Issues**

**File:** `mc_pygame_controller/async_mcp_executor.py`  
**Lines:** `~80-120` (`AsyncMCPExecutor.execute_tool`)
**What to Look For:**
- How `asyncio.Queue` is used for result passing
- The error: `"<Queue> is bound to a different event loop"`
- **Key Insight:** asyncio objects are bound to specific event loops - cross-loop access fails.

### **5. Understand the Data Collection Architecture**

**File:** `mc_pygame_controller/controller_base.py`
**Lines:** `~180-220` (`_run_pygame_loop` vs `_run_pygame_async`)
**What to Look For:**
- Traditional pygame mode: synchronous loop with `pygame.event.get()`
- Data collection mode: async loop with `animation_loop()`
- **Key Insight:** The event loop context determines what async operations are possible.

### **Essential Concepts to Grasp:**

1. **Event Loop Boundaries**: Objects created in one event loop cannot be used in another
2. **Initialization Order**: MCP server must be initialized before any tool calls
3. **Reference Pattern**: MCP mode's startup sequence is the proven working approach
4. **Context Matching**: getBotStatus works when called from the same context as server initialization

**Only after understanding these fundamentals should you proceed with the debugging story below.**

---

## **Introduction and Context**

The `mc_pygame_controller` is a sophisticated dual-mode interface for Minecraft Web Client that serves as a **core component of the 3D Visual SKETCHPAD research project**. The system is designed to capture human spatial reasoning demonstrations and convert them into training data for AI agents, with the ultimate goal of collecting 50K trajectories for 3D spatial reasoning research.

The controller operates in two primary modes:
- **Pygame Mode**: Provides optimal human control experience via traditional pygame interface with WebSocket communication to Minecraft client
- **MCP Mode**: Enables AI-driven autonomous gameplay using Model Context Protocol (MCP) servers for structured tool execution

A critical feature of the system is **data collection mode** (`--data-collection`), which enhances pygame mode with parallel MCP execution. This hybrid approach allows humans to control the game naturally while simultaneously collecting structured MCP tool responses, screenshots, and state information - creating rich training data in OpenAI-compatible conversation format.

### **The Feature We Were Implementing**

MCP mode includes a robust startup verification system that tests `getBotStatus` immediately after initialization. This test serves multiple critical purposes:

1. **Connectivity Verification**: Confirms the MCP server is responsive and properly connected to Minecraft
2. **Data Validation**: Retrieves rich game state (position, inventory, biome, etc.) with screenshots
3. **Early Failure Detection**: Identifies server issues before they affect the user experience
4. **Debug Information**: Provides detailed status for troubleshooting connectivity problems

**The working MCP mode startup sequence**:
```
🧪 Testing getBotStatus at startup...
📊 Startup getBotStatus result: {'content': [{'type': 'text', 'text': 'Position: (8, 63, -66) facing West...'}]}
```

**Our Goal**: Add this exact same verification system to pygame mode when data collection is enabled, ensuring the same level of reliability and debugging capability.

### **The Technical Challenge**

The challenge arose from the **architectural differences** between the two modes:

- **MCP Mode**: Everything runs in a unified async context with proper server initialization
- **Pygame Mode**: Traditionally synchronous with WebSocket-only communication
- **Data Collection Mode**: A hybrid that needed to bridge both paradigms

When data collection is enabled, pygame mode creates an MCP server for parallel execution, but the initialization architecture was fundamentally different from MCP mode's proven approach. This led to cross-event-loop communication issues, timing problems, and the classic async synchronization challenges.

### **The Reference Implementation**

We had a **perfect working example** in MCP mode's startup sequence:
```python
# controller.py - MCP mode (working perfectly)
await initialize_servers(servers)
await run_chat_session(config, args.sensitivity)

# handle_interactive_session() 
await controller.test_get_bot_status_startup(chain)
```

This approach was clean, reliable, and had been thoroughly tested. The getBotStatus call worked seamlessly because everything operated within the same async event loop context.

### **What Went Wrong: The Engineering Journey**

Instead of recognizing that we had a proven reference implementation, we attempted to "integrate" the getBotStatus test into pygame mode's existing architecture. This led to a cascade of increasingly complex solutions, each trying to solve the fundamental architectural mismatch between pygame's synchronous design and MCP's async requirements.

The debugging journey that followed became a case study in **when engineering effort should focus on copying proven patterns rather than creating novel solutions**.

---

## **TL;DR: When You Have a Working Solution, Copy It Exactly**

**The Problem**: We needed `getBotStatus` startup testing in pygame mode with data collection.
**The Reference**: MCP mode already did this perfectly.
**What We Did**: Tried to "fix" it with increasingly complex solutions.
**What We Should Have Done**: Copy MCP mode exactly.

---

## **What We Did: A Case Study in Overcomplication**

### **The Goal** 🎯
Add a startup `getBotStatus` test to pygame mode when data collection is enabled, just like MCP mode has.

### **The Reference Implementation** ✅
**MCP mode** already had this working perfectly:
- Initialize MCP servers in main async context
- Call `getBotStatus` directly from same event loop  
- Clean, simple, reliable

### **Our "Solution" Journey** 🤦‍♂️

#### **Attempt 1: Cross-Thread Communication**
```python
# Background thread initializes MCP server
def run_async_init():
    loop = asyncio.new_event_loop()  # Different event loop!
    asyncio.set_event_loop(loop)
    await self.mcp_server.initialize()

# Main thread tries to use it
await self.mcp_server.execute_tool("getBotStatus", {})  # ❌ Event loop mismatch!
```
**Result**: `⚠️ MCP execution error: <Queue> is bound to a different event loop`

#### **Attempt 2: Thread-Safe Queues**
```python
# Added complex queue system for cross-thread communication
self._thread_safe_queue = queue.Queue()
async def _process_thread_safe_queue(self): ...
def _queue_action_for_background_thread(self): ...
```
**Result**: Still fighting the fundamental cross-event-loop issue

#### **Attempt 3: Timing Fixes**
```python
# Wait for background initialization
async def _wait_for_mcp_server_ready(self, timeout=10.0): ...
await self._wait_for_mcp_server_ready()
```
**Result**: Fixed timing but not the architecture - still died with asyncio warnings

---

## **What We Learned: The Hard Way**

### **Lesson 1: Reference Implementations Are Gold** 🏆
We had a **perfect working example** in MCP mode:
```python
# MCP mode (working):
await initialize_servers(servers)           # Main async context
result = await chain.tools_mapping["getBotStatus"]()  # Same context
```

But instead of copying this, we tried to "improve" it.

### **Lesson 2: Event Loop Boundaries Are Real** ⚡
- **Same event loop**: Everything works seamlessly
- **Different event loops**: `asyncio.Queue` bound to different event loop errors
- **Cross-thread async**: Complex synchronization problems

### **Lesson 3: Complexity Cascade** 📈
Each "fix" made things more complex:
1. Simple cross-thread call → Event loop error
2. Add thread-safe queue → More complex, same fundamental issue  
3. Add timing coordination → Even more complex, still doesn't work
4. **Should have been**: Copy the working pattern

---

## **The Core Principle: "If It's Broken, Don't Fix It"**

### **Traditional Wisdom**: "If it ain't broke, don't fix it"
Don't mess with working code.

### **Our New Wisdom**: "If it's broken, don't fix it"
When something is broken **and you have a working reference**, don't try to fix the broken approach - **adopt the working approach**.

### **Applied to Our Case**:
- ❌ **Don't fix**: Background thread MCP initialization  
- ✅ **Do adopt**: Main thread MCP initialization (like MCP mode)

---

## **The Right Solution: Copy What Works**

**What MCP mode does**:
```python
# controller.py (MCP mode)
await initialize_servers(servers)
await run_chat_session(config, args.sensitivity)

# handle_interactive_session()
controller = MinecraftController(mode="mcp", chain_args=(servers, chain))
await controller.test_get_bot_status_startup(chain)
```

**What pygame mode should do**:
```python
# controller_base.py (_run_pygame_async)
await self.mcp_server.initialize()  # Same pattern!
await self.test_get_bot_status_pygame_startup()  # Same pattern!
```

**No background threads. No cross-event-loop communication. No complex synchronization.**

---

## **When to Apply This Principle**

### **✅ Use "Don't Fix It" When**:
- You have a working reference implementation
- Your "fix" is getting increasingly complex
- You're fighting fundamental architectural issues
- The reference implementation is simpler

### **❌ Don't Use When**:
- No working reference exists
- The reference has different requirements
- Simple fixes are available
- You understand why the reference works

---

## **The Meta-Lesson: Engineering Humility**

### **What Went Wrong** 🤔
We assumed our complex pygame architecture was "better" and tried to make MCP fit into it.

### **What We Should Have Done** 💡
Recognized that MCP mode's architecture was already proven and adopted it wholesale.

### **The Humility**:
- **Working code** > **"Better" architecture**
- **Proven patterns** > **Novel approaches**  
- **Simple copying** > **Complex integration**

---

## **Practical Applications**

### **In Code Reviews**:
- "We already do this successfully in module X - let's use the same pattern"
- "Why are we reinventing this when we have a working implementation?"

### **In Architecture Decisions**:
- "Component A already solves this problem - let's use the same approach"
- "Don't architect around the broken piece - copy the working piece"

### **In Debugging**:
- "This works in scenario X but not Y - what's different about X's approach?"
- "Instead of fixing Y, can we make Y work like X?"

---

## **Warning Signs We Missed: How to Recognize You're Overcomplicating**

### **Code Complexity Indicators** 🚨
Each "fix" made our codebase more complex, not simpler:

```python
# Attempt 1: Simple (but wrong)
await self.mcp_server.execute_tool("getBotStatus", {})

# Attempt 2: Added threading
import threading
def run_async_init(): ...
init_thread = threading.Thread(target=run_async_init, daemon=True)

# Attempt 3: Added thread-safe queues  
import queue
self._thread_safe_queue = queue.Queue()
async def _process_thread_safe_queue(self): ...

# Attempt 4: Added timing coordination
async def _wait_for_mcp_server_ready(self, timeout=10.0): ...
```

**Warning Signs**:
- ✅ **Good**: Each fix removes code
- ❌ **Bad**: Each fix adds imports, classes, methods, state variables

### **Error Pattern Escalation** 📈
Our error messages got more obscure, not clearer:

1. `❌ Server not initialized` (clear, actionable)
2. `⚠️ Cannot create async task (no event loop)` (technical, but understandable)  
3. `⚠️ <Queue> is bound to a different event loop` (deep async internals)
4. `WARNING:asyncio:Loop is closed` (framework-level warnings)

**Rule**: If your error messages are getting more technical and less actionable, you're probably going in the wrong direction.

### **The "Just One More" Trap** 🕳️
- "Just add a thread to handle initialization"
- "Just add a queue for cross-thread communication"  
- "Just add timing coordination to wait for readiness"
- "Just add error handling for edge cases"

**Each "just" was a sign we were patching symptoms, not fixing the root cause.**

---

## **The Debugging Methodology We Should Have Used**

### **Working Backwards from Success** 🎯

**Instead of**: "How do we fix our broken approach?"
**Should have asked**: "How does the working approach work?"

```python
# Step 1: Trace the working pattern (MCP mode)
await initialize_servers(servers)                    # Initialize in main async context
result = await chain.tools_mapping["getBotStatus"]() # Call from same context
print(f"📊 Startup getBotStatus result: {result}")   # Success!

# Step 2: Identify the key difference
# MCP: Same event loop for init + use
# Pygame: Different event loops for init + use

# Step 3: Apply the working pattern
# Initialize MCP server in same context where we'll use it
```

### **The "Diff Analysis" Technique** 🔍

**Question**: What's the minimal difference between working and broken code?

```diff
# Working (MCP mode):
+ await self.mcp_server.initialize()  # Main async context
+ await self.mcp_server.execute_tool()  # Same context

# Broken (Pygame mode):
+ # Background thread: self.mcp_server.initialize()  # Different context  
+ await self.mcp_server.execute_tool()  # Main context
```

**The diff shows exactly what to change**: Move initialization to the same context.

### **Reference-Driven Development** 📚

**Process**:
1. **Find working example** in your codebase
2. **Understand WHY it works** (don't just copy blindly)
3. **Identify key patterns** (event loop context, initialization order, etc.)
4. **Apply patterns** to your problem
5. **Verify pattern match** before adding complexity

---

## **The Psychology: Why Smart Engineers Fall Into These Traps**

### **The "Architecture Pride" Problem** 🏗️
We assumed our pygame architecture was superior and tried to force MCP to fit into it.

**Symptom**: "Our approach is more flexible/elegant/scalable"
**Reality**: Working code > elegant architecture
**Fix**: Respect proven patterns over theoretical improvements

### **The Sunk Cost Fallacy in Debugging** 💸
Once we invested effort in the background thread approach, we kept trying to make it work.

**Symptom**: "We've already implemented so much, let's just fix this one issue"
**Reality**: Sometimes starting over is faster than fixing
**Fix**: Track complexity as a debugging metric - if it's increasing, reassess

### **The "Not Invented Here" Syndrome** 🏭
We wanted to solve it "our way" instead of copying the working solution.

**Symptom**: "We can do this better/cleaner/more efficiently"
**Reality**: Working reference implementations are gifts, not challenges
**Fix**: Copy first, optimize later (if ever)

### **Expertise Blindness** 🕶️
Our async/threading knowledge made us think complex solutions were necessary.

**Symptom**: "This requires sophisticated async coordination"
**Reality**: Simple problems often have simple solutions
**Fix**: Start with the simplest possible approach

---

## **Practical Patterns: Code Smells and Solutions**

### **Event Loop Boundary Smell** 🚨
```python
# SMELL: Creating event loops in different threads
def run_async_init():
    loop = asyncio.new_event_loop()  # 🚨 Different loop!
    asyncio.set_event_loop(loop)

# SOLUTION: Use existing async context
async def _run_pygame_async(self):
    await self.mcp_server.initialize()  # ✅ Same loop!
```

### **Cross-Thread Async Smell** 🚨
```python
# SMELL: asyncio.create_task from non-async context
try:
    task = asyncio.create_task(some_async_function())  # 🚨 No event loop!
except RuntimeError as e:
    print("Cannot create async task (no event loop)")

# SOLUTION: Stay in async context
async def proper_async_function(self):
    await some_async_function()  # ✅ Already in event loop!
```

### **Timing Coordination Smell** 🚨
```python
# SMELL: Complex wait/notify patterns for initialization
async def _wait_for_mcp_server_ready(self, timeout=10.0):  # 🚨 Complex!
    while time.time() - start_time < timeout:
        if self.mcp_server.session:
            return True
        await asyncio.sleep(0.1)

# SOLUTION: Direct initialization
await self.mcp_server.initialize()  # ✅ Simple!
```

### **Import Proliferation Smell** 🚨
```python
# SMELL: Each fix requires new imports
import threading     # For background init
import queue        # For cross-thread communication  
import time         # For timing coordination
import asyncio      # For event loop management

# SOLUTION: If imports are proliferating, you're probably overcomplicating
# MCP mode needs: import asyncio  # That's it!
```

---

## **The Actionable Debugging Checklist**

### **Before Writing Code** ✅
- [ ] Is there a working example of this exact functionality?
- [ ] Do I understand WHY the working example works?
- [ ] What's the minimal change to apply the working pattern?
- [ ] Am I trying to fix architecture or fix a bug?

### **While Debugging** ✅
- [ ] Is each fix making the code simpler or more complex?
- [ ] Are my error messages getting clearer or more obscure?
- [ ] Am I adding imports/state/threads, or removing them?
- [ ] Would starting over be faster than continuing this path?

### **When Stuck** ✅
- [ ] Step back: What working code can I copy?
- [ ] Diff analysis: What's the minimal difference between working/broken?
- [ ] Complexity audit: How much scaffolding have I added?
- [ ] Sunk cost check: Am I continuing because of past investment?

---

## **Conclusion: The Wisdom of Simplicity**

**Complex Problem**: Cross-event-loop async communication with timing synchronization
**Simple Solution**: Use the same event loop (like the working reference)

**Complex Debugging**: Event loop warnings, thread synchronization, timing issues  
**Simple Debugging**: Copy-paste the working code

**The hardest part of software engineering isn't writing complex code - it's recognizing when you don't need to.**

---

**Final Wisdom**: When you find yourself saying "this should work but it doesn't," step back and ask: **"Who else has already solved this exact problem?"**

The answer is often sitting right next to your broken code. 🎯

---

## **✅ UPDATE: FIX IMPLEMENTED AND WORKING**

**Date**: January 2025  
**Status**: getBotStatus startup test now works in pygame + data collection mode

### **What Was Fixed**

The core issue from this case study has been **successfully resolved**:

1. **✅ Background thread initialization removed** - No more cross-event-loop communication
2. **✅ Direct async initialization implemented** - Using exact MCP mode pattern  
3. **✅ getBotStatus test works in same event loop** - Clean, simple, reliable
4. **✅ JSON serialization errors handled** - Graceful fallback for data collection
5. **✅ Action deduplication implemented** - No more duplicate leftClick actions
6. **✅ Sequence tracking fixed** - Proper MCP response counting

### **Current Status: Phase 2 Testing Required**

**getBotStatus now works reliably**, but we have identified the **next critical requirement**:

> **Every action that can be performed in pygame mode must translate into a proper MCP trace for data collection.**

This is essential because the 3D Visual SKETCHPAD research project depends on **comprehensive spatial reasoning data capture**. Missing or incorrect MCP traces would create gaps in the training data.

---

## **🎯 PHASE 2: COMPREHENSIVE ACTION COVERAGE VERIFICATION**

### **The Challenge**

We need to systematically verify that **all possible user actions** in pygame mode:
1. **Trigger MCP data collection** when a session is active
2. **Convert to correct MCP format** with proper parameters  
3. **Include getBotStatus calls** for complete state capture
4. **Save to session files** without errors

### **Complete Action Inventory**

**Movement Actions:**
- ✅ WASD keyboard movement → `walk` MCP tool
- ✅ Virtual joystick movement → `walk` MCP tool  
- ⚠️ Mouse camera look/drag → `lookAngle` MCP tool (needs verification)

**Click Actions:**  
- ✅ Left click (via button) → `leftClick` MCP tool
- ✅ Left click (via mouse) → `leftClick` MCP tool
- ✅ Right click (via button) → `rightClick` MCP tool  
- ✅ Right click (via mouse) → `rightClick` MCP tool

**Discrete Actions:**
- ⚠️ Jump (spacebar) → `jump` MCP tool (needs verification)
- ⚠️ Jump (button) → `jump` MCP tool (needs verification)
- ⚠️ Sneak toggle → `sneak` MCP tool (needs verification)
- ⚠️ Sprint toggle → `sprint` MCP tool (needs verification)
- ⚠️ Inventory (E key) → `toggleInventory` MCP tool (needs verification)
- ⚠️ Inventory (button) → `toggleInventory` MCP tool (needs verification)
- ⚠️ Drop item (Q key) → `dropItem` MCP tool (needs verification)
- ⚠️ Drop item (button) → `dropItem` MCP tool (needs verification)
- ⚠️ Swap hands (F key) → `swapHands` MCP tool (needs verification)
- ⚠️ Swap hands (button) → `swapHands` MCP tool (needs verification)
- ⚠️ Hotbar selection (1-9 keys) → `setHotbarSlot` MCP tool (needs verification)
- ⚠️ Hotbar selection (buttons) → `setHotbarSlot` MCP tool (needs verification)

**Special Actions:**
- ❓ Clear path button → No MCP equivalent (UI-only action)
- ❓ Test getBotStatus button → Direct MCP call (special case)
- ❓ Save demonstration button → UI-only action
- ❓ Data collection hotkeys (F5/F6/F7) → Session management (not gameplay)

### **Critical Verification Points**

**1. Action Detection Pipeline:**
```
User Input → UI Manager → Action Handler → Mode Strategy → MCP Data Collection
```

**2. Data Collection Trigger Points:**
- `PygameModeStrategy.handle_movement()` → Should trigger MCP collection
- `PygameModeStrategy.handle_timed_action()` → Should trigger MCP collection  
- `PygameModeStrategy.handle_toggle_action()` → Should trigger MCP collection
- `PygameModeStrategy.handle_simple_action()` → Should trigger MCP collection

**3. Conversion Accuracy:**
- Each action should convert to the **correct MCP tool** with **proper parameters**
- Duration calculations should be **consistent** and **meaningful**
- No actions should be **duplicated** or **missed**

**4. Session Data Integrity:**
- Each action sequence should include **getBotStatus response**
- Session files should contain **complete conversation chains**
- No **JSON serialization errors** should occur

### **Recommended Testing Protocol**

**Phase 2A: Systematic Action Testing**
```bash
# 1. Start pygame mode with data collection
python -m mc_pygame_controller.controller --data-collection

# 2. Start session (F5) with test task description
# 3. Test each action type individually:
#    - Perform action
#    - Wait for MCP processing 
#    - Check console output for MCP traces
#    - Verify getBotStatus is called

# 4. Save session (F6) and inspect JSON file
# 5. Verify session contains expected conversations
```

**Phase 2B: Integration Testing**
```bash
# Test realistic gameplay scenarios:
# - Mining sequence: look → move → left click → getBotStatus
# - Building sequence: select hotbar → right click → getBotStatus  
# - Navigation sequence: move → jump → look → getBotStatus
# - Inventory sequence: inventory → drop item → swap hands → getBotStatus
```

**Phase 2C: Edge Case Testing**
```bash
# Test edge cases that might break data collection:
# - Rapid action sequences
# - Simultaneous actions (move + look)
# - Long action sequences (extended mining)
# - Session boundary conditions (start/stop during actions)
```

### **Success Criteria**

**✅ Complete Coverage**: Every user action generates appropriate MCP trace  
**✅ Accurate Conversion**: All MCP tools have correct parameters and timing  
**✅ Reliable Capture**: getBotStatus consistently called after each action  
**✅ Clean Sessions**: All session files contain complete, valid conversation data  
**✅ No Errors**: No JSON serialization, sequence tracking, or async execution errors

### **Expected Outcome**

When Phase 2 is complete, the system will provide **comprehensive spatial reasoning data collection** suitable for training AI agents on 3D spatial tasks. Every human demonstration will be captured as complete, structured conversations that include:

- **User intent** (task description)
- **Action sequences** (movement, clicks, camera, etc.)  
- **Game state responses** (getBotStatus with position, inventory, world state)
- **Complete context** (screenshots, timing, metadata)

This creates the **50K Visual SKETCHPAD trajectories** needed for the research project's spatial reasoning training data.

### **The Bigger Picture**

This case study demonstrates that **working reference implementations are invaluable** - even complex async architecture problems have simple solutions when you identify and copy proven patterns. The key insight was:

> **Don't fix broken architecture - adopt working architecture.**

Now that the foundation is solid, Phase 2 will ensure the **spatial reasoning research goals** are fully achievable through comprehensive action coverage and reliable data collection. 🎯🎮🧠 
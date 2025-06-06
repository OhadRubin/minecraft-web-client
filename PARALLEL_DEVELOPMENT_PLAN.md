# MVP Implementation Plan: First Trajectory in 2 Days

## Reality Check: We're Almost There! 🎯

**Current Status**: Three.js scene access ✅ PROVEN (121 rainbow cubes successfully added)
**Goal**: First complete trajectory in 2 days
**Mantra**: "If it doesn't help collect the first 50 trajectories, it's scope creep!"

## Single Path to Success

### Option A: Solo Development (2 days)
**Day 1**: Implement MCP tool → **Day 2**: Add recording → **Result**: First trajectory

### Option B: Simple Parallel (1 day) 
**Person 1**: MCP tool implementation (4 hours)
**Person 2**: Recording infrastructure (4 hours)  
**Together**: Integration testing (2 hours)
**Result**: First trajectory in 1 day

## Parallel Approach (If You Want Speed)

### Person 1: MCP Tool (4 hours)
**Goal**: Get `annotate_3d_position` working via agent loop

**Tasks**:
- Copy existing `server.addTool` pattern from `minecraft-mcp-server.ts`
- Add WebSocket handler (copy the proven cube creation code)
- Test via `python simple_client.py --msg "annotate_3d_position(100, 64, 200)"`

**Success**: Red cube appears when called from agent loop

### Person 2: Recording Infrastructure (4 hours)
**Goal**: F5/F6 hotkeys that save trajectory JSON

**Tasks**:
- Add F5/F6 handlers to `mc_pygame_controller/controller.py`
- Create OpenAIAsyncMessageChain recording state
- Hook into existing WebSocket message sending
- Save trajectory JSON files

**Success**: F5/F6 creates valid JSON files

### Integration (2 hours together)
**Goal**: End-to-end test

**Tasks**:
- F5 → "Find and mark the nearest tree"
- Use annotation tool from Person 1
- F6 → Save trajectory from Person 2
- Verify JSON loads correctly

**Success**: Complete trajectory with 3D annotation

### Day 1: One Tool Only (4-6 hours)
**Goal**: Get `annotate_3d_position` working via agent loop

**Morning (2 hours)**: Implement MCP tool
- Copy existing `server.addTool` pattern from `minecraft-mcp-server.ts`
- Add WebSocket handler (copy the proven cube creation code)
- Return screenshot + success message

**Afternoon (2 hours)**: Test via agent loop
- `python simple_client.py --msg "annotate_3d_position(100, 64, 200, 'test', 'red')"`
- Should see red cube appear in Minecraft
- Debug until it works

**That's it. No other tools. No fancy features. Just one working tool.**

### Day 2: Simple Recording (4-6 hours)
**Goal**: F5/F6 hotkeys that create trajectory JSON files

**Morning (3 hours)**: Add recording to pygame controller
- F5: Start recording (set flag, create OpenAIAsyncMessageChain)
- F6: Stop recording (save JSON file)
- Hook into existing WebSocket message sending

**Afternoon (3 hours)**: Test end-to-end
- F5 → "Find and mark the nearest tree"
- Use annotation tool
- F6 → Save trajectory
- Verify JSON loads correctly

**That's it. No UI indicators. No modal dialogs. Just basic recording.**

## MVP Specifications

### Single Tool Implementation
```typescript
// In minecraft-mcp-server.ts - copy existing pattern
server.addTool({
  name: "annotate_3d_position",
  description: "Add red cube at coordinates",
  parameters: z.object({
    x: z.number(),
    y: z.number(), 
    z: z.number()
  }),
  execute: async (args) => {
    // Send WebSocket command (copy cube creation code)
    // Return screenshot
    return { success: true, screenshot: base64Image };
  }
})
```

### Simple Recording Integration
```python
# In mc_pygame_controller/controller.py
class MinecraftController:
    def __init__(self):
        self.recording = False
        self.current_chain = None
    
    def handle_f5(self):
        self.recording = True
        self.current_chain = OpenAIAsyncMessageChain()
    
    def handle_f6(self):
        self.recording = False
        # Save self.current_chain to JSON file
```

### Success Criteria (MVP Only)
- ✅ One tool callable from agent loop
- ✅ Red cube appears at specified coordinates
- ✅ F5/F6 creates valid trajectory JSON
- ✅ JSON contains conversation + screenshots
- ✅ Ready to collect 50 manual examples

## What We're NOT Doing (Scope Creep)

❌ Multiple tools (zoom_and_orient, detect_blocks_in_view)
❌ Complex 3-LLM coordination 
❌ Fancy UI with modal dialogs
❌ Error handling beyond basic functionality
❌ Performance optimization
❌ Color customization
❌ Text labels on markers
❌ Integration testing frameworks
❌ Extensive documentation
❌ Multiple LLM coordination protocols

## The Only Question That Matters

**"Does this help collect the first trajectory?"**

If no → It's scope creep → Don't do it

## Reality: This Should Be Easy

**We already have**:
- ✅ Working WebSocket connection
- ✅ Working MCP server with tools
- ✅ Working pygame controller
- ✅ Working agent loop
- ✅ Working screenshot capture
- ✅ PROVEN Three.js scene modification

**We just need to connect the pieces with minimal glue code.**

## Next Steps (Right Now)

1. Open `minecraft-mcp-server.ts`
2. Copy existing tool pattern
3. Add cube creation code from successful test
4. Test via `python simple_client.py`
5. When that works, add F5/F6 to pygame controller
6. Test end-to-end
7. **Celebrate first trajectory! 🎉**

---

**Remember**: The goal is proving the research concept, not building perfect software. Simple red cubes and basic recording are enough to validate 3D spatial reasoning transfer.

**Timeline**: 2 days from implementation to first trajectory to proving entire research hypothesis.

**Keep it simple. Keep it focused. Get it working.**

## Simple Coordination (No Complex Protocols)

### Person 1 Deliverable
- Working MCP tool in `minecraft-mcp-server.ts`
- Test command: `python simple_client.py --msg "annotate_3d_position(100, 64, 200)"`
- Screenshot showing red cube at coordinates

### Person 2 Deliverable  
- F5/F6 handlers in `mc_pygame_controller/controller.py`
- Example trajectory JSON file (can be empty conversation)
- Proof that OpenAIAsyncMessageChain serialization works

### Integration Requirements
- Person 1's tool must work via agent loop
- Person 2's recording must capture tool calls
- Together: Test F5 → tool usage → F6 workflow

**No complex handoff protocols. Just simple deliverables.** 
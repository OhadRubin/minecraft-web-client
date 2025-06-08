# TASK 05: Inventory Actions Verification

**Assigned Developer**: [DEV_NAME]  
**Estimated Time**: 3-4 hours  
**Priority**: MEDIUM (Item management)

## **Objective**
Verify that inventory-related actions (inventory toggle, drop item, swap hands) trigger proper MCP data collection via keyboard shortcuts and UI buttons.

## **Scope**
Test these inventory actions:
- ⚠️ Inventory (E key) → `toggleInventory` MCP tool (needs verification)
- ⚠️ Inventory (button) → `toggleInventory` MCP tool (needs verification)
- ⚠️ Drop item (Q key) → `dropItem` MCP tool (needs verification)
- ⚠️ Drop item (button) → `dropItem` MCP tool (needs verification)
- ⚠️ Swap hands (F key) → `swapHands` MCP tool (needs verification)
- ⚠️ Swap hands (button) → `swapHands` MCP tool (needs verification)

## **What You Need to Test**

### **1. Inventory Toggle**
```bash
# Test Protocol:
1. Start: python -m mc_pygame_controller.controller --data-collection
2. Press F5, enter task: "Testing inventory toggle"
3. Test inventory access:
   - Press E key to open inventory
   - Press E key again to close inventory
   - Click inventory UI button
   - Rapid E key presses (open/close/open/close)
4. Press F6 to save session
```

### **2. Drop Item**
```bash
# Test Protocol:
1. Start new session: "Testing drop item"
2. Test item dropping:
   - Press Q key (drop 1 item from current slot)
   - Hold Q key (should drop multiple items?)
   - Click drop item UI button
   - Rapid Q key presses
   - Drop while different hotbar slots selected
3. Save session
```

### **3. Swap Hands**
```bash
# Test Protocol:
1. Start new session: "Testing swap hands"
2. Test hand swapping:
   - Press F key (swap main/off hand items)
   - Click swap hands UI button
   - Rapid F key presses
   - Swap hands with different items equipped
3. Save session
```

### **4. Combined Inventory Actions**
```bash
# Test Protocol:
1. Start new session: "Testing inventory combinations"
2. Test action sequences:
   - Open inventory → drop item → close inventory
   - Swap hands → drop item → swap hands
   - Inventory actions while moving/jumping
3. Save session
```

## **Expected MCP Traces**

### **Toggle Inventory Should Generate:**
```json
{
  "tool": "toggleInventory",
  "parameters": {}
}
```

### **Drop Item Should Generate:**
```json
{
  "tool": "dropItem",
  "parameters": {
    "amount": 1
  }
}
```

### **Swap Hands Should Generate:**
```json
{
  "tool": "swapHands",
  "parameters": {}
}
```

## **Edge Detection vs Continuous**

### **Inventory (E key):**
- Should use edge detection (open on press, not continuous)
- Each E press = one toggleInventory action
- Holding E should NOT spam inventory actions

### **Drop Item (Q key):**
- Edge detection for single drops
- Possible continuous for rapid dropping?
- Verify intended behavior

### **Swap Hands (F key):**
- Should use edge detection (swap on press)
- Each F press = one swapHands action
- Holding F should NOT spam swap actions

## **Verification Points**

### **✅ Success Criteria:**
1. **Keyboard Shortcuts Work**: E, Q, F keys trigger MCP actions
2. **UI Buttons Work**: All inventory UI buttons trigger MCP actions
3. **Edge Detection**: Single keypress = single MCP action
4. **Correct Parameters**: Amount=1 for drops, empty params for others
5. **getBotStatus Called**: After each inventory action sequence
6. **No Spam**: Held keys don't generate continuous actions

### **❌ Failure Modes to Check:**
- Keyboard shortcuts not triggering MCP collection
- UI buttons not triggering MCP collection
- Held keys spamming MCP actions
- Wrong parameters (amount != 1 for drops)
- Missing getBotStatus calls
- Conflicts with other actions

## **Deliverables**

### **1. Test Results Document** (`inventory_test_results.md`)
```markdown
## Inventory Toggle Tests
- [✅/❌] E key triggers toggleInventory MCP action
- [✅/❌] Inventory button triggers MCP action
- [✅/❌] Edge detection works (no spam)
- [✅/❌] Parameters are correct (empty)
- [Console log snippet]

## Drop Item Tests
- [✅/❌] Q key triggers dropItem MCP action
- [✅/❌] Drop button triggers MCP action
- [✅/❌] Amount parameter = 1
- [✅/❌] Multiple drops work correctly
- [Console log snippet]

## Swap Hands Tests
- [✅/❌] F key triggers swapHands MCP action
- [✅/❌] Swap button triggers MCP action
- [✅/❌] Parameters are correct (empty)
- [✅/❌] Edge detection works correctly
- [Console log snippet]

## Edge Detection Verification
- [✅/❌] Held E key only triggers once
- [✅/❌] Held Q key behavior is correct
- [✅/❌] Held F key only triggers once
- [Evidence: timing analysis]
```

### **2. Sample Session Files**
- `session_inventory_toggle.json`
- `session_drop_items.json`
- `session_swap_hands.json`
- `session_inventory_combinations.json`

### **3. Edge Detection Analysis**
```markdown
| Key | Hold Duration | Expected Actions | Actual Actions | ✅/❌ |
|-----|---------------|------------------|----------------|-------|
| E   | 2 seconds     | 1 toggleInventory | [result]     |       |
| Q   | 2 seconds     | [1 or multiple?] | [result]     |       |
| F   | 2 seconds     | 1 swapHands      | [result]     |       |
```

## **Key Files to Examine**

- `mc_pygame_controller/action_handler.py` (lines ~370-420) - Inventory edge detection
- `mc_pygame_controller/ui_manager.py` - Inventory UI buttons
- `mc_pygame_controller/mode_strategy.py` - `handle_simple_action()` for inventory
- `mc_pygame_controller/controller_state.py` - State tracking for edge detection

## **Key Code to Review**

Look for edge detection patterns:
```python
# In action_handler.py - verify these patterns:
def process_edge_detections(self, keys_pressed):
    # Handle inventory (E key)
    just_pressed, _ = self._detect_key_edge("inventory", keys_pressed[pygame.K_e])
    if just_pressed:
        self.handle_inventory()

    # Handle drop item (Q key)  
    just_pressed, _ = self._detect_key_edge("drop_item", keys_pressed[pygame.K_q])
    if just_pressed:
        self.handle_drop_item()
        
    # Handle swap hands (F key)
    just_pressed, _ = self._detect_key_edge("swap_hands", keys_pressed[pygame.K_f])
    if just_pressed:
        self.handle_swap_hands()
```

## **Debug Commands**

```bash
# Start with inventory debugging
python -m mc_pygame_controller.controller --data-collection

# Watch for these patterns:
# On E press: "📋 Queued MCP action: toggleInventory"
# On Q press: "📋 Queued MCP action: dropItem"  
# On F press: "📋 Queued MCP action: swapHands"
# Should NOT see spam when holding keys
```

## **Questions to Answer**

1. Are all inventory actions using edge detection correctly?
2. Does drop item always use amount=1 or can it be configured?
3. Do inventory actions work while other actions are active?
4. Are there any UI visual feedback for inventory actions?
5. Do inventory actions interfere with movement/combat?

**DEADLINE**: [SET_DEADLINE]  
**Contact**: [LEAD_DEV] for questions 
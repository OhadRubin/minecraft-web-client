# WebSocket Cursor Drag & Drop Implementation Plan

## Overview

This plan outlines how to implement drag and drop functionality for the Minecraft web client using the WebSocket cursor. The system will allow external controllers to drag items between inventory slots, craft items, and manage equipment.

## Current State

✅ **WebSocket cursor working** - Visible in inventory/modals, controllable via WebSocket
✅ **Inventory system** - Using minecraft-inventory-gui for UI
✅ **Bot integration** - Can perform inventory operations via mineflayer

## Architecture Components

### 1. Enhanced Cursor State (`src/react/WsCursor.tsx`)

```typescript
export const wsCursorState = proxy({
  // Position
  x: 50,
  y: 50,
  display: false,
  usingWsInput: false,
  
  // Drag state
  isDragging: false,
  draggedItem: null as Item | null,
  dragSource: null as { type: 'inventory' | 'hotbar' | 'armor' | 'crafting', slot: number } | null,
  dragStartPosition: { x: 0, y: 0 },
  
  // Visual feedback
  showDropZones: false,
  hoveredSlot: null as { type: string, slot: number } | null,
})
```

### 2. Drag Visual Component (`src/react/DragPreview.tsx`)

```typescript
// Shows the dragged item following the cursor
interface DragPreviewProps {
  item: Item
  cursorX: number
  cursorY: number
}

// Ghost item that follows cursor during drag
// Semi-transparent, shows item icon and count
// Positioned absolutely relative to cursor
```

### 3. Inventory Integration (`src/react/InventoryDragLayer.tsx`)

```typescript
// Overlay for detecting inventory interactions
// Detects cursor position over inventory slots
// Highlights valid drop zones
// Handles slot hover events
```

### 4. WebSocket Commands Extension

```typescript
interface DragCommand extends MouseCommand {
  type: 'dragStart' | 'dragMove' | 'dragEnd' | 'dragCancel'
  
  // dragStart fields
  sourceType?: 'inventory' | 'hotbar' | 'armor' | 'crafting' | 'offhand'
  sourceSlot?: number
  
  // dragMove fields (cursor position handled by existing cursor command)
  
  // dragEnd fields  
  targetType?: string
  targetSlot?: number
  
  // Drag options
  splitStack?: boolean  // Right-click drag (split stack)
  quickMove?: boolean   // Shift-click (quick transfer)
}
```

## Implementation Phases

### Phase 1: Basic Drag Detection 🔍

#### 1.1 Cursor Interaction Detection
- **File**: `src/react/InventorySlotDetector.tsx`
- **Purpose**: Detect which inventory slot cursor is over
- **Implementation**:
  ```typescript
  // Use cursor position to detect slot hover
  const detectSlotAtPosition = (x: number, y: number) => {
    const element = document.elementFromPoint(x, y)
    const slotElement = element?.closest('[data-slot-type][data-slot-id]')
    if (slotElement) {
      return {
        type: slotElement.getAttribute('data-slot-type'),
        slot: parseInt(slotElement.getAttribute('data-slot-id'))
      }
    }
    return null
  }
  ```

#### 1.2 WebSocket Command Handler
- **File**: `src/wsCommandClient.ts` (extend existing)
- **Add drag command cases**:
  ```typescript
  case 'dragStart':
    const sourceSlot = detectSlotAtCursor()
    if (sourceSlot && hasItemAtSlot(sourceSlot)) {
      wsCursorState.isDragging = true
      wsCursorState.draggedItem = getItemAtSlot(sourceSlot)
      wsCursorState.dragSource = sourceSlot
      wsCursorState.showDropZones = true
    }
    break
  ```

### Phase 2: Visual Feedback System 👀

#### 2.1 Drag Preview Component
- **File**: `src/react/DragPreview.tsx`
- **Features**:
  - Semi-transparent item icon following cursor
  - Item count display
  - Stack split indicator for right-click drags
  - Smooth animations

#### 2.2 Drop Zone Highlighting
- **File**: `src/react/DropZoneHighlight.tsx`
- **Features**:
  - Highlight valid drop slots in green
  - Show invalid slots in red
  - Special highlighting for crafting areas
  - Equipment slot validation (armor type checking)

#### 2.3 Inventory Slot Enhancement
- **Extend existing inventory components**
- **Add data attributes**:
  ```jsx
  <div 
    className="inventory-slot"
    data-slot-type="inventory"
    data-slot-id={slotIndex}
    data-accepts={getAcceptedItemTypes(slotIndex)}
  >
  ```

### Phase 3: Drag Operations Logic 🔄

#### 3.1 Drag State Management
- **File**: `src/react/DragStateManager.tsx`
- **Responsibilities**:
  - Track drag lifecycle (start → move → end)
  - Validate drop targets
  - Handle drag cancellation
  - Manage visual state updates

#### 3.2 Inventory Validation
- **File**: `src/utils/inventoryValidation.ts`
- **Functions**:
  ```typescript
  const isValidDrop = (item: Item, targetSlot: SlotInfo) => {
    // Check if item can be placed in target slot
    // Handle armor restrictions, crafting constraints, etc.
  }
  
  const canStackItems = (sourceItem: Item, targetItem: Item) => {
    // Check if items can be stacked together
  }
  ```

### Phase 4: Bot Integration 🤖

#### 4.1 Inventory Operations
- **File**: `src/inventoryOperations.ts`
- **Bot commands**:
  ```typescript
  const performDragOperation = async (operation: DragOperation) => {
    switch (operation.type) {
      case 'move':
        await bot.moveSlotItem(operation.source, operation.target)
        break
      case 'split':
        await bot.splitStack(operation.source, operation.target)
        break
      case 'swap':
        await bot.swapSlots(operation.source, operation.target)
        break
    }
  }
  ```

#### 4.2 State Synchronization
- **Keep UI in sync with bot inventory**
- **Handle operation failures gracefully**
- **Revert visual changes if bot operation fails**

### Phase 5: Advanced Features ⚡

#### 5.1 Crafting Integration
- **Auto-arrange crafting ingredients**
- **Recipe suggestions based on dragged items**
- **Quick-craft with shift-click**

#### 5.2 Smart Stacking
- **Auto-stack similar items when dropping**
- **Fill existing stacks before creating new ones**
- **Merge partial stacks**

#### 5.3 Equipment Management
- **Auto-equip armor when dragged to player**
- **Weapon/tool quick-swap**
- **Off-hand item management**

## WebSocket Protocol

### Command Examples

#### Start Drag
```json
{
  "type": "dragStart",
  "sourceType": "inventory", 
  "sourceSlot": 15
}
```

#### Move During Drag
```json
{
  "type": "cursor",
  "x": 45,
  "z": 60
}
```

#### End Drag (Drop)
```json
{
  "type": "dragEnd",
  "targetType": "hotbar",
  "targetSlot": 2
}
```

#### Cancel Drag
```json
{
  "type": "dragCancel"
}
```

#### Right-Click Drag (Split Stack)
```json
{
  "type": "dragStart",
  "sourceType": "inventory",
  "sourceSlot": 10,
  "splitStack": true
}
```

## Implementation Strategy

### Week 1: Foundation
1. ✅ **Enhanced cursor state management**
2. ✅ **Basic drag detection**  
3. ✅ **WebSocket command structure**

### Week 2: Visual System
4. ✅ **Drag preview component**
5. ✅ **Drop zone highlighting**
6. ✅ **Inventory slot detection**

### Week 3: Core Logic
7. ✅ **Drag state management**
8. ✅ **Validation logic**
9. ✅ **Basic bot integration**

### Week 4: Polish & Advanced
10. ✅ **Error handling**
11. ✅ **Crafting integration**
12. ✅ **Smart stacking features**

## Technical Considerations

### Performance
- **Debounce cursor position updates** (16ms for 60fps)
- **Optimize slot detection** (cache slot positions)
- **Batch inventory operations** (reduce bot command spam)

### Error Handling
- **Network failures** - Revert visual state
- **Invalid operations** - Show error feedback
- **Bot desync** - Refresh inventory state

### Accessibility
- **Keyboard navigation** fallback
- **Screen reader** support for drag operations
- **High contrast** mode for drop zones

## Integration Points

### Existing Systems
- **minecraft-inventory-gui**: Hook into existing inventory rendering
- **WsCursor**: Extend current cursor functionality  
- **Bot inventory**: Use existing mineflayer inventory methods
- **Touch controls**: Add touch drag support later

### External Controllers
- **Pygame controller**: Add drag buttons and gestures
- **Mobile touch**: Future touch drag implementation
- **LLM controller**: AI can perform complex inventory management

## Success Criteria

### Functional Requirements
- ✅ **Full stack drag**: Move any item between any valid slots
- ✅ **Stack splitting**: Right-click drag to split stacks
- ✅ **Quick transfer**: Shift-click equivalent operations  
- ✅ **Crafting**: Drag items to crafting grid, drag results out
- ✅ **Equipment**: Drag armor/tools to equipment slots
- ✅ **Error recovery**: Handle failures gracefully

### Performance Requirements
- ✅ **Smooth dragging**: 60fps cursor movement
- ✅ **Low latency**: <50ms response to drag commands
- ✅ **Reliable sync**: No inventory desync issues

### UX Requirements  
- ✅ **Visual feedback**: Clear drag preview and drop zones
- ✅ **Intuitive controls**: Familiar drag patterns
- ✅ **Error messages**: Clear feedback for invalid operations

## Testing Strategy

### Unit Tests
- Drag state management logic
- Slot detection algorithms  
- Validation functions
- Bot operation wrappers

### Integration Tests
- Full drag operations end-to-end
- Multi-slot operations (crafting)
- Error scenarios and recovery
- Performance under load

### Manual Test Scenarios
1. **Basic item movement** - Drag item from inventory to hotbar
2. **Stack operations** - Split stacks, merge stacks
3. **Crafting workflow** - Craft wooden pickaxe using only cursor
4. **Equipment management** - Equip full armor set
5. **Chest interaction** - Transfer items to/from chests
6. **Error handling** - Network failures during drag
7. **Complex operations** - Organize full inventory

## Future Enhancements

### Smart Features
- **Auto-sort inventory** - One-command organization
- **Recipe assistant** - Highlight missing ingredients  
- **Bulk operations** - Move all items of type
- **Favorites system** - Quick-access to commonly used items

### Advanced Interactions
- **Multi-select** - Drag multiple items at once
- **Gesture controls** - Swipe patterns for common operations
- **Voice commands** - "Move all wood to chest"
- **AI assistance** - "Prepare for mining expedition"

---

This plan provides a comprehensive roadmap for implementing professional-grade drag and drop functionality that will make the Minecraft web client fully capable for complex inventory management via external controllers. 
# Implementation Plan: Enhanced Minecraft Web Client Features

## Overview
Our goal is to add missing features to make the Minecraft web client fully capable for survival gameplay. This includes inventory cursor control, item management, and enhanced interaction capabilities.

## Current Architecture Analysis

### Existing Systems
- **WebSocket Command System** (`src/wsCommandClient.ts`): Handles mouse, movement, and interaction commands
- **Touch Controls** (`src/react/TouchAreasControls.tsx`): Modern touch interface with joystick and action buttons
- **Inventory System** (`src/inventoryWindows.ts`): Uses minecraft-inventory-gui for container interfaces
- **Controls Framework** (`src/controls.ts`): ControMax-based input system
- **External Controllers**: Pygame controller with WebSocket communication

### Missing Features
1. **Visual Cursor for Web Interface** 
2. **Inventory Cursor Control** (drag/drop, crafting, armor)
3. **Item Drop/Throw** functionality
4. **Off-hand & Armor Management**
5. **Hotbar Scrolling**
6. **Enhanced Consumables/Eating**

## Implementation Strategy

### Phase 1: Visual Cursor System 🖱️

#### 1.1 Create Web Interface Cursor Component
- **File**: `src/react/WebCursor.tsx`
- **Purpose**: Visual cursor that follows mouse/gamepad/touch input
- **Features**:
  - Customizable cursor styles (arrow, hand, crosshair)
  - Smooth movement animations
  - Different states for different contexts (menu, game, inventory)
  - Hide/show based on input method

#### 1.2 Cursor State Management  
- **File**: `src/react/WebCursorProvider.tsx`
- **Purpose**: Global cursor state management
- **State Properties**:
  ```typescript
  {
    x: number,          // Screen percentage 0-100
    y: number,          // Screen percentage 0-100
    visible: boolean,   // Show/hide cursor
    style: 'arrow' | 'hand' | 'crosshair' | 'grabbing',
    isMoving: boolean,  // For animation states
  }
  ```

#### 1.3 WebSocket Cursor Commands
- **File**: Extend `src/wsCommandClient.ts`
- **New Command Types**:
  ```typescript
  {
    type: 'cursor'
    action: 'move' | 'show' | 'hide' | 'setStyle'
    x?: number
    y?: number
    style?: string
  }
  ```

### Phase 2: Enhanced Inventory Controls 🎒

#### 2.1 Inventory Cursor Integration
- **File**: Extend `src/inventoryWindows.ts`
- **Features**:
  - Visual cursor overlay in inventory screens
  - Slot highlighting on hover
  - Drag preview (ghost item following cursor)
  - Drop zones visualization

#### 2.2 Drag & Drop System
- **Implementation**: Extend minecraft-inventory-gui integration
- **Features**:
  - **Left-click drag**: Move full stack
  - **Right-click drag**: Split stack (half)
  - **Shift-click**: Quick transfer
  - **Ctrl-click**: Move single item
  - **Drop zones**: Inventory slots, hotbar, equipment, off-hand

#### 2.3 Crafting Interface Enhancement
- **Features**:
  - Drag items to crafting grid
  - Recipe auto-complete on hover
  - Quick craft (Shift+click result)
  - Recipe book integration

### Phase 3: Item Management Features 📦

#### 3.1 Item Drop/Throw System
- **File**: `src/react/ItemActions.tsx`
- **WebSocket Commands**:
  ```typescript
  {
    type: 'itemAction'
    action: 'drop' | 'throw'
    slot?: number      // Hotbar slot or inventory slot
    amount?: number    // 1 for single, stack for all
  }
  ```
- **UI Elements**:
  - Drop button in inventory
  - Hotkey support (Q key)
  - Long-press for full stack drop

#### 3.2 Off-hand & Armor Management  
- **File**: Extend `src/inventoryWindows.ts`
- **Features**:
  - Off-hand slot visualization
  - Armor slots with drag/drop support  
  - Equipment validation (correct armor types)
  - Visual feedback for equipped items

#### 3.3 Enhanced Hotbar Controls
- **File**: `src/react/HotbarControls.tsx`
- **Features**:
  - Scroll wheel support for slot cycling
  - Visual hotbar with item previews
  - Quick hotbar slot selection (1-9 keys)
  - Hotbar slot swapping

### Phase 4: Advanced Gameplay Features 🍖

#### 4.1 Consumables & Eating System
- **File**: `src/react/ConsumablesManager.tsx`
- **Features**:
  - Auto-eat when low on hunger
  - Hold-to-eat progress indicator  
  - Quick food access (prioritize best food)
  - Eating animation feedback

#### 4.2 Enhanced Touch Controls
- **File**: Extend `src/react/TouchAreasControls.tsx`
- **New Buttons**:
  - Inventory button
  - Drop item button  
  - Off-hand swap button
  - Hotbar scroll buttons (next/prev)

### Phase 5: External Controller Integration 🎮

#### 5.1 Pygame Controller Enhancement
- **File**: `pygame_controller.py` (external)
- **New Features**:
  - Cursor movement simulation
  - Inventory controls
  - Item management buttons
  - Hotbar scrolling

#### 5.2 WebSocket API Extensions
- **File**: `src/wsCommandClient.ts`
- **New Command Categories**:
  ```typescript
  // Hotbar management
  { type: 'setHotbarSlot', slot: 0-8 }
  { type: 'scrollHotbar', direction: 1 | -1 }
  
  // Inventory actions  
  { type: 'inventoryClick', slot: number, button: 0|1|2, mode: string }
  { type: 'inventoryDrag', from: number, to: number, amount?: number }
  
  // Item actions
  { type: 'dropItem', slot?: number, amount?: number }
  { type: 'swapHands' }
  ```

## Technical Implementation Details

### Component Architecture
```
src/react/
├── WebCursor.tsx              # Visual cursor component
├── WebCursorProvider.tsx      # Cursor state management
├── InventoryCursor.tsx        # Inventory-specific cursor
├── ItemActions.tsx            # Drop/throw/swap actions
├── HotbarControls.tsx         # Enhanced hotbar
├── ConsumablesManager.tsx     # Food/potion management
└── TouchInventoryControls.tsx # Touch-specific inventory controls
```

### State Management
```typescript
// Global cursor state
export const webCursorState = proxy({
  position: { x: 50, y: 50 },
  visible: true,
  style: 'arrow' as CursorStyle,
  isMoving: false,
})

// Inventory interaction state  
export const inventoryInteractionState = proxy({
  draggedItem: null as Item | null,
  dragSource: null as number | null,
  hoveredSlot: null as number | null,
  showDropZones: false,
})
```

### WebSocket Protocol Extensions
```typescript
interface EnhancedMouseCommand extends MouseCommand {
  // Existing types +
  type: 'cursor' | 'inventoryAction' | 'itemDrop' | 'hotbarScroll'
  
  // Cursor specific
  cursorStyle?: 'arrow' | 'hand' | 'crosshair' | 'grabbing'
  
  // Inventory specific
  sourceSlot?: number
  targetSlot?: number
  dragAmount?: number
  clickMode?: 'normal' | 'shift' | 'ctrl'
  
  // Item actions
  dropAmount?: number | 'all'
}
```

## Implementation Priorities

### High Priority (Week 1-2)
1. ✅ **Visual Cursor System** - Essential for all other features
2. ✅ **Basic Inventory Cursor** - Core functionality
3. ✅ **WebSocket Command Extensions** - Communication layer

### Medium Priority (Week 3-4) 
4. ✅ **Drag & Drop System** - Full inventory management
5. ✅ **Item Drop/Throw** - Basic survival needs
6. ✅ **Hotbar Scrolling** - Improved UX

### Lower Priority (Week 5+)
7. ✅ **Advanced Consumables** - Quality of life
8. ✅ **Touch Control Enhancement** - Mobile experience
9. ✅ **External Controller Updates** - Pygame integration

## Success Metrics

### Functional Requirements
- [ ] **Inventory Management**: Drag/drop any item between any valid slots
- [ ] **Crafting**: Create items using cursor-based crafting interface
- [ ] **Equipment**: Equip armor and tools via drag/drop
- [ ] **Item Actions**: Drop, throw, swap hands reliably
- [ ] **Hotbar**: Cycle through slots with scroll/buttons
- [ ] **Survival Ready**: Can complete basic survival tasks without keyboard

### Technical Requirements  
- [ ] **Performance**: Cursor responds within 16ms (60fps)
- [ ] **Compatibility**: Works with mouse, touch, gamepad, external controllers
- [ ] **Reliability**: Zero inventory desync issues
- [ ] **UX**: Intuitive controls matching native Minecraft feel

## Testing Strategy

### Unit Tests
- Cursor state management
- WebSocket command parsing
- Inventory slot validation
- Item stack calculations

### Integration Tests
- Pygame controller → WebSocket → Game actions
- Touch controls → Inventory interactions
- Gamepad → Cursor movement → Inventory

### Manual Testing Scenarios
1. **Crafting a wooden pickaxe** using only cursor controls
2. **Organizing full inventory** with drag/drop
3. **Equipping armor set** from chest to player
4. **Food management** during low hunger
5. **Combat** with weapon switching and healing

## Risk Mitigation

### Technical Risks
- **Inventory Desync**: Implement client-side validation + server reconciliation
- **Performance**: Throttle cursor updates, use RequestAnimationFrame
- **Touch Lag**: Optimize touch event handling, reduce DOM manipulations

### UX Risks  
- **Learning Curve**: Provide interactive tutorial/hints system
- **Muscle Memory**: Keep controls similar to existing Minecraft interfaces
- **Accessibility**: Support keyboard navigation as fallback

## Dependencies & Prerequisites

### Required Libraries
- `minecraft-inventory-gui`: Already integrated ✅
- `valtio`: State management ✅
- `@emotion/css`: Styling ✅
- WebSocket implementation ✅

### Development Prerequisites
- Understanding of Minecraft inventory mechanics
- WebSocket debugging tools
- Multiple input device testing setup
- Minecraft server for integration testing

## Next Steps

1. **Set up development environment** with all testing devices
2. **Create basic cursor component** and verify WebSocket integration  
3. **Implement drag/drop proof of concept** with two inventory slots
4. **Iterate based on user feedback** and performance metrics
5. **Gradually add advanced features** following priority order

---

*This plan provides a comprehensive roadmap for implementing full survival-ready inventory and item management features. Each phase builds upon the previous, ensuring a stable foundation while progressively adding capabilities.* 
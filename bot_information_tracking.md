# Bot Information Tracking Documentation

## Overview
This document outlines the key information that should be tracked and reported by the Minecraft bot system, along with the appropriate locations for implementing this tracking.

## Information to Track

### 1. Entity Position and State
**What to track:**
- `bot.entity.position.floored()` - The bot's current block coordinates
- `bot.entity.yaw` - Horizontal rotation (in radians, convert to degrees for output)
- `bot.entity.pitch` - Vertical rotation (in radians, convert to degrees for output)
- Cardinal direction (calculated from yaw)

**Entity Status Flags (but only if they are true):**
- `bot.entity.isFlying`
- `bot.entity.isInLava`
- `bot.entity.isInWater`
- `bot.entity.isInWeb`
- `bot.entity.isInvulnerable`
- `bot.entity.isUnderLava`
- `bot.entity.isUnderWater`

### 2. Block Information
**Current Target Block:**
- `bot.blockAtCursor()` - The block the bot is currently looking at
- If block is null: "pointing at a block that is too far away"
- If block exists:
  - `block.displayName` - Human-readable block name
  - `bot.canDigBlock(block)` - Whether the block can be mined
  - `block.biome` - The biome information

### 3. Calculated Information
**Cardinal Direction:**
Convert yaw (radians) to cardinal direction:
- North: yaw ≈ 0 or ≈ 2π
- East: yaw ≈ π/2
- South: yaw ≈ π
- West: yaw ≈ 3π/2

### 4. Biome
`biome = bot.blockAt(bot.player.entity.position).biome`
print out biome.displayName

### 5. Inventory Information
**Currently Selected Slot:**
- `bot.quickBarSlot` - The currently selected hotbar slot (0-8)

**Hotbar Items:**
To access hotbar slots and return only non-empty slots:
```typescript
// For each slot 0-8, if not empty, return:
item = bot.inventory.slots[bot.inventory.hotbarStart + slotId] // slotId is 0-8
item.displayName 
item.count
```

### 6. Time Information
**Time Fields:**
- `bot.time.timeOfDay` - Time of the day, in ticks
- `bot.time.day` - Day of the world  
- `bot.time.isDay` - Whether it is day or not

**Time System:**
- Time is based on ticks, where 20 ticks happen every second
- There are 24000 ticks in a day, making Minecraft days exactly 20 minutes long
- 0 is sunrise, 6000 is noon, 12000 is sunset, and 18000 is midnight
- Day is between 0 and 13000 ticks (day + sunset)

**Time Until Sunset/Sunrise:**
Calculate how long (in minutes) until the next sunset or sunrise:
- If `bot.time.timeOfDay < 12000` (daytime): time until sunset = `(12000 - bot.time.timeOfDay) / 1200` minutes
- If `bot.time.timeOfDay >= 12000` (nighttime): time until sunrise = `(24000 - bot.time.timeOfDay) / 1200` minutes

## Implementation Locations

### Primary Location: MCP Server Tools
**File:** `minecraft-mcp-server.ts`

**Where to add:** Create a new tool called `getBotStatus` that returns comprehensive bot information.

```typescript
server.addTool({
    name: "getBotStatus",
    description: "Get comprehensive information about the bot's current state",
    parameters: z.object({}),
    execute: async (args) => {
        // Request bot status from WebSocket client
        // Return formatted status information
    },
});
```

### Secondary Location: WebSocket Command Client
**File:** `src/wsCommandClient.ts`

**Where to add:** Add a new command type `'getBotStatus'` in the `MouseCommand` interface and implement in the `TouchEvaluator.execute()` method.

```typescript
// Add to MouseCommand interface
interface MouseCommand {
  type: 
  | 'getBotStatus'  // <-- Add this
  | 'control'
  | 'leftDown'
  // ... existing types
}

// Add to TouchEvaluator.execute() switch statement
case 'getBotStatus':
  try {
    const status = collectBotStatus();
    if (this.ws) {
      this.ws.send(JSON.stringify({
        type: 'botStatus',
        data: status
      }));
    }
  } catch (error) {
    console.error('[WsCommandClient] Error getting bot status:', error);
  }
  break;
```

### Helper Functions to Implement

#### 1. Cardinal Direction Calculator
```typescript
function getCardinalDirection(yaw: number): string {
  // Convert yaw (radians) to degrees
  let degrees = (yaw * 180 / Math.PI + 360) % 360;
  
  if (degrees >= 315 || degrees < 45) return "North";
  else if (degrees >= 45 && degrees < 135) return "East";
  else if (degrees >= 135 && degrees < 225) return "South";
  else return "West";
}
```

#### 2. Bot Status Collector
```typescript
function collectBotStatus() {
  const position = bot.entity.position.floored();
  const block = bot.blockAtCursor();
  const currentBiome = bot.blockAt(bot.entity.position).biome;
  
  // Only include entity status flags that are true
  const activeEntityStates: any = {};
  if (bot.entity.isFlying) activeEntityStates.isFlying = true;
  if (bot.entity.isInLava) activeEntityStates.isInLava = true;
  if (bot.entity.isInWater) activeEntityStates.isInWater = true;
  if (bot.entity.isInWeb) activeEntityStates.isInWeb = true;
  if (bot.entity.isInvulnerable) activeEntityStates.isInvulnerable = true;
  if (bot.entity.isUnderLava) activeEntityStates.isUnderLava = true;
  if (bot.entity.isUnderWater) activeEntityStates.isUnderWater = true;
  
  // Collect hotbar items (only non-empty slots)
  const hotbarItems: any = {};
  for (let i = 0; i < 9; i++) {
    const item = bot.inventory.slots[bot.QUICK_BAR_START + i];
    if (item) {
      hotbarItems[i] = {
        displayName: item.displayName,
        count: item.count
      };
    }
  }
  
  // Calculate time until sunset/sunrise
  const timeOfDay = bot.time.timeOfDay;
  let timeUntilNext: { event: string, minutes: number };
  
  if (timeOfDay < 12000) {
    // Daytime - calculate time until sunset
    const minutesUntilSunset = (12000 - timeOfDay) / 1200;
    timeUntilNext = { event: "sunset", minutes: Math.round(minutesUntilSunset * 100) / 100 };
  } else {
    // Nighttime - calculate time until sunrise
    const minutesUntilSunrise = (24000 - timeOfDay) / 1200;
    timeUntilNext = { event: "sunrise", minutes: Math.round(minutesUntilSunrise * 100) / 100 };
  }
  
  return {
    position: {
      x: position.x,
      y: position.y,
      z: position.z
    },
    rotation: {
      yaw: Math.round((bot.entity.yaw * 180 / Math.PI) * 100) / 100, // Convert to degrees
      pitch: Math.round((bot.entity.pitch * 180 / Math.PI) * 100) / 100, // Convert to degrees
      cardinalDirection: getCardinalDirection(bot.entity.yaw)
    },
    biome: {
      displayName: currentBiome.displayName
    },
    inventory: {
      currentSlot: bot.quickBarSlot,
      hotbarItems: hotbarItems
    },
    time: {
      timeOfDay: bot.time.timeOfDay,
      day: bot.time.day,
      isDay: bot.time.isDay,
      timeUntilNext: timeUntilNext
    },
    entityState: activeEntityStates, // Only includes flags that are true
    targetBlock: block ? {
      displayName: block.displayName,
      canDig: bot.canDigBlock(block),
      biome: block.biome,
      position: block.position
    } : {
      message: "pointing at a block that is too far away"
    }
  };
}
```

## Usage Patterns

### 1. Automatic Status Updates
Add status information to existing tools (like `walk`, `lookAngle`) so every action includes current bot state.

### 2. Dedicated Status Tool
Create a standalone `getBotStatus` tool that can be called anytime to get comprehensive information.

### 3. Periodic Status Broadcasting
Optionally implement periodic status updates that are sent automatically at regular intervals.

## Data Format
The status information should be returned in a structured format that's easy for the MCP client to parse and use for decision-making.

```json
{
  "position": { "x": 100, "y": 64, "z": 200 },
  "rotation": { "yaw": 90.0, "pitch": -15.5, "cardinalDirection": "East" },
  "biome": { "displayName": "Forest" },
  "inventory": {
    "currentSlot": 2,
    "hotbarItems": {
      "0": { "displayName": "Diamond Sword", "count": 1 },
      "2": { "displayName": "Oak Wood", "count": 32 },
      "5": { "displayName": "Cooked Beef", "count": 16 }
    }
  },
  "time": {
    "timeOfDay": 8000,
    "day": 5,
    "isDay": true,
    "timeUntilNext": { "event": "sunset", "minutes": 3.33 }
  },
  "entityState": { "isInWater": true },
  "targetBlock": { "displayName": "Oak Log", "canDig": true, "biome": "forest" }
}
```

**Note:** 
- `entityState` will only contain flags that are currently true
- `hotbarItems` will only contain slots that have items (empty slots are omitted)
- `timeUntilNext` shows either time until sunset (if daytime) or time until sunrise (if nighttime)
- `yaw` and `pitch` are converted from radians to degrees for easier readability

## Implementation Priority
1. **First:** Add `getBotStatus` command to WebSocket client
2. **Second:** Add corresponding MCP tool in server
3. **Third:** Integrate status info into existing tools
4. **Fourth:** Add automatic status broadcasting (optional) 



currently selected slot
bot.quickBarSlot
To access a hotbar slot:
```
item = bot.inventory.slots[bot.QUICK_BAR_START + slotId] // slotId is 0-8
// return theses for all 0-8 if they are not empty
item.displayName 
//and
item.count

```
explanation of fields:
```
bot.time.timeOfDay
Time of the day, in ticks.

Time is based on ticks, where 20 ticks happen every second. There are 24000 ticks in a day, making Minecraft days exactly 20 minutes long.

The time of day is based on the timestamp modulo 24000. 0 is sunrise, 6000 is noon, 12000 is sunset, and 18000 is midnight.

bot.time.day
Day of the world.

bot.time.isDay
Whether it is day or not.

Based on whether the current time of day is between 0 and 13000 ticks (day + sunset).
```


what I want to add: how long (in minutes) until sunset/sunrise.
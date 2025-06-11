from __future__ import annotations

import re
import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Awaitable


@dataclass(eq=True, frozen=True)
class Position:
    x: float
    y: float
    z: float


@dataclass(eq=True, frozen=True)
class Rotation:
    yaw: float
    pitch: float
    cardinal_direction: str


@dataclass(eq=True, frozen=True)
class HotbarItem:
    slot: int
    name: str
    count: int


@dataclass(eq=True, frozen=True)
class BotStatus:
    position: Position
    rotation: Rotation
    biome: Optional[str] = None
    day: Optional[int] = None
    minutes_until_event: Optional[float] = None
    next_event: Optional[str] = None
    selected_slot: Optional[int] = None
    hotbar: List[HotbarItem] = field(default_factory=list)
    looking_at: Optional[str] = None


POSITION_RE = re.compile(r"Position:\s*\(([-\d\.]+),\s*([-\d\.]+),\s*([-\d\.]+)\)\s*facing\s+([A-Za-z]+)\s*\(([-\d\.]+)°,\s*([-\d\.]+)°\)")
BIOME_RE = re.compile(r"Biome:\s*(.+)")
DAY_RE = re.compile(r"Day\s+(\d+),\s*([\d\.]+)\s*minutes\s*until\s*(\w+)")
SLOT_RE = re.compile(r"Selected slot:\s*(\d+)")
HOTBAR_ITEM_RE = re.compile(r"\[(\d+):\s*([^\]]+)\sx(\d+)\]")
LOOKING_RE = re.compile(r"Looking at:\s*(.+)")


def parse_bot_status(text: str) -> BotStatus:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip() and not line.startswith("====")]
    position = Position(0.0, 0.0, 0.0)
    rotation = Rotation(0.0, 0.0, "")
    biome = None
    day = None
    minutes_until_event = None
    next_event = None
    selected_slot = None
    hotbar: List[HotbarItem] = []
    looking_at = None

    for line in lines:
        if m := POSITION_RE.search(line):
            position = Position(float(m.group(1)), float(m.group(2)), float(m.group(3)))
            rotation = Rotation(float(m.group(5)), float(m.group(6)), m.group(4))
        elif m := BIOME_RE.search(line):
            biome = m.group(1)
        elif m := DAY_RE.search(line):
            day = int(m.group(1))
            minutes_until_event = float(m.group(2))
            next_event = m.group(3)
        elif m := SLOT_RE.search(line):
            selected_slot = int(m.group(1))
        elif m := HOTBAR_ITEM_RE.search(line):
            for match in HOTBAR_ITEM_RE.finditer(line):
                hotbar.append(
                    HotbarItem(int(match.group(1)), match.group(2), int(match.group(3)))
                )
        elif m := LOOKING_RE.search(line):
            looking_at = m.group(1)

    return BotStatus(
        position=position,
        rotation=rotation,
        biome=biome,
        day=day,
        minutes_until_event=minutes_until_event,
        next_event=next_event,
        selected_slot=selected_slot,
        hotbar=hotbar,
        looking_at=looking_at,
    )


async def wait_for_state_stable(
    get_status: Callable[[], Awaitable[str]],
    *,
    attempts: int = 3,
    interval: float = 0.1,
    timeout: float = 5.0,
) -> BotStatus:
    """Wait until get_status returns identical BotStatus for `attempts` times."""

    last_status: Optional[BotStatus] = None
    stable_count = 0
    start = asyncio.get_event_loop().time()

    while True:
        text = await get_status()
        status = parse_bot_status(text)
        if status == last_status:
            stable_count += 1
            if stable_count >= attempts:
                return status
        else:
            stable_count = 1
            last_status = status

        if asyncio.get_event_loop().time() - start > timeout:
            raise TimeoutError("State did not stabilize within timeout")

        await asyncio.sleep(interval)


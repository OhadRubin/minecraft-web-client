import asyncio
import pytest

from getbotstatus_parser import (
    parse_bot_status,
    wait_for_state_stable,
    Position,
    Rotation,
    HotbarItem,
)

SAMPLE_STATUS = """====
Position: (30, 63, -18) facing East (-288.15°, -2.55°)
Biome: Sparse Jungle
Day 0, 8.71 minutes until sunset
Selected slot: 1
Hotbar: [0: Oak Sapling x3] [1: Jungle Log x1]
Looking at: Vines (is close enough to dig)
===="""


def test_parse_bot_status_basic():
    status = parse_bot_status(SAMPLE_STATUS)
    assert status.position == Position(30.0, 63.0, -18.0)
    assert status.rotation == Rotation(-288.15, -2.55, "East")
    assert status.biome == "Sparse Jungle"
    assert status.day == 0
    assert status.minutes_until_event == 8.71
    assert status.next_event == "sunset"
    assert status.selected_slot == 1
    assert status.hotbar == [
        HotbarItem(0, "Oak Sapling", 3),
        HotbarItem(1, "Jungle Log", 1),
    ]
    assert status.looking_at.startswith("Vines")


class Dummy:
    def __init__(self):
        self.calls = 0

    async def get(self) -> str:
        self.calls += 1
        # first call returns same text, second call also same -> stable after two calls
        return SAMPLE_STATUS


@pytest.mark.asyncio
async def test_wait_for_state_stable():
    dummy = Dummy()
    status = await wait_for_state_stable(dummy.get, attempts=2, interval=0.01, timeout=1)
    assert status.position.x == 30.0
    assert dummy.calls >= 2


MISSING_STATUS = """====
Position: (10, 64, 20) facing South (180°, 0°)
===="""

WRAP_STATUS = """====
Position: (0, 64, 0) facing North (361°, -1°)
Hotbar: [0: Dirt x64] [1: Stone x64] [2: Stick x10]
===="""

class Flapping:
    def __init__(self):
        self.state = False

    async def get(self) -> str:
        self.state = not self.state
        if self.state:
            return SAMPLE_STATUS
        return SAMPLE_STATUS.replace("East", "West")


def test_parse_bot_status_missing_fields():
    status = parse_bot_status(MISSING_STATUS)
    assert status.position == Position(10.0, 64.0, 20.0)
    assert status.rotation == Rotation(180.0, 0.0, "South")
    assert status.biome is None
    assert status.hotbar == []
    assert status.looking_at is None


def test_parse_bot_status_wraparound():
    status = parse_bot_status(WRAP_STATUS)
    assert status.rotation.yaw == 361.0
    assert len(status.hotbar) == 3
    assert status.hotbar[0] == HotbarItem(0, "Dirt", 64)


@pytest.mark.asyncio
async def test_wait_for_state_stable_timeout():
    flapping = Flapping()
    with pytest.raises(TimeoutError):
        await wait_for_state_stable(flapping.get, attempts=3, interval=0.01, timeout=0.2)
PRECISION_STATUS = """====
Position: (-1024.125, 64.5, 2048.875) facing West (270.123°, -45.987°)
Biome: Plains
Day 1, 12.5 minutes until sunrise
Selected slot: 2
Hotbar: [0: Torch x64] [2: Diamond Pickaxe x1]
===="""

class Oscillating:
    def __init__(self):
        self.count = 0

    async def get(self) -> str:
        self.count += 1
        if self.count == 1:
            return SAMPLE_STATUS.replace("Jungle Log", "Oak Log")
        return SAMPLE_STATUS


def test_parse_bot_status_precision():
    status = parse_bot_status(PRECISION_STATUS)
    assert status.position == Position(-1024.125, 64.5, 2048.875)
    assert status.rotation == Rotation(270.123, -45.987, "West")
    assert status.hotbar[-1] == HotbarItem(2, "Diamond Pickaxe", 1)


@pytest.mark.asyncio
async def test_wait_for_state_stable_recovers():
    osc = Oscillating()
    status = await wait_for_state_stable(osc.get, attempts=2, interval=0.01, timeout=1)
    assert status.hotbar[1].name == "Jungle Log"
    assert osc.count >= 3

# Additional edge case samples
NEGATIVE_ROT_STATUS = """====
Position: (0, 64, 0) facing West (-450°, 10°)
Hotbar: [0: Dirt x1]
Looking at: Stone (cannot dig - too far away)
===="""

NO_HOTBAR_STATUS = """====
Position: (5, 65, -5) facing North (0°, 0°)
Hotbar:
===="""


def test_parse_bot_status_negative_rotation():
    status = parse_bot_status(NEGATIVE_ROT_STATUS)
    assert status.rotation.yaw == -450.0
    assert status.rotation.pitch == 10.0
    assert status.looking_at.startswith("Stone")


def test_parse_bot_status_no_hotbar_items():
    status = parse_bot_status(NO_HOTBAR_STATUS)
    assert status.hotbar == []
    assert status.selected_slot is None


class Immediate:
    async def get(self) -> str:
        return SAMPLE_STATUS


@pytest.mark.asyncio
async def test_wait_for_state_stable_immediate():
    immediate = Immediate()
    status = await wait_for_state_stable(immediate.get, attempts=1, interval=0.01, timeout=0.5)
    assert status.rotation.cardinal_direction == "East"


# Additional edge cases
MISSING_POSITION_STATUS = """====
Biome: Forest
Day 3, 1.5 minutes until sunrise
Selected slot: 0
Hotbar: [0: Dirt x1]
===="""

LINE_ORDER_STATUS = """====
Hotbar: [0: Dirt x64] [1: Stone x64]
Looking at: Grass Block (is too far away)
Day 2, 5.0 minutes until sunrise
Position: (1, 2, 3) facing North (0°, 0°)
Biome: Plains
Selected slot: 1
===="""

MULTILINE_HOTBAR_STATUS = """====
Position: (0, 64, 0) facing South (90°, 0°)
Hotbar: [0: Stone x64]
[1: Stick x1]
===="""


def test_parse_bot_status_missing_position():
    status = parse_bot_status(MISSING_POSITION_STATUS)
    assert status.position == Position(0.0, 0.0, 0.0)
    assert status.rotation == Rotation(0.0, 0.0, "")
    assert status.biome == "Forest"
    assert status.hotbar == [HotbarItem(0, "Dirt", 1)]


def test_parse_bot_status_line_order():
    status = parse_bot_status(LINE_ORDER_STATUS)
    assert status.position == Position(1.0, 2.0, 3.0)
    assert status.hotbar[0].name == "Dirt"
    assert status.looking_at.startswith("Grass Block")


def test_parse_bot_status_multiline_hotbar():
    status = parse_bot_status(MULTILINE_HOTBAR_STATUS)
    assert len(status.hotbar) == 2
    assert status.hotbar[1] == HotbarItem(1, "Stick", 1)

# New edge case samples
DUPLICATE_POSITION_STATUS = """====
Position: (0, 0, 0) facing North (0°, 0°)
Biome: Plains
Position: (1, 2, 3) facing South (180°, 0°)
Hotbar: [0: Dirt x64]
===="""

CRLF_STATUS = "====\r\nPosition: (2, 3, 4) facing East (90°, 0°)\r\nBiome: Desert\r\n====\r\n"

UNKNOWN_LINE_STATUS = """====
Foo: bar
Position: (5, 5, 5) facing West (270°, 0°)
Baz: qux
===="""

class GradualStable:
    def __init__(self):
        self.calls = 0

    async def get(self) -> str:
        self.calls += 1
        if self.calls <= 3:
            return SAMPLE_STATUS.replace("East", f"East-{self.calls}")
        return SAMPLE_STATUS


def test_parse_bot_status_duplicate_position():
    status = parse_bot_status(DUPLICATE_POSITION_STATUS)
    assert status.position == Position(1.0, 2.0, 3.0)
    assert status.rotation.cardinal_direction == "South"


def test_parse_bot_status_crlf_newlines():
    status = parse_bot_status(CRLF_STATUS)
    assert status.position == Position(2.0, 3.0, 4.0)
    assert status.biome == "Desert"


def test_parse_bot_status_unknown_lines():
    status = parse_bot_status(UNKNOWN_LINE_STATUS)
    assert status.position == Position(5.0, 5.0, 5.0)
    assert status.rotation.cardinal_direction == "West"


@pytest.mark.asyncio
async def test_wait_for_state_stable_delayed():
    stable = GradualStable()
    status = await wait_for_state_stable(stable.get, attempts=2, interval=0.01, timeout=1)
    assert status.rotation.cardinal_direction == "East"
    assert stable.calls >= 4

MULTI_BIOME_STATUS = """====
Biome: Plains
Biome: Desert
Position: (2, 65, 2) facing East (90°, 0°)
===="""

class ExplodingProvider:
    def __init__(self):
        self.called = False
    async def get(self) -> str:
        if not self.called:
            self.called = True
            return SAMPLE_STATUS
        raise RuntimeError("boom")


def test_parse_bot_status_multiple_biomes():
    status = parse_bot_status(MULTI_BIOME_STATUS)
    assert status.biome == "Desert"
    assert status.position == Position(2.0, 65.0, 2.0)


@pytest.mark.asyncio
async def test_wait_for_state_stable_propagates_exception():
    provider = ExplodingProvider()
    with pytest.raises(RuntimeError):
        await wait_for_state_stable(provider.get, attempts=2, interval=0.01, timeout=1)

SPACED_STATUS = """====
Position:    (1, 2, 3)     facing   North   (0°, 0°)
Hotbar:    [0: Dirt x1]    [1: Stone x2]
===="""

def test_parse_bot_status_extra_spaces():
    status = parse_bot_status(SPACED_STATUS)
    assert status.position == Position(1.0, 2.0, 3.0)
    assert status.rotation.cardinal_direction == "North"
    assert status.hotbar[1] == HotbarItem(1, "Stone", 2)

MULTI_DAY_STATUS = """====
Day 1, 10.0 minutes until sunrise
Day 2, 5.0 minutes until sunset
Position: (1, 64, 1) facing North (0°, 0°)
===="""

TRAILING_WS_STATUS = "====\nPosition: (2, 65, 2) facing West (270°, 0°)   \nBiome: Desert   \n====   "


def test_parse_bot_status_multiple_day_lines():
    status = parse_bot_status(MULTI_DAY_STATUS)
    assert status.day == 2
    assert status.minutes_until_event == 5.0
    assert status.next_event == "sunset"


def test_parse_bot_status_trailing_whitespace():
    status = parse_bot_status(TRAILING_WS_STATUS)
    assert status.position == Position(2.0, 65.0, 2.0)
    assert status.biome == "Desert"


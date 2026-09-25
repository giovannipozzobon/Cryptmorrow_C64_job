"""The dungeon as text: grid, room files, zones, openings, doors, the
portal, objects and enemies.

Reads rooms/dungeon.txt and the room files, and checks everything the
C64 program takes for granted: every opening leads to a room with the
same opening facing it, doors, objects and enemies are where they can
work, and
the whole game can be completed (`solve`). The tile pictures are chosen
elsewhere (build_assets.py); this module only reads and checks text.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRID = 4                        # the dungeon is GRID x GRID rooms
MAP_W, MAP_H = 20, 10           # metatiles per room

WALLS = "#Ttrn"                 # symbols that are masonry
GROUND = ".mEPbWADgwu"          # symbols standing on the floor
SYMBOLS = WALLS + GROUND + "G"
OPENINGS = "ED"                 # an opening, open or locked
WALKABLE_INSIDE = ".mbg"        # what may lie behind an opening
OBJECT_GROUND = ".mbg"          # what an object may lie on
SIDES = {"north": (-GRID, "south"), "south": (GRID, "north"),
         "west": (-1, "east"), "east": (1, "west")}
INWARD = {"north": (1, 0), "south": (-1, 0), "west": (0, 1),
          "east": (0, -1)}

# Object kinds as the C64 stores them (objects.asm uses the same).
KEY_LETTERS = "ABC"
PORTAL = "portal"               # the gate of the start: door number 4
DOOR_NUMBERS = {"A": 1, "B": 2, "C": 3, PORTAL: 4}
ZONES = ["atrio", "A", "B", "C"]        # zone number = index
KINDS = {"key": 1, "seal": 4, "treasure": 5, "potion": 6}
MAX_OBJECTS = 2                 # sprites 5 and 6
MAX_SEALS = 3
ENEMIES = {"skeleton": 1, "bat": 2}
AXES = {"h": 0, "v": 1}         # a skeleton patrols across or up-down
FAST = 2                        # flag bit: a skeleton walking every frame
MAX_ENEMIES = 3                 # sprites 2 to 4
ENEMY_DISTANCE = 3              # tiles from an opening, at least


class Room:
    def __init__(self, name, title, grid, door, objects, enemies=(),
                 zone="atrio"):
        self.name, self.title, self.grid = name, title, grid
        self.door = door                # key letter, PORTAL or None
        self.objects = objects          # (kind, letter, column, row)
        self.enemies = list(enemies)    # (kind, column, row, axis, fast)
        self.zone = zone                # one of ZONES
        self.slot = None

    def code(self, kind, letter):
        return KINDS[kind] + (KEY_LETTERS.index(letter) if letter else 0)


def load_dungeon():
    """'start:' and the GRID lines after 'grid:'. Returns the room
    file names by slot (None for an empty place) and the start slot."""
    lines = [line for line in
             (HERE / "rooms" / "dungeon.txt").read_text().splitlines()
             if line.strip() and not line.startswith("#")]
    start = next(line.split(":", 1)[1].strip() for line in lines
                 if line.startswith("start:"))
    first = lines.index("grid:") + 1
    rows = [line.split() for line in lines[first:first + GRID]]
    if len(rows) != GRID or any(len(row) != GRID for row in rows):
        raise ValueError(f"dungeon.txt: the grid must be {GRID} x {GRID}")
    slots = [None if name == "-" else name for row in rows for name in row]
    if start not in slots:
        raise ValueError(f"dungeon.txt: start room {start} not in the grid")
    return slots, slots.index(start)


def load_room(name):
    """Header lines ('name:', 'zone:', 'door:', 'object:', 'enemy:'),
    then the map."""
    lines = (HERE / "rooms" / f"{name}.txt").read_text().splitlines()
    start = lines.index("map:")
    header, grid = lines[:start], lines[start + 1:start + 1 + MAP_H]
    title, door, objects, enemies, zone = None, None, [], [], "atrio"
    for line in header:
        if line.startswith("#") or not line.strip():
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        words = value.split()
        if key == "name":
            title = value
        elif key == "zone":
            if value not in ZONES:
                raise ValueError(f"{name}: zone must be one of {ZONES}")
            zone = value
        elif key == "door":
            if value not in DOOR_NUMBERS:
                raise ValueError(f"{name}: door needs a key letter A-C "
                                 f"or '{PORTAL}'")
            door = value
        elif key == "object":
            if not words or words[0] not in KINDS:
                raise ValueError(f"{name}: unknown object '{value}'")
            letter = words[1] if words[0] == "key" else None
            if words[0] == "key" and letter not in KEY_LETTERS:
                raise ValueError(f"{name}: a key needs a letter A-C")
            column, row = (int(v) for v in words[-2:])
            objects.append((words[0], letter, column, row))
        elif key == "enemy":
            if not words or words[0] not in ENEMIES:
                raise ValueError(f"{name}: unknown enemy '{value}'")
            axis = words[3] if words[0] == "skeleton" and \
                len(words) > 3 else None
            if words[0] == "skeleton" and axis not in AXES:
                raise ValueError(f"{name}: a skeleton needs 'h' or 'v'")
            extra = words[4:] if words[0] == "skeleton" else words[3:]
            if extra not in ([], ["fast"]) or \
                    (extra and words[0] != "skeleton"):
                raise ValueError(f"{name}: only a skeleton may be 'fast'")
            enemies.append((words[0], int(words[1]), int(words[2]),
                            axis, bool(extra)))
        else:
            raise ValueError(f"{name}: unknown line '{line}'")
    if title is None:
        raise ValueError(f"{name}: 'name:' missing")
    if len(grid) != MAP_H or any(len(row) != MAP_W for row in grid):
        raise ValueError(f"{name}: the map must be {MAP_W} x {MAP_H}")
    for r, row in enumerate(grid):
        for c, symbol in enumerate(row):
            if symbol not in SYMBOLS:
                raise ValueError(f"{name}: unknown '{symbol}' at {c},{r}")
    return Room(name, title, grid, door, objects, enemies, zone)


VOID = "_"                      # screens only: black, nothing to draw
SCREEN_SYMBOLS = SYMBOLS + VOID + "O"   # O: the gate, open


def load_screen(name):
    """A title or end screen in screens/: 'name:' (the text of the
    bottom row, may be empty), 'zone:' and a map like a room's, with
    '_' for the black places where the program writes. No doors,
    objects or enemies."""
    lines = (HERE / "screens" / f"{name}.txt").read_text().splitlines()
    start = lines.index("map:")
    title, zone = None, "atrio"
    for line in lines[:start]:
        if line.startswith("#") or not line.strip():
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if key == "name":
            title = value
        elif key == "zone" and value in ZONES:
            zone = value
        else:
            raise ValueError(f"screen {name}: unknown line '{line}'")
    grid = lines[start + 1:start + 1 + MAP_H]
    if title is None:
        raise ValueError(f"screen {name}: 'name:' missing")
    if len(grid) != MAP_H or any(len(row) != MAP_W for row in grid):
        raise ValueError(f"screen {name}: the map must be {MAP_W} x "
                         f"{MAP_H}")
    for r, row in enumerate(grid):
        for c, symbol in enumerate(row):
            if symbol not in SCREEN_SYMBOLS:
                raise ValueError(f"screen {name}: unknown '{symbol}' at "
                                 f"{c},{r}")
    return Room(name, title, grid, None, [], [], zone)


def edges(r, c):
    return [side for side, hit in (
        ("north", r == 0), ("south", r == MAP_H - 1),
        ("west", c == 0), ("east", c == MAP_W - 1)) if hit]


def openings(room):
    """Positions of the openings (open or locked) on each edge."""
    found = {"north": [], "south": [], "west": [], "east": []}
    grid = room.grid
    for r in range(MAP_H):
        for c in range(MAP_W):
            symbol, edge = grid[r][c], edges(r, c)
            if symbol in OPENINGS and len(edge) != 1:
                raise ValueError(f"{room.name}: opening at {c},{r} must "
                                 "be on one edge, not inside or in a "
                                 "corner")
            if not edge:
                continue
            if symbol not in WALLS + "G" + OPENINGS:
                raise ValueError(f"{room.name}: '{symbol}' at {c},{r} "
                                 "leaves the edge open; use E or a wall")
            if symbol in OPENINGS:
                side = edge[0]
                dr, dc = INWARD[side]
                if grid[r + dr][c + dc] not in WALKABLE_INSIDE:
                    raise ValueError(f"{room.name}: the opening at {c},{r}"
                                     " needs floor behind it")
                found[side].append(c if side in ("north", "south")
                                   else r)
    return found


def check_links(slots, rooms):
    """Every opening leads to a room with the same opening facing it.
    Returns (slot, side, neighbour slot) for every way out."""
    links = []
    for slot, name in enumerate(slots):
        if name is None:
            continue
        for side, places in openings(rooms[name]).items():
            step, facing = SIDES[side]
            there = slot + step
            inside = 0 <= there < GRID * GRID and (
                side in ("north", "south") or there // GRID == slot // GRID)
            neighbour = slots[there] if inside else None
            if not places:
                continue
            if neighbour is None:
                raise ValueError(f"{name}: the {side} opening leads to "
                                 "no room")
            if openings(rooms[neighbour])[facing] != places:
                raise ValueError(f"{name}: the {side} opening does not "
                                 f"match the {facing} edge of {neighbour}")
            links.append((slot, side, there))
    return links


def door_tiles(room):
    """The tiles that change when the room's door opens, [(column,
    row), ...], and the edge the door closes. A locked door is two 'D'
    tiles: side by side on the south edge, one above the other on the
    east or west edge. The portal is the 2 x 3 gate 'G' of the north
    edge, opened by the seals."""
    if room.door == PORTAL:
        tiles = [(c, r) for r in range(MAP_H) for c in range(MAP_W)
                 if room.grid[r][c] == "G"]
        if len(tiles) != 6 or tiles[0][1] != 0:
            raise ValueError(f"{room.name}: the portal is a 2 x 3 gate "
                             "on the north edge")
        return tiles, "north"
    tiles = [(c, r) for r in range(MAP_H) for c in range(MAP_W)
             if room.grid[r][c] == "D"]
    if not tiles and not room.door:
        return [], None
    if len(tiles) != 2 or not room.door:
        raise ValueError(f"{room.name}: a door is two 'D' tiles and a "
                         "'door:' line")
    (c1, r1), (c2, r2) = tiles
    side = edges(r1, c1)[0]
    pair = (r1 == r2 and c2 == c1 + 1) if side == "south" else \
        (c1 == c2 and r2 == r1 + 1) if side in ("east", "west") else False
    if not pair:
        raise ValueError(f"{room.name}: a door is two tiles side by side "
                         "on the south edge, or one above the other on "
                         "the east or west edge")
    return tiles, side


def check_objects(slots, rooms):
    """Objects on free floor, away from openings; unique keys and
    doors; at most MAX_OBJECTS per room and MAX_SEALS seals."""
    keys, doors, seals = {}, {}, 0
    for slot, name in enumerate(slots):
        if name is None:
            continue
        room = rooms[name]
        if len(room.objects) > MAX_OBJECTS:
            raise ValueError(f"{name}: at most {MAX_OBJECTS} objects")
        places = set()
        for kind, letter, c, r in room.objects:
            if not (0 < c < MAP_W - 1 and 0 < r < MAP_H - 1) or \
                    room.grid[r][c] not in OBJECT_GROUND:
                raise ValueError(f"{name}: {kind} at {c},{r} is not on "
                                 "free floor")
            near = [room.grid[r + dr][c + dc] for dr, dc in
                    ((0, 1), (0, -1), (1, 0), (-1, 0))]
            if any(symbol in OPENINGS for symbol in near):
                raise ValueError(f"{name}: {kind} at {c},{r} lies in "
                                 "the way of an opening")
            if (c, r) in places:
                raise ValueError(f"{name}: two objects at {c},{r}")
            places.add((c, r))
            if kind == "key":
                if letter in keys:
                    raise ValueError(f"key {letter} placed twice")
                keys[letter] = slot
            seals += kind == "seal"
        if room.door:
            if room.door in doors:
                raise ValueError(f"door {room.door} placed twice")
            doors[room.door] = slot
        door_tiles(room)
    if seals > MAX_SEALS:
        raise ValueError(f"{seals} seals, at most {MAX_SEALS}")
    if PORTAL in doors and seals != MAX_SEALS:
        raise ValueError(f"the portal needs all {MAX_SEALS} seals, the "
                         f"dungeon has {seals}")
    for letter in doors:
        if letter != PORTAL and letter not in keys:
            raise ValueError(f"door {letter} has no key")
    return keys, doors


def check_enemies(slots, rooms, start):
    """Enemies on free floor, well away from the openings, at most
    MAX_ENEMIES per room, none in the start room; a skeleton needs
    floor next to it along its patrol."""
    count = 0
    for slot, name in enumerate(slots):
        if name is None:
            continue
        room = rooms[name]
        if slot == start and room.enemies:
            raise ValueError(f"{name}: the start room is safe")
        if len(room.enemies) > MAX_ENEMIES:
            raise ValueError(f"{name}: at most {MAX_ENEMIES} enemies")
        grid = room.grid
        for kind, c, r, axis, fast in room.enemies:
            if not (0 < c < MAP_W - 1 and 0 < r < MAP_H - 1) or \
                    grid[r][c] not in OBJECT_GROUND:
                raise ValueError(f"{name}: {kind} at {c},{r} is not on "
                                 "free floor")
            for rr in range(MAP_H):
                for cc in range(MAP_W):
                    if grid[rr][cc] in OPENINGS and \
                            abs(rr - r) + abs(cc - c) < ENEMY_DISTANCE:
                        raise ValueError(f"{name}: {kind} at {c},{r} is "
                                         "too near an opening")
            if kind == "skeleton":
                dr, dc = (0, 1) if axis == "h" else (1, 0)
                if grid[r + dr][c + dc] not in OBJECT_GROUND and \
                        grid[r - dr][c - dc] not in OBJECT_GROUND:
                    raise ValueError(f"{name}: the skeleton at {c},{r} "
                                     "has nowhere to walk")
            count += 1
    return count


def solve(slots, rooms, start, links):
    """Play the game on paper: explore what is open, pick up the keys
    found, open their doors, repeat. Every room and every seal must be
    reached, and no key may lie behind its own door; with all the seals
    the portal opens and the game is won."""
    blocked = {}                        # (slot, side) -> door letter
    for slot, name in enumerate(slots):
        if name and rooms[name].door and rooms[name].door != PORTAL:
            _, side = door_tiles(rooms[name])
            step, facing = SIDES[side]
            blocked[(slot, side)] = blocked[(slot + step, facing)] = \
                rooms[name].door
    held, opened, steps = set(), set(), []
    while True:
        seen, todo = {start}, [start]
        while todo:
            here = todo.pop()
            for slot, side, there in links:
                letter = blocked.get((slot, side))
                if slot == here and there not in seen and \
                        (letter is None or letter in opened):
                    seen.add(there)
                    todo.append(there)
        found = {letter for slot in seen
                 for kind, letter, c, r in rooms[slots[slot]].objects
                 if kind == "key"} - held
        for letter in sorted(found):
            steps.append(f"key {letter}")
        held |= found
        doors = {letter for letter in set(blocked.values())
                 if letter in held} - opened
        for letter in sorted(doors):
            steps.append(f"door {letter}")
        opened |= doors
        if not found and not doors:
            break
    rooms_all = {slot for slot, name in enumerate(slots) if name}
    if seen != rooms_all:
        raise ValueError(f"rooms never reached: {sorted(rooms_all - seen)}")
    seals = [slot for slot in seen
             for kind, *_ in rooms[slots[slot]].objects if kind == "seal"]
    portal = [slot for slot in seen if rooms[slots[slot]].door == PORTAL]
    if portal and len(seals) == MAX_SEALS:
        steps.append("portal")
    return {"order": steps, "rooms_reached": sorted(seen),
            "seals_reached": len(seals),
            "won": steps[-1:] == ["portal"],
            "keys_without_door": sorted(held - set(blocked.values()))}

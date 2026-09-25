"""Cryptmorrow asset builder: the data of the complete game.

Reads the dungeon (rooms/dungeon.txt and the room files, checked by
dungeon.py), chooses a metatile recipe for every map position
(autotiling), keeps each distinct tile once in a catalog, checks the C64
colour limits and writes the binary files included by the Assembly
source: one 256-byte page per room with its map, objects, door, zone,
enemies and name; the open tiles of every door and of the portal; the
colour tables of the catalog for each zone; the sprites of the
explorer, objects, enemies and sword; also the pages of the
title and end screens (screens/*.txt) and the big letters with their
colour styles (bigfont.py). Compiles the SID music, the end-of-game
pieces and the sound effects (score.py, sfx.py -> music.asm). Also
writes previews into ../build for the eye.

Run from anywhere with Python 3; no additional packages are required.
"""
import json
from pathlib import Path
import sys

import c64gfx as gfx
import bigfont
import dungeon as D
from dungeon import GROUND, GRID, MAP_H, MAP_W, WALLS
import font
import music
import sprites
import tiles as T

HERE = Path(__file__).resolve().parent
OUT = HERE / "generated"
BUILD = HERE.parent / "build"
ROOM_PAGE = 256                 # bytes per room at ROOM_DATA
OBJECTS_AT = 200                # page offsets, as in memory.asm
DOOR_AT = 208                   # door number: 1-3 keys A-C, 4 portal
ZONE_AT = 209                   # 0 atrio, 1-3 zones A-C
ENEMIES_AT = 216
NAME_AT = 228
DOOR_LIST = 32                  # bytes per door in doors.bin
LIST_END = 0xFF
SCREENS = ["title", "game_over", "victory"]     # pages at $9d00-$9fff

FIRST_CELL_ROW = 3              # the playfield starts on cell row 3
MAX_TILES = 128                 # ids 0..127 (bit 7 selects the half)
MAX_TORCHES = 6                 # size of the torch list in room.asm
NAME_ROW = 24
NAME_COLOUR = gfx.GREY
OBJECT_COLOURS = {1: gfx.YELLOW, 2: gfx.YELLOW, 3: gfx.YELLOW,
                  4: gfx.LIGHT_GREEN, 5: gfx.YELLOW, 6: gfx.WHITE}
OBJECT_FRAME = {1: 0, 2: 0, 3: 0, 4: 1, 5: 2, 6: 3}


def at(grid, r, c):
    """Map symbol; everything outside the room counts as wall."""
    if 0 <= r < MAP_H and 0 <= c < MAP_W:
        return grid[r][c]
    return "#"


def choose_tile(grid, r, c):
    """Autotiling: pick the recipe from the symbol and its neighbours."""
    symbol = grid[r][c]
    if symbol == D.VOID:            # title and end screens only
        return T.void()
    pick = r * 7 + c * 13           # stable variant choice, no randomness
    north = at(grid, r - 1, c) in GROUND
    south = at(grid, r + 1, c) in GROUND
    east = at(grid, r, c + 1) in GROUND
    west = at(grid, r, c - 1) in GROUND
    rimmed = north or east or west
    if symbol == "#":
        if south:
            count = T.FACE_PLAIN if rimmed else T.FACE_ALL
            tile = T.wall_face(pick % count)
        else:
            count = T.MASS_PLAIN if rimmed else T.MASS_ALL
            tile = T.wall_mass(pick % count)
        return T.add_rims(tile, north, east, west) if rimmed else tile
    if symbol in "rn":
        if not south:
            raise ValueError(f"'{symbol}' at {c},{r} needs floor below")
        tile = T.wall_face(pick % T.FACE_PLAIN)
        if rimmed:
            tile = T.add_rims(tile, north, east, west)
        if symbol == "n":
            return T.niche(tile)
        return T.roots(tile, flip=pick % 2 == 1)
    if symbol in "Tt":
        if not south:
            raise ValueError(f"torch at {c},{r} needs floor below it")
        tile = T.torch(right=symbol == "t")
        if not rimmed:
            return tile
        rim = T.add_rims(tile, north, east, west)
        x0 = 4 if symbol == "t" else 0      # the flame cell keeps no rim
        for y in range(8):
            rim.pixels[y][x0:x0 + 4] = tile.pixels[y][x0:x0 + 4]
        return rim
    under_wall = at(grid, r - 1, c) in WALLS
    if symbol == ".":
        variant = pick % T.FLOOR_VARIANTS
        return T.floor_shadow(variant) if under_wall else T.floor(variant)
    if symbol == "m":
        if under_wall:
            raise ValueError(f"moss at {c},{r}: not supported under walls")
        return T.floor_moss(pick % 2)
    if symbol == "b":
        return T.floor_bones(pick % 2, shadow=under_wall)
    if symbol == "D":
        if r == MAP_H - 1:
            right = at(grid, r, c - 1) == "D"
            return T.door_grate([T.exit_stairs(False),
                                 T.exit_stairs(True)])[right]
        lower = at(grid, r - 1, c) == "D"       # second of the pair
        top = r - 1 if lower else r
        opened = [row.replace("D", "E") for row in grid]
        pair = [choose_tile(opened, top, c), choose_tile(opened, top + 1, c)]
        return T.door_side(pair, east=c == MAP_W - 1)[lower]
    if symbol == "g":
        return T.floor_gold(pick % 2, shadow=under_wall)
    if symbol == "w":
        edge = at(grid, r - 1, c) != "w"
        return T.water(pick % 2, edge)
    if symbol == "u":
        base = T.floor_shadow(4) if under_wall else T.floor(4)
        return T.urn(base)
    if symbol == "W":
        column = 0 if at(grid, r, c - 1) != "W" else 1
        row = 0 if at(grid, r - 1, c) != "W" else 1
        return T.well(column, row, [T.floor(v) for v in (2, 5, 3, 6)])
    if symbol == "A":
        column = 0
        while at(grid, r, c - column - 1) == "A":
            column += 1
        if column > 2:
            raise ValueError(f"altar at {c},{r}: three tiles at most")
        base = T.floor_shadow(3) if under_wall else T.floor(3)
        return T.altar(column, base)
    if symbol == "E":                   # the side comes from the edge
        if r == MAP_H - 1:
            return T.exit_stairs(right=at(grid, r, c - 1) == "E")
        if r == 0:
            return T.passage("north", pick % T.FLOOR_VARIANTS)
        side = "west" if c == 0 else "east"
        return T.passage(side, pick % T.FLOOR_VARIANTS, under_wall)
    if symbol == "P":
        top = at(grid, r - 1, c) != "P"
        return T.pillar(0 if top else 1, T.floor(pick % T.FLOOR_VARIANTS))
    if symbol in "GO":                  # O: the gate, opened
        column = 0 if at(grid, r, c - 1) != symbol else 1
        row = 0
        while at(grid, r - row - 1, c) == symbol:
            row += 1
        walls = [T.wall_mass(1), T.wall_mass(2)] if row == 0 else \
                [T.wall_face(0), T.wall_face(2)]
        return T.gate(column, row, walls, T.floor_shadow(3 + column),
                      opened=symbol == "O")
    raise AssertionError(symbol)


def cells(tile):
    """The four 4 x 8 cells of a metatile: TL, TR, BL, BR."""
    p = tile.pixels
    return [[row[x:x + 4] for row in p[y:y + 8]]
            for y in (0, 8) for x in (0, 4)]


def encode_tile(tile):
    flame = {T.TYPE_TORCH_LEFT: 0, T.TYPE_TORCH_RIGHT: 1}.get(tile.kind)
    encoded = []
    for index, pixels in enumerate(cells(tile)):
        forced = T.FLAME_PALETTE if index == flame else None
        try:
            encoded.append(gfx.encode_cell(pixels, forced))
        except ValueError as error:
            names = ["TL", "TR", "BL", "BR"]
            raise ValueError(f"{tile.name} {names[index]}: {error}")
    return encoded


def add(catalog, index, tile):
    """Catalog id of a tile, adding it the first time it is seen."""
    key = tile.key()
    if key not in index:
        index[key] = len(catalog)
        catalog.append(tile)
    return index[key]


def room_header(room, first_id):
    """Page bytes 200-215: two objects (kind, column, row, number),
    the door number (0 none, 1-3 keys A-C, 4 the portal) and the
    zone number."""
    header = bytearray(16)
    for n, (kind, letter, c, r) in enumerate(room.objects):
        header[n * 4:n * 4 + 4] = bytes([room.code(kind, letter), c, r,
                                         first_id + n])
    if room.door:
        header[DOOR_AT - OBJECTS_AT] = D.DOOR_NUMBERS[room.door]
    header[ZONE_AT - OBJECTS_AT] = D.ZONES.index(room.zone)
    return header


def door_list(room, catalog, index):
    """The tiles show_door draws once the room's door is open: column,
    row and metatile of each, ending with LIST_END. A locked door
    opens into its opening (D becomes E); the portal's gate G into the
    open gate O."""
    tiles, _ = D.door_tiles(room)
    opened = [row.replace("D", "E").replace("G", "O") for row in room.grid]
    data = bytearray()
    for c, r in tiles:
        data += bytes([c, r, add(catalog, index, choose_tile(opened, r, c))])
    data.append(LIST_END)
    if len(data) > DOOR_LIST:
        raise ValueError(f"{room.name}: door list too long")
    return data


def build():
    slots, start = D.load_dungeon()
    rooms_by_name = {name: D.load_room(name) for name in filter(None, slots)}
    links = D.check_links(slots, rooms_by_name)
    keys, doors = D.check_objects(slots, rooms_by_name)
    enemy_count = D.check_enemies(slots, rooms_by_name, start)
    solution = D.solve(slots, rooms_by_name, start, links)
    catalog, index, rooms = [], {}, []
    object_count, lists, doors_bin = 0, {}, bytearray()
    for slot, name in enumerate(slots):
        if name is None:
            continue
        room = rooms_by_name[name]
        room.slot = slot
        grid = room.grid
        ids = [add(catalog, index, choose_tile(grid, r, c))
               for r in range(MAP_H) for c in range(MAP_W)]
        torches = sum(row.count("T") + row.count("t") for row in grid)
        if torches > MAX_TORCHES:
            raise ValueError(f"{name}: {torches} torches, max {MAX_TORCHES}")
        header = room_header(room, object_count)
        if room.door:
            number = D.DOOR_NUMBERS[room.door]
            lists[number] = door_list(room, catalog, index)
        object_count += len(room.objects)
        rooms.append((slot, room, ids, header))
    screens = []
    for name in SCREENS:
        room = D.load_screen(name)
        ids = [add(catalog, index, choose_tile(room.grid, r, c))
               for r in range(MAP_H) for c in range(MAP_W)]
        torches = sum(row.count("T") + row.count("t") for row in room.grid)
        if torches > MAX_TORCHES:
            raise ValueError(f"screen {name}: {torches} torches")
        screens.append((room, ids))
    if len(catalog) > MAX_TILES:
        raise ValueError(f"{len(catalog)} tiles, the limit is {MAX_TILES}")

    bitmap = bytearray()
    tables = {name: bytearray(256) for name in
              ("screen_left", "screen_right", "color_left", "color_right")}
    attr = bytearray(MAX_TILES)
    for number, tile in enumerate(catalog):
        encoded = encode_tile(tile)
        for data, _, _ in encoded:
            bitmap += data
        for cell, (_, screen, color) in enumerate(encoded):
            side = "left" if cell % 2 == 0 else "right"
            slot = number + (128 if cell >= 2 else 0)
            tables["screen_" + side][slot] = screen
            tables["color_" + side][slot] = color
        attr[number] = tile.attr

    OUT.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    outputs = {"tiles.bitmap": bitmap, "tiles.attr": attr,
               "font.bin": font.font_bytes(),
               "hero.sprites": b"".join(sprites.encode_sprite(frame)
                                        for frame in sprites.HERO_FRAMES),
               "flames.bin": sprites.encode_flames()}
    zones = bytearray()
    for zone in D.ZONES:
        palette = T.ZONE_PALETTES[zone]
        for name in ("screen_left", "screen_right", "color_left",
                     "color_right"):
            zones += bytes(T.recoloured(value, palette)
                           for value in tables[name])
    outputs["zones.color"] = zones
    doors_bin = bytearray([LIST_END] * (4 * DOOR_LIST))
    for number, data in lists.items():
        offset = (number - 1) * DOOR_LIST
        doors_bin[offset:offset + len(data)] = data
    outputs["doors.bin"] = doors_bin
    pages = bytearray(GRID * GRID * ROOM_PAGE)
    for slot, room, ids, header in rooms:
        column = (40 - len(room.title)) // 2
        name = font.encode_text(room.title, column, NAME_ROW, NAME_COLOUR)
        if NAME_AT + len(name) > ROOM_PAGE:
            raise ValueError(f"{room.name}: name too long")
        base = slot * ROOM_PAGE
        pages[base:base + len(ids)] = bytes(ids)
        pages[base + OBJECTS_AT:base + OBJECTS_AT + 16] = header
        for n, (kind, c, r, axis, fast) in enumerate(room.enemies):
            at = base + ENEMIES_AT + n * 4
            flags = D.AXES.get(axis, 0) | (D.FAST if fast else 0)
            pages[at:at + 4] = bytes([D.ENEMIES[kind], c, r, flags])
        pages[base + NAME_AT:base + NAME_AT + len(name)] = name
    outputs["rooms.bin"] = pages
    pages = bytearray()
    for room, ids in screens:
        page = bytearray(ROOM_PAGE)
        page[:len(ids)] = bytes(ids)
        page[ZONE_AT] = D.ZONES.index(room.zone)
        column = (40 - len(room.title)) // 2
        name = font.encode_text(room.title, column, NAME_ROW, NAME_COLOUR)
        page[NAME_AT:NAME_AT + len(name)] = name
        pages += page
    outputs["screens.bin"] = pages
    outputs["big.font"] = bigfont.font_bytes()
    outputs["big.styles"] = bigfont.style_bytes()
    if object_count > 32:
        raise ValueError(f"{object_count} objects, the limit is 32")
    outputs["dungeon.asm"] = (
        "; Generated by game/assets/build_assets.py from\n"
        "; rooms/dungeon.txt: do not edit.\n"
        f"START_ROOM = {start:<11}; {slots[start]}\n"
        f"OBJECT_COUNT = {object_count:<9}; all rooms\n").encode()
    outputs["objects.sprites"] = b"".join(
        sprites.encode_sprite(frame) for frame in sprites.OBJECT_FRAMES)
    outputs["combat.sprites"] = b"".join(
        [sprites.encode_sprite(frame) for frame in sprites.ENEMY_FRAMES] +
        [sprites.encode_hires(frame) for frame in sprites.BLADE_FRAMES])
    for name, data in outputs.items():
        (OUT / name).write_bytes(data)
    for stale in ["room.bitmap", "room.screen", "room.color",
                  "room.solid", "tiles.screen_left", "tiles.screen_right",
                  "tiles.color_left", "tiles.color_right"] + \
            [p.name for p in OUT.glob("room_*.bin")]:
        if (OUT / stale).exists():
            (OUT / stale).unlink()

    summary = {
        "version": "1.0.1",
        "stage": "The complete game",
        "metatile": "2 x 2 cells, 8 x 16 logical pixels, 40 bytes",
        "tiles": len(catalog), "tile_limit": MAX_TILES,
        "catalog": [{"id": n, "name": t.name, "attr": t.attr}
                    for n, t in enumerate(catalog)],
        "grid": f"{GRID} x {GRID}", "start_room": start,
        "rooms": [{"slot": slot, "file": f"rooms/{room.name}.txt",
                   "name": room.title, "distinct_tiles": len(set(ids)),
                   "torches": sum(row.count("T") + row.count("t")
                                  for row in room.grid),
                   "exits": {side: there for s0, side, there in links
                             if s0 == slot},
                   "zone": room.zone,
                   "door": room.door,
                   "objects": [" ".join(filter(None, (kind, letter)))
                               + f" at {c},{r}" for kind, letter, c, r
                               in room.objects],
                   "enemies": [f"{kind} at {c},{r}" + (f" {axis}" if axis
                                                       else "")
                               + " fast" * fast
                               for kind, c, r, axis, fast in room.enemies]}
                  for slot, room, ids, header in rooms],
        "screens": [{"file": f"screens/{room.name}.txt",
                     "zone": room.zone, "bottom_row": room.title,
                     "distinct_tiles": len(set(ids))}
                    for room, ids in screens],
        "big_letters": {"alphabet": bigfont.ALPHABET,
                        "bytes": len(outputs["big.font"]),
                        "styles": bigfont.STYLE_ORDER},
        "objects": object_count,
        "enemies": enemy_count,
        "solution": solution,
        "glyphs": font.GLYPH_ORDER,
        "hero_frames": len(sprites.HERO_FRAMES),
    }
    summary["music"] = music.build(OUT)
    (OUT / "assets.json").write_text(json.dumps(summary, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
    write_previews(catalog, rooms, lists)
    write_screen_previews(catalog, screens)
    print(f"Assets checked: {len(catalog)} metatiles "
          f"(limit {MAX_TILES}), {len(rooms)} room(s), "
          f"{len(screens)} screens, "
          f"{len(links)} exits, {object_count} objects, "
          f"{enemy_count} enemies, "
          f"{len(doors)} door(s), "
          f"{len(font.GLYPH_ORDER)} glyphs, 8 hero frames, 4 flames, "
          f"music {summary['music']['song_steps']} steps "
          f"({summary['music']['loop_seconds']} s).")


def write_previews(catalog, rooms, lists):
    """PNG previews for the author; the C64 never sees these files.
    Rooms are shown in their zone's colours with the doors closed; the
    tile sheet shows every metatile, open doors and portal included."""
    columns = 16
    rows = (len(catalog) + columns - 1) // columns
    sheet = [[gfx.DARK_GREY] * (columns * 9 + 1) for _ in range(rows * 17 + 1)]
    for number, tile in enumerate(catalog):
        x0, y0 = 1 + (number % columns) * 9, 1 + (number // columns) * 17
        for y in range(T.H):
            sheet[y0 + y][x0:x0 + T.W] = tile.pixels[y]
    gfx.write_png(BUILD / "tiles-preview.png", sheet, scale=3)
    # the rooms in their places of the grid, playfield and name only
    used = [slot for slot, *_ in rooms]
    top, bottom = min(used) // GRID, max(used) // GRID
    left = min(slot % GRID for slot in used)
    right = max(slot % GRID for slot in used)
    gap = 6
    image = [[gfx.DARK_GREY] * ((right - left + 1) * (160 + gap) + gap)
             for _ in range((bottom - top + 1) * (184 + gap) + gap)]
    for slot, room, ids, header in rooms:
        title = room.title
        x0 = gap + (slot % GRID - left) * (160 + gap)
        y0 = gap + (slot // GRID - top) * (184 + gap)
        for y in range(184):
            image[y0 + y][x0:x0 + 160] = [gfx.BLACK] * 160
        palette = T.ZONE_PALETTES[room.zone]
        for r in range(MAP_H):
            for c in range(MAP_W):
                tile = catalog[ids[r * MAP_W + c]]
                for y in range(T.H):
                    image[y0 + r * 16 + y][x0 + c * 8:x0 + c * 8 + 8] = \
                        [palette.get(p, p) for p in tile.pixels[y]]
        for text, column, row, colour in (
                ("~" * 36, 2, 20, gfx.GREEN),
                (title, (40 - len(title)) // 2, 22, NAME_COLOUR)):
            for offset, char in enumerate(text):
                pixels = gfx.decode_cell(font.glyph_bytes(char),
                                         colour << 4, 0)
                for y in range(8):
                    x = x0 + (column + offset) * 4
                    image[y0 + row * 8 + y][x:x + 4] = pixels[y]
        for kind, letter, c, r in room.objects:
            code = room.code(kind, letter)
            frame = sprites.OBJECT_FRAMES[OBJECT_FRAME[code]]
            colours = {"B": gfx.BROWN, "G": OBJECT_COLOURS[code],
                       "S": gfx.PINK}
            for y, line in enumerate(frame):
                for x, char in enumerate(line):
                    if char != ".":
                        image[y0 + r * 16 - 2 + y][x0 + c * 8 - 2 + x] = \
                            colours[char]
        for kind, c, r, axis, fast in room.enemies:
            frame = sprites.SKELETON[0] if kind == "skeleton" else \
                sprites.BAT[0]
            colours = {"B": gfx.BROWN, "S": gfx.PINK,
                       "G": gfx.LIGHT_GREY if kind == "skeleton"
                       else gfx.PURPLE}
            for y, line in enumerate(frame):
                for x, char in enumerate(line):
                    if char != ".":
                        image[y0 + r * 16 - 4 + y][x0 + c * 8 - 2 + x] = \
                            colours[char]
    gfx.write_png(BUILD / "dungeon-preview.png", image, scale=2)
    stale = BUILD / "room-preview.png"
    if stale.exists():
        stale.unlink()


BIG_WORDS = {"title": ("CRYPTMORROW", 4, "logo"),
             "game_over": ("GAME OVER", 7, "lost"),
             "victory": ("VICTORY", 10, "won")}


def write_screen_previews(catalog, screens):
    """The three screens side by side as the asset files make them:
    map, big word and bottom row; the menu, the score and the sprites
    are the program's and appear only in the VICE captures."""
    gap = 6
    image = [[gfx.DARK_GREY] * (3 * (160 + gap) + gap)
             for _ in range(200 + 2 * gap)]
    for n, (room, ids) in enumerate(screens):
        x0, y0 = gap + n * (160 + gap), gap
        canvas = gfx.blank(160, 200)
        palette = T.ZONE_PALETTES[room.zone]
        for r in range(MAP_H):
            for c in range(MAP_W):
                tile = catalog[ids[r * MAP_W + c]]
                for y in range(T.H):
                    canvas[24 + r * 16 + y][c * 8:c * 8 + 8] = \
                        [palette.get(p, p) for p in tile.pixels[y]]
        word, column, style = BIG_WORDS[room.name]
        bigfont.draw(canvas, word, column, 1, style)
        text = room.title
        for offset, char in enumerate(text):
            pixels = gfx.decode_cell(font.glyph_bytes(char),
                                     NAME_COLOUR << 4, 0)
            x = ((40 - len(text)) // 2 + offset) * 4
            for y in range(8):
                canvas[NAME_ROW * 8 + y][x:x + 4] = pixels[y]
        for y in range(200):
            image[y0 + y][x0:x0 + 160] = canvas[y]
    gfx.write_png(BUILD / "screens-preview.png", image, scale=2)


if __name__ == "__main__":
    try:
        build()
    except ValueError as error:
        print(f"Asset check FAILED: {error}", file=sys.stderr)
        sys.exit(1)

"""Original pixel recipes for Cryptmorrow's metatiles.

A metatile is 2 x 2 cells: 8 x 16 logical pixels, 16 x 16 on screen.
Every recipe returns a Tile. The builder chooses the recipe for each
map position (autotiling), removes duplicates and encodes the result.

Cell order used by the solid bits: TL = bit 0, TR = bit 1, BL = bit 2,
BR = bit 3. Bits 4-6 hold the tile type read by the C64 renderer.
"""
from c64gfx import (BLACK, BLUE, BROWN, CYAN, DARK_GREY, GREEN, GREY,
                    LIGHT_BLUE, LIGHT_GREEN, LIGHT_GREY, ORANGE, PINK, RED,
                    WHITE, YELLOW, blank, paint)
from sprites import FLAMES

W, H = 8, 16

TYPE_NORMAL = 0
TYPE_TORCH_LEFT = 1     # animated flame in the top-left cell
TYPE_TORCH_RIGHT = 2    # animated flame in the top-right cell
TYPE_EXIT = 3           # opening towards the next room
TYPE_DOOR = 4           # gate or locked door: solid value 2

SOLID_NONE = 0b0000
SOLID_TOP = 0b0011
SOLID_ALL = 0b1111

FLAME_PALETTE = [RED, ORANGE, YELLOW]   # codes 01, 10, 11 of FLAMES


class Tile:
    def __init__(self, name, pixels, solid=SOLID_NONE, kind=TYPE_NORMAL):
        assert len(pixels) == H and all(len(r) == W for r in pixels)
        self.name = name
        self.pixels = pixels
        self.solid = solid
        self.kind = kind

    @property
    def attr(self):
        return self.solid | (self.kind << 4)

    def key(self):
        return (tuple(map(tuple, self.pixels)), self.attr)


def mirrored(pixels):
    return [row[::-1] for row in pixels]


def recolour(pixels, mapping, x0=0, x1=W, y0=0, y1=H):
    for y in range(y0, y1):
        for x in range(x0, x1):
            pixels[y][x] = mapping.get(pixels[y][x], pixels[y][x])


# --- Masonry -------------------------------------------------------------

def bricks(variant, body, light, shade=None):
    """Two brick courses with offset joints and black mortar."""
    t = blank(W, H)
    joint = 2 + variant % 4
    for y in range(1, 15):
        for x in range(W):
            seam = y == 7 or x == (joint if y < 8 else (joint + 4) % 8)
            if not seam:
                t[y][x] = body
    for x in range(W):
        if x != joint and x != variant % 8:
            t[1][x] = light
        if x != (joint + 4) % 8 and (x + variant) % 5:
            t[8][x] = light
        if shade is not None:
            if x != joint:
                t[6][x] = shade
            if x != (joint + 4) % 8:
                t[14][x] = shade
    # small pits keep large walls from looking printed
    t[4][(variant * 3) % 8] = BLACK
    t[12][(variant + 2) % 8] = BLACK
    return t


MOSS_CLUMPS = [
    [(0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (0, 3), (1, 4), (0, 5),
     (5, 8), (6, 8), (6, 9), (7, 9), (6, 10)],
    [(4, 1), (5, 1), (6, 1), (7, 1), (5, 2), (6, 2), (7, 2), (6, 3),
     (7, 4), (7, 5)],
    [(0, 8), (1, 8), (2, 8), (1, 9), (2, 9), (3, 9), (2, 10), (2, 11),
     (5, 1), (6, 1), (6, 2)],
    [(2, 1), (3, 1), (4, 1), (3, 2), (4, 2), (3, 3), (5, 8), (6, 8),
     (7, 8), (6, 9), (7, 9), (7, 10), (0, 12), (1, 12), (0, 13)],
]


def wall_mass(variant):
    """Thick wall seen beyond the lit faces: darker bricks, moss."""
    t = bricks(variant, DARK_GREY, GREY)
    if variant >= MASS_PLAIN:
        for x, y in MOSS_CLUMPS[variant - MASS_PLAIN]:
            t[y][x] = GREEN
    return Tile(f"wall.mass.{variant}", t, SOLID_ALL)


MASS_PLAIN = 3          # variants 0-2 have no moss (rims may be added)
MASS_ALL = 7            # variants 3-6 carry a moss clump


def wall_face(variant):
    """North-facing wall lit by the torches: lighter three-tone bricks.

    Variant 3 is overgrown: its mossy cells swap the three greys for
    green tones, so every cell still uses at most three colours.
    """
    t = bricks(variant, GREY, LIGHT_GREY, DARK_GREY)
    t[15] = [DARK_GREY] * W           # footing, above the floor shadow
    if variant == 3:
        moss = {LIGHT_GREY: LIGHT_GREEN, DARK_GREY: GREEN}
        recolour(t, moss, 0, 4, 0, 8)
        recolour(t, moss, 4, 8, 8, 16)
        for x, y in [(1, 7), (2, 7), (2, 8), (5, 7), (6, 6)]:
            if x < 4 and y < 8 or x >= 4 and y >= 8:
                t[y][x] = GREEN
    if variant == 4:
        moss = {LIGHT_GREY: GREEN}
        recolour(t, moss, 4, 8, 0, 8)
        recolour(t, moss, 0, 4, 8, 16)
        for x, y in [(5, 2), (6, 2), (6, 3), (1, 9), (1, 10), (2, 11)]:
            t[y][x] = GREEN
    return Tile(f"wall.face.{variant}", t, SOLID_ALL)


FACE_PLAIN = 3
FACE_ALL = 5


def add_rims(tile, north, east, west):
    """Light edge where the wall meets the floor on that side."""
    t = [row[:] for row in tile.pixels]
    if north:
        t[0] = [LIGHT_GREY] * W
    for flag, x in ((east, W - 1), (west, 0)):
        if flag:
            for y in range(H):
                t[y][x] = GREY if y in (0, 7, 15) else LIGHT_GREY
    sides = "n" * north + "e" * east + "w" * west
    return Tile(f"{tile.name}.rim-{sides}", t, tile.solid, tile.kind)


ROOTS = [
    "OBOOBOOB", ".OBOB.OB", ".OB.OB.O", "O.B.OB.O", "OB..O.B.",
    ".O..OB..", ".OB..O..", "..O..OB.", "..OB..O.", "...O..O.",
    "...OB.B.", "....O...", "....B...",
]


def roots(tile, flip=False):
    """Roots breaking through a lit face. Earth stains the bricks:
    light grey turns grey and the dark grey shading turns brown, so
    with the orange roots every cell keeps three colours."""
    t = [row[:] for row in tile.pixels]
    recolour(t, {LIGHT_GREY: GREY, DARK_GREY: BROWN})
    pattern = [line[::-1] for line in ROOTS] if flip else ROOTS
    paint(t, 0, 0, pattern, {"O": ORANGE, "B": BROWN})
    return Tile(f"{tile.name}.roots{'.flip' * flip}", t, tile.solid,
                tile.kind)


NICHE = [
    "........", "..kkkk..", ".kkkkkk.", ".kkkkkk.", ".kkkkkk.",
    ".kkkkkk.", ".kWWWWk.", ".WWWWWW.", ".WkWWkW.", ".WWWWWW.",
    ".kWkkWk.", ".kWWWWk.", ".LLLLLL.", "........",
]


def niche(tile):
    """A burial niche cut into a lit face, a skull inside. The dark
    grey shading turns grey so the white skull fits every cell."""
    t = [row[:] for row in tile.pixels]
    recolour(t, {DARK_GREY: GREY})
    paint(t, 0, 1, NICHE, {"k": BLACK, "W": WHITE, "L": LIGHT_GREY})
    return Tile(f"{tile.name}.niche", t, tile.solid, tile.kind)


def torch(right=False):
    """Face bricks with a dark niche: flame above, iron bracket below."""
    base = wall_face(1).pixels
    t = [row[:] for row in base]
    for y in range(H):
        for x in range(4):
            t[y][x] = BLACK
    bracket = [".BB.", ".OB.", ".OB.", ".OB.", ".BB.", "BBBB", ".BB.",
               "GGGG"]
    paint(t, 0, 8, bracket, {"B": BROWN, "O": ORANGE, "G": GREY})
    if right:
        t = mirrored(t)
    flame_x = 4 if right else 0
    paint(t, flame_x, 0, FLAMES[0], {"R": RED, "O": ORANGE, "Y": YELLOW})
    kind = TYPE_TORCH_RIGHT if right else TYPE_TORCH_LEFT
    side = "right" if right else "left"
    return Tile(f"wall.torch.{side}", t, SOLID_ALL, kind)


# --- Floor ---------------------------------------------------------------

def slab(variant):
    """Cobblestone floor of the first room: one rounded stone
    per tile, seven shapes, dark gaps; a small lit upper-left edge."""
    t = blank(W, H)
    top = 1 + variant % 3
    bottom = 10 + variant % 4
    left = 1 if variant % 2 else 0
    for y in range(top, bottom):
        for x in range(left, 7):
            corner = (y == top and x in (left, 6)) or \
                     (y == bottom - 1 and x == 6)
            if not corner:
                t[y][x] = DARK_GREY
    t[top][left + 1] = GREY
    t[top][left + 2] = GREY
    if variant in (1, 4):
        for x, y in [(4, top + 1), (4, top + 2), (3, top + 3),
                     (3, top + 4), (2, top + 5)]:
            t[y][x] = BLACK
    return t


FLOOR_VARIANTS = 7


def floor(variant):
    return Tile(f"floor.{variant}", slab(variant))


def void():
    """Nothing: the black places of the title and end screens, where
    the program prints its words."""
    return Tile("void", blank(W, H))


def floor_shadow(variant):
    """Floor under a north wall: the wall's shadow darkens the top."""
    t = slab(variant)
    for y in range(0, 3):
        t[y] = [BLACK] * W
    for x in range(W):
        if x % 2 == 0:
            t[3][x] = BLACK
    recolour(t, {GREY: DARK_GREY}, 0, W, 0, 6)
    return Tile(f"floor.shadow.{variant}", t)


def floor_moss(variant):
    """Moss tufts growing between the slabs."""
    t = slab(variant)
    tufts = [["..g.", ".gG.", "g.Gg", ".Gg.", "..g."],
             [".g..", "gGg.", ".Gg.", "..g."]]
    x, y = (0, 9) if variant % 2 == 0 else (4, 2)
    cell = (x, x + 4, y // 8 * 8, y // 8 * 8 + 8)
    recolour(t, {GREY: DARK_GREY}, *cell)
    paint(t, x, y, tufts[variant % 2], {"g": GREEN, "G": LIGHT_GREEN})
    return Tile(f"floor.moss.{variant}", t)


BONES = [
    [".WWW.", "WkWkW", "WWWWW", ".W.W."],                   # skull
    ["W....W", ".W..W.", "..WW..", "..WW..", ".W..W.", "W....W"],
]


def floor_bones(variant, shadow=False):
    """Bones on the cobblestones: a skull or two long bones."""
    stone = variant * 3 + 1
    t = floor_shadow(stone).pixels if shadow else slab(stone)
    x, y = (2, 6) if variant == 0 else (1, 6)
    paint(t, x, y, BONES[variant], {"W": WHITE, "k": BLACK})
    return Tile(f"floor.bones.{variant}" + ".shadow" * shadow, t)


def passage(side, variant, shadow=False):
    """Opening on the north, west or east edge: the floor runs on to
    the edge of the playfield and loses its highlights near it. The
    light rims of the walls beside it mark the gap."""
    t = floor_shadow(variant).pixels if shadow else slab(variant)
    for y in range(H):
        for x in range(W):
            depth = {"north": y, "west": x, "east": W - 1 - x}[side]
            if depth < 3 and t[y][x] == GREY:
                t[y][x] = DARK_GREY
    name = f"floor.exit.{side}.{variant}" + ".shadow" * shadow
    return Tile(name, t, SOLID_NONE, TYPE_EXIT)


def exit_stairs(right=False):
    """Steps going down to the south: each step darker than the last."""
    t = blank(W, H)
    t[1] = [GREY] * W
    for y in (2, 3):
        t[y] = [DARK_GREY] * W
    t[5] = [DARK_GREY] * W
    t[6] = [DARK_GREY if x % 2 else BLACK for x in range(W)]
    t[9] = [DARK_GREY if x % 2 == 0 else BLACK for x in range(W)]
    t[12] = [DARK_GREY if x % 4 == 1 else BLACK for x in range(W)]
    if right:
        t = mirrored(t)
    side = "right" if right else "left"
    return Tile(f"floor.exit.{side}", t, SOLID_NONE, TYPE_EXIT)


# --- Large pieces ----------------------------------------------------------

GATE = [
    "......GGGG......", "....GGggggGG....", "...GGg....gGG...",
    "..GGg......gGG..", "..Gg........gG..", ".GG....BB....GG.",
    ".Gg...BBBB...gG.", ".Gg..BBBBBB..gG.", "GG..BOBBOBOB..GG",
    "Gg..BOBBOBOB..gG", "Gg..BOBBOBOB..gG", "Gg..BOBBOBOB..gG",
    "GG..BOBBOBOB..GG", "Gg..BOBBOBOB..gG", "Gg..BOBBOBOB..gG",
    "Gg..BOBBOBOB..gG", "GG..BBBBBBBB..GG", "Gg..BOBBOBOB..gG",
    "Gg..BOBBOBOB..gG", "Gg..BOBBOBOB..gG", "GG..BOBBOBOB..GG",
    "Gg..BOBB..OB..gG", "Gg..BOBB..OB..gG", "Gg..BOBBOBOB..gG",
    "GG..BOBBOBOB..GG", "Gg..BOBBOBOB..gG", "Gg..BOBBOBOB..gG",
    "Gg..BOBBOBOB..gG", "GG..BBBBBBBB..GG", "Gg..BOBBOBOB..gG",
    "Gg..BOBBOBOB..gG", "Gg..BOBBOBOB..gG", "GG..BOBBOBOB..GG",
    "Gg..BOBBOBOB..gG", "Gg..BOBBOBOB..gG", "GGGGGGGGGGGGGGGG",
    "BBBBBBBBBBBBBBBB", "................", "..GGGGGGGGGGGG..",
    "................", "...gggggggggg...", "..gGGgggggGGgg..",
    "..gggggggggggg..", "....gggggggg....", "................",
    "m.............m.", "mm...........mm.", "................",
]
GATE_COLOURS = {"G": GREY, "g": DARK_GREY, "B": BROWN, "O": ORANGE,
                "m": GREEN, "Y": YELLOW, "W": WHITE, "S": CYAN,
                "H": LIGHT_GREEN, "F": GREEN}


def open_arch(gate_rows):
    """The gate without its door: between the sides of the arch, rows
    1-34, the world outside at dawn - sky and rising sun, hills, fields
    and a light road. Colour bands follow the 8-row cells, so that the
    cells with the sides of the arch keep one colour of their own."""
    def outside(x, gy):
        dx = x - 7.5
        sun = (dx * 2) ** 2 + ((gy - 10) * 1.0) ** 2   # screen pixels
        if gy < 16:
            if sun < 7:
                return "W"                      # the rising sun
            if sun < 26:
                return "Y"
            return "S"                          # sky
        if gy < 24:
            hill = 17 + abs(dx) * 0.9           # a valley between hills
            return "S" if gy < hill and 4 <= x <= 11 else "H"
        road = 7.5 + (gy - 24) * 0.35
        if gy < 32 and 4 <= x <= 11 and abs(x - road) < 1 + (gy - 24) / 8:
            return "Y"
        return "F"                              # fields
    rows = []
    for gy, line in enumerate(gate_rows):
        if not 1 <= gy <= 34:
            rows.append(line)
            continue
        chars = list(line)
        inside = [x for x in range(len(chars))
                  if chars[x] in ".BO" and
                  any(c in "Gg" for c in chars[:x]) and
                  any(c in "Gg" for c in chars[x + 1:])]
        for x in inside:
            chars[x] = outside(x, gy)
        rows.append("".join(chars))
    return rows


GATE_OPEN = open_arch(GATE)
GATE_ARCH_ROWS = 35     # rows above this belong to the wall
GATE_FLOOR_ROWS = 40    # from here the approach lies on the floor


def gate(column, row, wall_tiles, floor_tile, opened=False):
    """One of the 2 x 3 gate tiles, over masonry and floor. Opened by
    the three seals, the bars are gone and daylight fills the arch;
    the open tiles are floor, not door."""
    t = blank(W, H)
    pattern = GATE_OPEN if opened else GATE
    for y in range(H):
        gy = row * H + y
        line = pattern[gy]
        first = len(line) - len(line.lstrip("."))
        last = len(line.rstrip(".")) - 1
        for x in range(W):
            gx = column * W + x
            char = line[gx]
            if char != ".":
                t[y][x] = GATE_COLOURS[char]
            elif gy >= GATE_FLOOR_ROWS:
                t[y][x] = floor_tile.pixels[y][x]
            elif gy < GATE_ARCH_ROWS and (gx < first or gx > last):
                t[y][x] = wall_tiles[column].pixels[y][x]
    if opened:
        limit_colours(t, [(DARK_GREY, BLACK), (WHITE, YELLOW)])
        return Tile(f"gate.open.{column}{row}", t)
    solid = SOLID_ALL if row < 2 else SOLID_TOP
    return Tile(f"gate.{column}{row}", t, solid, TYPE_DOOR)


def limit_colours(t, drops):
    """Make every 4 x 8 cell encodable: while a cell shows more than
    three colours, replace colours following `drops` (a list of
    (colour, replacement) pairs, tried in order)."""
    for y0 in range(0, len(t), 8):
        for x0 in range(0, len(t[0]), 4):
            cell = [(y, x) for y in range(y0, y0 + 8)
                    for x in range(x0, x0 + 4)]
            for colour, replacement in drops:
                used = {t[y][x] for y, x in cell} - {BLACK}
                if len(used) <= 3:
                    break
                for y, x in cell:
                    if t[y][x] == colour:
                        t[y][x] = replacement


GRATE = [
    "................", ".L..L..LL..L..L.", "LLLLLLLLLLLLLLLL",
    "GGGGGGGGGGGGGGGG", ".L..L..LL..L..L.", ".L..L.YYYY.L..L.",
    ".L..L.YkkY.L..L.", ".L..L.YYkY.L..L.", ".L..L.YYYY.L..L.",
    ".L..L..LL..L..L.", ".L..L..LL..L..L.", "LLLLLLLLLLLLLLLL",
    "GGGGGGGGGGGGGGGG", ".L..L..LL..L..L.", ".L..L..LL..L..L.",
    "................",
]


def door_grate(open_tiles):
    """Locked door on the south edge: an iron grate with a brass
    lock over the two stair tiles. Returns the two closed tiles."""
    t = [a + b for a, b in zip(open_tiles[0].pixels, open_tiles[1].pixels)]
    for y in range(4, 9):                       # behind the lock plate
        for x in range(4, 12):
            if t[y][x] == DARK_GREY:
                t[y][x] = BLACK
    paint(t, 0, 0, GRATE, {"L": LIGHT_GREY, "G": GREY, "Y": YELLOW,
                           "k": BLACK})
    limit_colours(t, [(DARK_GREY, BLACK)])
    return [Tile(f"door.south.{half}", [row[half * W:(half + 1) * W]
                                        for row in t], SOLID_ALL, TYPE_DOOR)
            for half in (0, 1)]


GRATE_SIDE = [
    "..GLLLLL", "..G.L.L.", "..G.L.L.", "..G.L.L.", "..GLLLLL",
    "..G.L.L.", "..G.L.L.", "..G.L.L.", "..G.L.L.", "..G.L.L.",
    "..GLLLLL", "..G.L.L.", "..GYYYY.", "..GYkkY.", "..GYkYY.",
    "..GYYYY.", "..G.L.L.", "..G.L.L.", "..GLLLLL", "..G.L.L.",
    "..G.L.L.", "..G.L.L.", "..G.L.L.", "..G.L.L.", "..GLLLLL",
    "..G.L.L.", "..G.L.L.", "..G.L.L.", "..GLLLLL", "..G.L.L.",
    "..G.L.L.", "..GGGGGG",
]


def door_side(open_tiles, east):
    """Locked door on the east or west edge: an iron grate with a
    brass lock across the passage, over its two open tiles (one
    above the other). Returns the two closed tiles, top first."""
    t = [row[:] for row in open_tiles[0].pixels + open_tiles[1].pixels]
    pattern = GRATE_SIDE if east else [row[::-1] for row in GRATE_SIDE]
    for y, line in enumerate(pattern):
        for x, char in enumerate(line):
            if char == "." and (x >= 3 if east else x <= 4):
                t[y][x] = BLACK                 # dark beyond the bars
    paint(t, 0, 0, pattern, {"L": LIGHT_GREY, "G": GREY, "Y": YELLOW,
                             "k": BLACK})
    limit_colours(t, [(DARK_GREY, BLACK)])
    side = "east" if east else "west"
    return [Tile(f"door.{side}.{half}", t[half * H:(half + 1) * H],
                 SOLID_ALL, TYPE_DOOR) for half in (0, 1)]


def water(variant, edge):
    """Standing water, solid: dark blue with light ripples; `edge`
    adds the stone lip where floor or wall lies to the north."""
    t = blank(W, H)
    for y in range(H):
        for x in range(W):
            t[y][x] = BLUE
    ripples = [(1, 4), (2, 4), (3, 4), (5, 9), (6, 9), (2, 13), (3, 13),
               (4, 13)] if variant == 0 else \
        [(4, 3), (5, 3), (6, 3), (0, 8), (1, 8), (2, 8), (5, 12), (6, 12)]
    for x, y in ripples:
        t[y][x] = LIGHT_BLUE
    t[5 + variant * 4][4 - variant] = CYAN
    if edge:
        t[0] = [LIGHT_GREY] * W
        t[1] = [GREY] * W
        t[2] = [BLACK if x % 3 else BLUE for x in range(W)]
        limit_colours(t, [(CYAN, LIGHT_BLUE), (LIGHT_BLUE, BLUE)])
    name = f"water.{variant}" + ".edge" * edge
    return Tile(name, t, SOLID_ALL)


COINS = [
    ["........", ".YO.....", "OYY.....", ".O...YO.", "....YYO.",
     ".....O..", "........", "........"],
    ["........", "....YO..", "...OYY..", "....O...", ".YO.....",
     "YYO..YO.", ".O..OYY.", ".....O.."],
]


def floor_gold(variant, shadow=False):
    """Gold coins spilt on the cobblestones (walkable scenery)."""
    stone = variant * 2 + 3
    t = floor_shadow(stone).pixels if shadow else slab(stone)
    paint(t, 0, 7 if variant else 4, COINS[variant],
          {"Y": YELLOW, "O": ORANGE})
    limit_colours(t, [(GREY, DARK_GREY)])
    return Tile(f"floor.gold.{variant}" + ".shadow" * shadow, t)


URN = [
    "........", "..OOOO..", "...BB...", "..OYYO..", ".OYYYOO.",
    ".OYOOOO.", ".OOOOOB.", ".OOOOOB.", ".BOOOOB.", "..BOOB..",
    "..BBBB..", "........", "........", "........", "........",
    "........",
]


def urn(floor_tile):
    """A tall amber jar on the floor; solid."""
    t = [row[:] for row in floor_tile.pixels]
    for y in range(10, 13):                     # its shadow
        for x in range(1, 7):
            t[y][x] = BLACK
    paint(t, 0, 0, URN, {"O": ORANGE, "Y": YELLOW, "B": BROWN})
    limit_colours(t, [(GREY, DARK_GREY), (DARK_GREY, BLACK)])
    return Tile("urn", t, SOLID_ALL)


def well(column, row, floor_tiles):
    """Round stone well, 2 x 2 metatiles, drawn as a circle in screen
    pixels (a logical pixel is two screen pixels wide): lit stones on
    the rim, dark water inside with a glint. Solid."""
    size = 2 * W, 2 * H
    t = [a + b for a, b in zip(floor_tiles[0].pixels, floor_tiles[1].pixels)]
    t += [a + b for a, b in zip(floor_tiles[2].pixels,
                                floor_tiles[3].pixels)]
    for y in range(size[1]):
        for x in range(size[0]):
            dx, dy = x * 2 + 1 - 16, y + 0.5 - 16
            d = (dx * dx + dy * dy) ** 0.5
            if d > 15.5:
                continue
            if d > 10.5:                         # rim of stones
                seam = int((dx + 16) / 5 + (dy + 16) / 7) % 3 == 0 and \
                    abs(d - 13) < 0.8
                if seam:
                    t[y][x] = BLACK
                elif dy < -4 or (dx < -6 and dy < 6):
                    t[y][x] = LIGHT_GREY
                else:
                    t[y][x] = GREY
            elif d > 9.2 and dy < 0:             # shadow inside the rim
                t[y][x] = BLACK
            else:
                t[y][x] = BLUE
                if 2 < dx < 7 and 3 < dy < 6:
                    t[y][x] = LIGHT_BLUE
    for y in range(size[1]):                     # shadow on the floor
        for x in range(size[0]):
            dx, dy = x * 2 + 1 - 16, y + 0.5 - 16
            if 15.5 < (dx * dx + dy * dy) ** 0.5 < 17.5 and dy > 2:
                t[y][x] = BLACK
    limit_colours(t, [(LIGHT_BLUE, BLUE), (DARK_GREY, BLACK),
                      (GREY, BLACK)])
    part = [line[column * W:(column + 1) * W]
            for line in t[row * H:(row + 1) * H]]
    return Tile(f"well.{column}{row}", part, SOLID_ALL)


ALTAR = [
    "...Y................Y...", "...L................L...",
    ".LLLLLLLLLLLLLLLLLLLLLL.", ".GLLLLLLLLLLLLLLLLLLLLG.",
    ".GGGGGGGGGGGGGGGGGGGGGG.", "..GGGGGGGRRRRRRGGGGGGG..",
    "..GGGGGGGRRRRRRGGGGGGG..", "..GGGGGGGRRRRRRGGGGGGG..",
    "..GgGgGGGRRRRRRGGGgGgG..", "..GGGGGGGRRRRRRGGGGGGG..",
    "..GgGgGGGRRRRRRGGGgGgG..", "..GGGGGGGRRkkRRGGGGGGG..",
    "..gggggggRk..kRggggggg..", "..ggggggg......ggggggg..",
    "........................", "........................",
]


def altar(column, floor_tile):
    """Stone altar, 3 x 1 metatiles, red cloth, two candles; solid."""
    t = [row[:] * 3 for row in floor_tile.pixels]
    paint(t, 0, 0, ALTAR, {"L": LIGHT_GREY, "G": GREY, "g": DARK_GREY,
                           "R": RED, "k": BLACK, "Y": YELLOW})
    limit_colours(t, [(DARK_GREY, BLACK)])
    part = [line[column * W:(column + 1) * W] for line in t]
    return Tile(f"altar.{column}", part, SOLID_ALL)


PILLAR = [
    ".GGGGGG.", "GGLLLLGG", "GLggggLG", ".GggggG.", ".GLgggG.",
    ".GLgggG.", ".GGgggG.", ".GGg.gG.", ".GG.ggG.", ".G.gggG.",
    ".GLgggG.", ".GLgggG.", ".GGgggG.", ".GggggG.", ".gggggg.",
    ".GggggG.", ".GLgggG.", ".GLgggG.", ".GGgggG.", ".GGgggG.",
    ".GGgg.G.", ".GLg.gG.", ".GLgggG.", ".GGgggG.", ".GggggG.",
    ".GggggG.", "GGLLLLGG", "GggggggG", "GGGGGGGG", ".gggggg.",
    "........", "........",
]


def pillar(row, floor_tile):
    t = [line[:] for line in floor_tile.pixels]
    paint(t, 0, 0, PILLAR[row * H:(row + 1) * H],
          {"G": GREY, "L": LIGHT_GREY, "g": DARK_GREY})
    return Tile(f"pillar.{row}", t, SOLID_ALL)


# --- Zone palettes -----------------------------------------------------
# The pixels of a tile never change; a zone swaps colours in the four
# colour tables (screen RAM nibbles and Color RAM) of the whole catalog.
# Colours not listed stay (flames, gold, blood-red cloth, water, bone).
ZONE_PALETTES = {
    "atrio": {},                                # moss green, unchanged
    "A": {GREY: CYAN, GREEN: DARK_GREY,         # grey-blue crypt, the
          LIGHT_GREEN: GREY},                   # moss turned to dust
    "B": {DARK_GREY: BLUE, GREY: LIGHT_BLUE,    # blue stone,
          BLUE: CYAN, LIGHT_BLUE: WHITE,        # cyan water
          CYAN: WHITE, GREEN: CYAN, LIGHT_GREEN: LIGHT_GREY},
    "C": {DARK_GREY: BROWN, GREY: ORANGE,       # amber: brown floor,
          LIGHT_GREY: PINK, GREEN: ORANGE,      # orange and light
          LIGHT_GREEN: YELLOW},                 # red stone
}


def recoloured(value, palette):
    """A colour-table byte (two nibbles, or one) through a palette."""
    high, low = value >> 4, value & 15
    return (palette.get(high, high) << 4) | palette.get(low, low)

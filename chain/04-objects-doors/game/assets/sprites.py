"""Original sprite and animation recipes: the explorer, the objects
and the flames.

Sprite frames are 12 x 21 logical pixels (a 24 x 21 multicolor sprite).
Codes: '.' transparent, B brown (01, shared $d025), G the sprite's own
colour (10: $d027 for the explorer's green tunic), S light red (11,
shared $d026: the explorer's skin). The objects and the enemies use
the same two shared colours.
"""

# Original multicolor hero, eight frames: two per facing (down, up, left,
# right). Right-facing frames are mirrored from the left-facing recipes.
# B = brown outline/hair/boots (01), G = green tunic (10), S = skin (11).
HERO_DOWN = [[
    "....BBBB....", "...BBBBBB...", "...BSSSSB...", "...BS.SSB...", "....SSSS....",
    ".....SS.....", "...GGGGGG...", "..SGGGGGGS..", "..SGGGGGGS..", "..SGGGGGGS..",
    "...GGGGGG...", "...GBBBBG...", "...GGGGGG...", "...GG..GG...", "...BB..BB...",
    "...BB..BB...", "...BB..BB...", "..BBB..BBB..", "..BBB..BBB..", "............",
    "............",
], [
    "....BBBB....", "...BBBBBB...", "...BSSSSB...", "...BS.SSB...", "....SSSS....",
    ".....SS.....", "...GGGGGG...", "..GGGGGGGS..", "..SGGGGGGS..", "..SGGGGGG...",
    "...GGGGGG...", "...GBBBBG...", "...GGGGGG...", "...GG..GG...", "...BB..BB...",
    "...BB..BBB..", "..BBB...BB..", "..BBB.......", "............", "............",
    "............",
]]
HERO_UP = [[
    "....BBBB....", "...BBBBBB...", "...BBBBBB...", "...BBBBBB...", "....BBBB....",
    ".....SS.....", "...GGGGGG...", "..SGGGGGGS..", "..SGGGGGGS..", "..SGGGGGGS..",
    "...GGGGGG...", "...GBBBBG...", "...GGGGGG...", "...GG..GG...", "...BB..BB...",
    "...BB..BB...", "...BB..BB...", "..BBB..BBB..", "..BBB..BBB..", "............",
    "............",
], [
    "....BBBB....", "...BBBBBB...", "...BBBBBB...", "...BBBBBB...", "....BBBB....",
    ".....SS.....", "...GGGGGG...", "..SGGGGGGG..", "..SGGGGGGS..", "...GGGGGGS..",
    "...GGGGGG...", "...GBBBBG...", "...GGGGGG...", "...GG..GG...", "...BB..BB...",
    "..BBB..BB...", "..BB...BBB..", ".......BBB..", "............", "............",
    "............",
]]
HERO_LEFT = [[
    "....BBBB....", "...BBBBBB...", "..SSSBBBB...", "..S.SBBBB...", "..SSSSBB....",
    "....SS......", "...GGGGG....", "...GGGGGG...", "..SGGGGGG...", "..SGGGGG....",
    "...GGGGG....", "...GBBBG....", "...GGGGG....", "...GGGGG....", "...BBBB.....",
    "...BBBB.....", "...BBBB.....", "..BBBBB.....", "..BBBBB.....", "............",
    "............",
], [
    "....BBBB....", "...BBBBBB...", "..SSSBBBB...", "..S.SBBBB...", "..SSSSBB....",
    "....SS......", "...GGGGG....", "...GGGGGG...", "..SGGGGGG...", "..SGGGGG....",
    "...GGGGG....", "...GBBBG....", "...GGGGG....", "...GGGGG....", "..BBB.BB....",
    "..BB..BBB...", ".BB....BB...", ".BBB...BBB..", "............", "............",
    "............",
]]
HERO_RIGHT = [[row[::-1] for row in frame] for frame in HERO_LEFT]
HERO_FRAMES = HERO_DOWN + HERO_UP + HERO_LEFT + HERO_RIGHT



# Objects lying on the floor, drawn around the middle of the sprite
# (column 6, row 10), so that the sprite is centred on a metatile.
# Own colour (G): key yellow, seal light green, treasure yellow,
# potion white (the glass; the liquid is the shared light red); see
# OBJECT_COLOURS in game/src/objects.asm.
_ = "............"
OBJECT_KEY = [_] * 7 + [
    "..GGG.......", ".GB.BG......", ".G...GGGGGGG", ".GB.BGBBGBGB",
    "..GGG...GBG.", "...BB...B.B.",
] + [_] * 8
OBJECT_SEAL = [_] * 5 + [
    "....BBBB....", "...BGGGGB...", "..BGGSSGGB..", ".BGGSGGSGGB.",
    ".BGSGGGGSGB.", ".BGSGGGGSGB.", ".BGGSGGSGGB.", "..BGGSSGGB..",
    "...BGGGGB...", "....BBBB....",
] + [_] * 6
OBJECT_TREASURE = [_] * 6 + [
    ".....GG.....", "....GSGB....", "...GGGGGB...", "..GGBGGSGB..",
    "..GSGGGGGB..", ".GGGGBGGGGB.", ".GBGGGGSGBB.", "BBGGGGGGGBBB",
    ".BBBBBBBBBB.",
] + [_] * 6
OBJECT_POTION = [_] * 4 + [
    "....BBBB....", ".....BB.....", ".....GG.....", "....G..G....",
    "...GSSSSG...", "..GSSSSSSG..", "..GSGSSSSG..", "..GSSSSSSG..",
    "..GSSSSSSG..", "...GSSSSG...", "....GGGG....",
] + [_] * 6
OBJECT_FRAMES = [OBJECT_KEY, OBJECT_SEAL, OBJECT_TREASURE, OBJECT_POTION]

# Enemies, multicolour like the explorer. Skeleton: own colour
# light grey bones (G), brown joints and sockets (B), light red eyes (S).
# Bat: own colour purple body (G), brown wings (B), light red eyes (S).
# Dust: what is left for a moment of a defeated enemy.
SKELETON = [[
    "....GGGG....", "...GGGGGG...", "...GSBBSG...", "...GGGGGG...",
    "....GBGB....", ".....GG.....", "..GGBGGBGG..", ".G.GBGGBG.G.",
    ".G.BGBBGB.G.", ".G.GBGGBG.G.", ".B.BGGGGB.B.", "....GBBG....",
    "....G..G....", "....G..G....", "...GB..BG...", "...G....G...",
    "..GG....GG..", "............", _, _, _,
], [
    "....GGGG....", "...GGGGGG...", "...GSBBSG...", "...GGGGGG...",
    "....GBGB....", ".....GG.....", "..GGBGGBGG..", "..GGBGGBG.G.",
    ".G.BGBBGB.G.", ".G.GBGGBGG..", ".B.BGGGGB...", "....GBBG....",
    "....G..G....", "...G...G....", "..GB....G...", "..G.....BG..",
    ".GG.......G.", "............", _, _, _,
]]
BAT = [[
    _, _, _, "B..........B", "BB........BB", "BGB......BGB",
    "BGGB.GG.BGGB", ".BGGBGGBGGB.", "..BGGSGSGB..", "...BGGGGB...",
    "....BGGB....", ".....BB.....", _, _, _, _, _, _, _, _, _,
], [
    _, _, _, _, _, ".....GG.....", "....GSGS....", "..BBGGGGBB..",
    ".BGGGGGGGGB.", "BGGB.GG.BGGB", "BGB..BB..BGB", "BB........BB",
    "B..........B", _, _, _, _, _, _, _, _,
]]
DUST = [_] * 5 + [
    "..G...G..G..", ".GGG.GG.GGG.", "..GBGGGBGG..", "GGBGGBGGBGGG",
    ".GGBGGGBGG..", "..GGG.GGG.G.", ".G...G...G..",
] + [_] * 9
ENEMY_FRAMES = SKELETON + BAT + [DUST]

# The sword blade: a high-resolution sprite, one colour, 24 x 21
# screen pixels ('X' set). One frame per facing: down, up, left, right,
# in the order of the DIR_ values of hero.asm.
__ = "." * 24
BLADE_RIGHT = [__] * 8 + [
    ".....X..................", ".....X..................",
    "..XXXXXXXXXXXXXXXXXXX...", "..XXXXXXXXXXXXXXXXXXXX..",
    ".....X..................", ".....X..................",
] + [__] * 7
BLADE_LEFT = [row[::-1] for row in BLADE_RIGHT]
BLADE_UP = [__] * 1 + [
    "...........X............", "..........XXX...........",
    "..........XXX...........", "..........XXX...........",
    "..........XXX...........", "..........XXX...........",
    "..........XXX...........", "..........XXX...........",
    "..........XXX...........", "..........XXX...........",
    "..........XXX...........", "..........XXX...........",
    "........XXXXXXX.........", "..........XXX...........",
    "..........XXX...........", "..........XXX...........",
] + [__] * 4
BLADE_DOWN = BLADE_UP[::-1]
BLADE_FRAMES = [BLADE_DOWN, BLADE_UP, BLADE_LEFT, BLADE_RIGHT]


def encode_hires(rows):
    """24 x 21 high-resolution pattern -> 64 bytes."""
    data = bytearray()
    for row in rows:
        assert len(row) == 24, row
        data.extend(int(row.replace(".", "0").replace("X", "1"), 2)
                    .to_bytes(3, "big"))
    data.append(0)
    return bytes(data)


def encode_sprite(rows):
    """12 x 21 pattern -> 64 bytes (63 of data plus one padding byte)."""
    data = bytearray()
    for row in rows:
        assert len(row) == 12, row
        bits = 0
        for char in row:
            bits = (bits << 2) | {".": 0, "B": 1, "G": 2, "S": 3}[char]
        data.extend(bits.to_bytes(3, "big"))
    data.append(0)
    return bytes(data)


# Four torch-flame frames, one 4 x 8 cell each, drawn for the fixed
# cell palette R = red (01), O = orange (10), Y = yellow (11).
FLAMES = [
    ["..R.", "..O.", ".RO.", ".OY.", "ROYO", "ROYO", ".OO.", "..R."],
    [".R..", ".O..", ".OR.", ".YO.", "OYOR", "OYOR", ".OO.", ".R.."],
    ["....", "..R.", ".RO.", ".OO.", "ROYO", "ROYO", ".OY.", "..R."],
    ["..R.", ".RO.", ".OY.", "ROYO", "ROYO", ".OO.", ".OR.", "..R."],
]
FLAME_CODES = {".": 0, "R": 1, "O": 2, "Y": 3}


def encode_flames():
    data = bytearray()
    for frame in FLAMES:
        for row in frame:
            bits = 0
            for char in row:
                bits = (bits << 2) | FLAME_CODES[char]
            data.append(bits)
    return bytes(data)

"""Original big letters for the title and the end screens.

A big letter fills 3 x 5 cells of the multicolor bitmap: 12 x 40
logical pixels, the last column kept for spacing. It is drawn here
as 11 x 20 characters, each row doubled on the screen. The
shading is computed, not drawn: light comes from the top left, so
a pixel with empty space above or to its left is the highlight,
below or to its right the shadow, the others the body. Two seams
cut every letter into stone blocks, and the letter casts a shadow
one pixel to the right and one down, into its spacing column.

The three shades use the same bit codes in every letter: highlight
01 (screen RAM high nibble), body 10 (screen RAM low nibble), shadow
11 (Color RAM). A style gives each of the five cell rows its own three
colours, so the same letters make a stone logo, a red GAME OVER and a
gold VICTORY. print_big in game/src/screens.asm reads both files.
"""
from c64gfx import (BLACK, BROWN, DARK_GREY, GREEN, GREY, LIGHT_GREEN,
                    LIGHT_GREY, ORANGE, PINK, RED, WHITE, YELLOW)

WIDTH, HEIGHT = 11, 20          # drawing size; each row twice on screen
CELLS_ACROSS, CELLS_DOWN = 3, 5
LETTER_BYTES = CELLS_ACROSS * CELLS_DOWN * 8     # 120
STYLE_BYTES = 16                # 5 screen bytes, 5 Color RAM, 6 unused

LETTERS = {
    "A": ["...#####...", "..#######..", ".###...###.", "###.....###",
          "###.....###", "###.....###", "###.....###", "###.....###",
          "###########", "###########"] + ["###.....###"] * 10,
    "B": ["#########..", "##########.", "###.....###", "###.....###",
          "###.....###", "###.....###", "###....###.", "#########..",
          "##########.", "###.....###", "###.....###", "###.....###",
          "###.....###", "###.....###", "###.....###", "###.....###",
          "###.....###", "###....####", "##########.", "#########.."],
    "C": ["..#######..", ".#########.", "###.....###", "###.....###"]
         + ["###........"] * 12
         + ["###.....###", "###.....###", ".#########.", "..#######.."],
    "D": ["########...", "#########..", "###....###.", "###.....###"]
         + ["###.....###"] * 12
         + ["###.....###", "###....###.", "#########..", "########..."],
    "E": ["###########", "###########"] + ["###........"] * 6
         + ["#########..", "#########.."] + ["###........"] * 8
         + ["###########", "###########"],
    "F": ["###########", "###########"] + ["###........"] * 6
         + ["#########..", "#########.."] + ["###........"] * 10,
    "G": ["..#######..", ".#########.", "###.....###", "###.....###"]
         + ["###........"] * 5
         + ["###...#####", "###...#####"] + ["###.....###"] * 7
         + [".#########.", "..#######.."],
    "H": ["###.....###"] * 8 + ["###########"] * 2
         + ["###.....###"] * 10,
    "I": ["###########"] * 2 + ["....###...."] * 16 + ["###########"] * 2,
    "J": ["....#######", "....#######"] + ["........###"] * 12
         + ["###.....###"] * 4 + [".#########.", "..#######.."],
    "K": ["###.....###", "###.....###", "###....###.", "###....###.",
          "###...###..", "###...###..", "###..###...", "###.###....",
          "######.....", "#####......", "######.....", "###.###....",
          "###..###...", "###...###..", "###...###..", "###....###.",
          "###....###.", "###.....###", "###.....###", "###.....###"],
    "L": ["###........"] * 18 + ["###########"] * 2,
    "M": ["###.....###", "####...####", "#####.#####", "###########",
          "###.###.###", "###..#..###"] + ["###.....###"] * 14,
    "N": ["###.....###", "####....###", "####....###", "#####...###",
          "#####...###", "###.##..###", "###.##..###", "###..##.###",
          "###..##.###", "###...#####", "###...#####", "###....####",
          "###....####"] + ["###.....###"] * 7,
    "O": ["..#######..", ".#########."] + ["###.....###"] * 16
         + [".#########.", "..#######.."],
    "P": ["#########..", "##########."] + ["###.....###"] * 6
         + ["##########.", "#########.."] + ["###........"] * 10,
    "Q": ["..#######..", ".#########."] + ["###.....###"] * 12
         + ["###..##.###", "###...#####", "###....###.", ".#########.",
            "..#########", "........###"],
    "R": ["#########..", "##########."] + ["###.....###"] * 6
         + ["##########.", "#########..", "###.###....", "###..###...",
            "###..###...", "###...###..", "###...###..", "###....###.",
            "###....###.", "###.....###", "###.....###", "###.....###"],
    "S": ["..#######..", ".#########.", "###.....###", "###.....###"]
         + ["###........"] * 4
         + [".########..", "..########."] + ["........###"] * 6
         + ["###.....###", "###.....###", ".#########.", "..#######.."],
    "T": ["###########"] * 2 + ["....###...."] * 18,
    "U": ["###.....###"] * 18 + [".#########.", "..#######.."],
    "V": ["###.....###"] * 10
         + [".###...###.", ".###...###.", ".###...###.", "..###.###..",
            "..###.###..", "..###.###..", "...#####...", "...#####...",
            "....###....", "....###...."],
    "W": ["###.....###"] * 13
         + ["###..#..###", "###.###.###", "###########", "#####.#####",
            "####...####", "###.....###", "##.......##"],
    "X": ["###.....###"] * 3
         + [".###...###.", ".###...###.", "..###.###..", "..###.###..",
            "...#####...", "...#####...", "....###....", "....###....",
            "...#####...", "...#####...", "..###.###..", "..###.###..",
            ".###...###.", ".###...###."] + ["###.....###"] * 3,
    "Y": ["###.....###"] * 4
         + [".###...###.", ".###...###.", "..###.###..", "..###.###..",
            "...#####...", "...#####..."] + ["....###...."] * 10,
    "Z": ["###########"] * 2
         + ["........###", ".......###.", ".......###.", "......###..",
            "......###..", ".....###...", ".....###...", "....###....",
            "....###....", "...###.....", "...###.....", "..###......",
            "..###......", ".###.......", ".###.......", "###........"]
         + ["###########"] * 2,
}
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"   # glyph codes 1-26, as font.py

# Colours of the five cell rows: (highlight, body, shadow).
STYLES = {
    "logo": [(WHITE, LIGHT_GREY, DARK_GREY), (LIGHT_GREY, GREY, DARK_GREY),
             (LIGHT_GREY, GREY, DARK_GREY), (LIGHT_GREEN, GREY, DARK_GREY),
             (LIGHT_GREEN, GREEN, DARK_GREY)],
    "lost": [(WHITE, PINK, RED), (WHITE, PINK, RED), (PINK, RED, BROWN),
             (PINK, RED, BROWN), (RED, BROWN, DARK_GREY)],
    "won": [(WHITE, YELLOW, ORANGE), (WHITE, YELLOW, ORANGE),
            (YELLOW, ORANGE, BROWN), (YELLOW, ORANGE, BROWN),
            (ORANGE, BROWN, DARK_GREY)],
}
STYLE_ORDER = ["logo", "lost", "won"]           # style numbers 0, 1, 2


SEAMS = (13, 27)                # pixel rows cut between stone blocks


def shades(char):
    """The letter at screen resolution: 12 x 40 values, 0 empty,
    1 highlight, 2 body, 3 shadow."""
    art = LETTERS[char]
    assert len(art) == HEIGHT and all(len(r) == WIDTH for r in art), char
    full = [row for row in art for _ in range(2)]

    def filled(x, y):
        return 0 <= y < len(full) and 0 <= x < WIDTH and full[y][x] == "#"
    result = []
    for y in range(len(full)):
        line = []
        for x in range(WIDTH + 1):          # with the spacing column
            if not filled(x, y):
                line.append(3 if filled(x - 1, y - 1) else 0)
            elif y in SEAMS:
                line.append(3)
            elif not filled(x, y - 1) or y - 1 in SEAMS:
                line.append(1)
            elif not filled(x, y + 1):
                line.append(3)
            elif not filled(x - 1, y):
                line.append(1)
            elif not filled(x + 1, y):
                line.append(3)
            else:
                line.append(2)
        result.append(line)
    return result


def letter_bytes(char):
    """120 bytes: for each cell row, the 3 cells of the row one after
    the other (24 bytes), as they lie in the bitmap."""
    values = shades(char)
    data = bytearray()
    for row in range(CELLS_DOWN):
        for column in range(CELLS_ACROSS):
            for y in range(row * 8, row * 8 + 8):
                byte = 0
                for x in range(column * 4, column * 4 + 4):
                    byte = (byte << 2) | values[y][x]
                data.append(byte)
    assert len(data) == LETTER_BYTES
    return data


def font_bytes():
    assert set(LETTERS) == set(ALPHABET), "big alphabet incomplete"
    return b"".join(letter_bytes(char) for char in ALPHABET)


def style_bytes():
    data = bytearray()
    for name in STYLE_ORDER:
        rows = STYLES[name]
        data += bytes(light << 4 | body for light, body, _ in rows)
        data += bytes(shadow for _, _, shadow in rows)
        data += bytes(STYLE_BYTES - 10)
    return data


def draw(image, text, column, row, style):
    """Paint a big string into a 160 x 200 preview, as print_big."""
    colours = STYLES[style]
    for index, char in enumerate(text):
        if char == " ":
            continue
        values = shades(char)
        x0, y0 = (column + index * CELLS_ACROSS) * 4, row * 8
        for y in range(40):
            for x in range(12):
                shade = values[y][x]
                if shade:
                    image[y0 + y][x0 + x] = colours[y // 8][shade - 1]
    return image


if __name__ == "__main__":
    assert BLACK == 0
    print(len(font_bytes()), "bytes of big letters,",
          len(style_bytes()), "bytes of styles")

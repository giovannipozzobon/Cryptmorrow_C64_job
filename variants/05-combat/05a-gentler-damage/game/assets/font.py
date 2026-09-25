"""Original 3 x 5 font: one character per 4 x 8 logical-pixel cell.

The glyph number of a character is its position in GLYPH_ORDER. The
Assembly source declares the same numbering with .cdef in text.asm, so
strings written in the source and strings exported by this builder use
the same codes. '~' is the horizontal rule of the HUD and of the name
row; '*', '+' and '@' are the HUD icons: energy block, key, seal.
Glyph pixels use colour code 01: the colour comes from the high nibble
of the cell's screen RAM byte, set by print_text.
"""

GLYPH_ORDER = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-:./~*+@>"
END_OF_TEXT = 0xFF

GLYPHS = {
    " ": ["000", "000", "000", "000", "000"],
    "A": ["010", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "C": ["111", "100", "100", "100", "111"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "F": ["111", "100", "110", "100", "100"],
    "G": ["111", "100", "101", "101", "111"],
    "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"],
    "J": ["001", "001", "001", "101", "111"],
    "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"],
    "N": ["110", "101", "101", "101", "101"],
    "O": ["111", "101", "101", "101", "111"],
    "P": ["110", "101", "110", "100", "100"],
    "Q": ["111", "101", "101", "110", "011"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["111", "100", "111", "001", "111"],
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"],
    "W": ["101", "101", "111", "111", "101"],
    "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"],
    "Z": ["111", "001", "010", "100", "111"],
    "0": ["010", "101", "101", "101", "010"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["110", "001", "010", "100", "111"],
    "3": ["110", "001", "010", "001", "110"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "110", "001", "110"],
    "6": ["011", "100", "110", "101", "010"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["010", "101", "010", "101", "010"],
    "9": ["010", "101", "011", "001", "110"],
    "-": ["000", "000", "111", "000", "000"],
    ":": ["000", "010", "000", "010", "000"],
    ".": ["000", "000", "000", "000", "010"],
    "/": ["001", "001", "010", "100", "100"],
}
# HUD icons use the whole 4 x 8 cell: '#' is a lit pixel.
ICONS = {
    "*": ["....", "###.", "###.", "###.", "###.", "###.", "....",
          "...."],
    "+": [".##.", "#..#", ".##.", ".#..", ".##.", ".#..", ".##.",
          "...."],
    "@": ["....", ".##.", "#..#", "#.##", "#..#", ".##.", "....",
          "...."],
    ">": ["....", "#...", "##..", "###.", "##..", "#...", "....",
          "...."],                          # menu cursor
}
GLYPH_TOP = 1          # first glyph row inside the 8-row cell
RULE_ROW = 3           # the rule glyph is one full line on this row


def glyph_bytes(char):
    """Eight bitmap bytes for one character."""
    rows = [0] * 8
    if char == "~":
        rows[RULE_ROW] = 0b01010101
        return bytes(rows)
    if char in ICONS:
        for index, pattern in enumerate(ICONS[char]):
            for bit in pattern:
                rows[index] = (rows[index] << 2) | (bit == "#")
        return bytes(rows)
    for index, pattern in enumerate(GLYPHS[char]):
        value = 0
        for bit in pattern + "0":
            value = (value << 2) | (1 if bit == "1" else 0)
        rows[GLYPH_TOP + index] = value
    return bytes(rows)


def font_bytes():
    assert set(GLYPH_ORDER) - {"~"} == set(GLYPHS) | set(ICONS), \
        "font incomplete"
    return b"".join(glyph_bytes(char) for char in GLYPH_ORDER)


def encode_text(text, column, row, colour):
    """[column][row][colour][glyph codes...][$ff], as print_text reads."""
    if column + len(text) > 40:
        raise ValueError(f"text too long for row: {text!r}")
    codes = bytes(glyph_code(char, text) for char in text)
    return bytes([column, row, colour]) + codes + bytes([END_OF_TEXT])


def glyph_code(char, text):
    """The code of a character of a string; a character that is not
    in the font stops the build, naming the character and the string."""
    if char not in GLYPH_ORDER:
        raise ValueError(f"{char!r} is not in the font (GLYPH_ORDER of "
                         f"font.py): {text!r}")
    return GLYPH_ORDER.index(char)

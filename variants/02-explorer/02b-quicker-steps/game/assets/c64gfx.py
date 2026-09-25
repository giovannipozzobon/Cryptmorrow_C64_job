"""Small helpers shared by the asset builder and the tests.

C64 multicolor bitmap facts used everywhere in Cryptmorrow:
- one logical pixel is two screen pixels wide;
- a cell is 4 x 8 logical pixels (8 x 8 on screen), 8 bitmap bytes;
- each cell shows black (the shared background, code 00) plus up to
  three colours of its own: screen RAM high nibble (code 01), screen
  RAM low nibble (code 10) and Color RAM (code 11).
Only the Python standard library is used.
"""
import struct
import zlib

# VICE "pepto" PAL palette, used only for previews on the PC.
PALETTE = [
    0x000000, 0xFFFFFF, 0x68372B, 0x70A4B2, 0x6F3D86, 0x588D43,
    0x352879, 0xB8C76F, 0x6F4F25, 0x433900, 0x9A6759, 0x444444,
    0x6C6C6C, 0x9AD284, 0x6C5EB5, 0x959595,
]

BLACK, WHITE, RED, CYAN, PURPLE, GREEN, BLUE, YELLOW = range(8)
ORANGE, BROWN, PINK, DARK_GREY, GREY, LIGHT_GREEN = range(8, 14)
LIGHT_BLUE, LIGHT_GREY = 14, 15


def blank(width, height):
    return [[BLACK] * width for _ in range(height)]


def paint(canvas, x, y, rows, colours):
    """Draw a text pattern; '.' leaves the canvas unchanged."""
    for yy, row in enumerate(rows):
        for xx, char in enumerate(row):
            if char != ".":
                canvas[y + yy][x + xx] = colours[char]


def encode_cell(pixels, forced=None):
    """Encode 4x8 logical pixels. Returns (8 bytes, screen, color).

    Colours are ranked in ascending order: the smallest becomes code 01
    (screen high nibble), the next code 10 (screen low nibble), the
    third code 11 (Color RAM). `forced` imposes an explicit order, used
    by animated cells whose frames were drawn for a fixed palette.
    """
    used = sorted({c for row in pixels for c in row} - {BLACK})
    if forced is not None:
        if not set(used) <= set(forced):
            raise ValueError(f"cell colours {used} not in {forced}")
        used = list(forced)
    if len(used) > 3:
        raise ValueError(f"cell uses {len(used)} colours: {used}")
    local = (used + [BLACK] * 3)[:3]
    code = {BLACK: 0}
    for index, colour in enumerate(local):
        if colour != BLACK:
            code[colour] = index + 1
    data = bytearray()
    for row in pixels:
        value = 0
        for colour in row:
            value = (value << 2) | code[colour]
        data.append(value)
    return bytes(data), local[0] * 16 + local[1], local[2]


def decode_cell(data, screen, color):
    """Inverse of encode_cell, used by previews and tests."""
    lookup = [BLACK, screen >> 4, screen & 15, color & 15]
    return [[lookup[(byte >> shift) & 3] for shift in (6, 4, 2, 0)]
            for byte in data]


def decode_screen(bitmap, screen, color):
    """Turn C64 memory images into a 160x200 logical-pixel picture."""
    image = blank(160, 200)
    for cell in range(1000):
        cx, cy = cell % 40, cell // 40
        pixels = decode_cell(bitmap[cell * 8:cell * 8 + 8],
                             screen[cell], color[cell])
        for yy in range(8):
            image[cy * 8 + yy][cx * 4:cx * 4 + 4] = pixels[yy]
    return image


def write_png(path, image, scale=2):
    """Save logical pixels as RGB PNG, doubling each pixel horizontally."""
    height, width = len(image), len(image[0])
    rows = []
    for row in image:
        line = bytearray()
        for colour in row:
            rgb = PALETTE[colour].to_bytes(3, "big")
            line += rgb * (2 * scale)
        for _ in range(scale):
            rows.append(b"\x00" + bytes(line))

    def chunk(kind, body):
        crc = zlib.crc32(kind + body) & 0xFFFFFFFF
        return struct.pack(">I", len(body)) + kind + body + \
            struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", width * 2 * scale, height * scale,
                         8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
    png += chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(png)

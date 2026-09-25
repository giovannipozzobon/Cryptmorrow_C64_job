"""Reference renderer: what the C64 memory must contain after print_hud
and draw_room; also the title and end screens (draw_screen,
print_big and the strings of screens.asm).

Independent from the Assembly: it reads the files exported by the asset
builder and applies the rules documented in game/src/room.asm, text.asm
and hud.asm, so a mistake in either the 6502 code or the exported tables
shows up as a difference.
"""
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
GENERATED = PROJECT / "game/assets/generated"
sys.path.insert(0, str(PROJECT / "game/assets"))

import c64gfx  # noqa: E402

FIRST_ROW, MAP_W, MAP_H = 3, 20, 10
TYPE_TORCH_LEFT, TYPE_TORCH_RIGHT, TYPE_DOOR = 1, 2, 4
WALL_CELL, DOOR_CELL = 1, 2
TEXT_END = 0xFF
BITMAP, SCREEN = 0x6000, 0x4400
ROOM_PAGE = 256
NAME_AT = 228                           # name string in a room page
OBJECTS_AT, DOOR_AT = 200, 208          # objects and door, same page
ZONE_AT = 209                           # zone of the room
DOOR_LIST, LIST_END = 32, 0xFF          # doors.bin: open tiles

SCREEN_PAGES = {"title": 0, "lost": 1, "won": 2}   # screens.bin
BIG_BYTES, STYLE_BYTES = 120, 16        # big.font, big.styles
MENU_GREY, MENU_YELLOW, CURSOR = 12, 7, 45
PROMPT_ROW, PROMPT_COLUMN, PROMPT_LENGTH = 22, 15, 10
STATS_ROW, VALUE_COLUMN = 18, 21

# The HUD values as documented in game/src/hud.asm.
HUD_ROW, ENERGY_MAX, BAR_COLUMN = 1, 8, 8
KEYS_COLUMN, SEALS_COLUMN, SCORE_COLUMN = 19, 23, 34
FULL, LOST, DIGIT = 10, 11, 1           # light red, dark grey, white
GLYPH_ZERO = 27


def load(name):
    return (GENERATED / name).read_bytes()


class Screen:
    """Bitmap, screen RAM, Color RAM and walkability, as after
    clear_screen: black everywhere, every cell solid."""

    def __init__(self):
        self.bitmap = bytearray(8000)
        self.screen = bytearray(1000)
        self.color = bytearray(1000)
        self.solid = bytearray([1] * 1000)
        self.torches = []
        self.font = load("font.bin")

    def room_page(self, slot):
        return load("rooms.bin")[slot * ROOM_PAGE:(slot + 1) * ROOM_PAGE]

    def draw_tile(self, c, r, tile, torches=True):
        """Metatile `tile` at map column c, row r (draw_half twice)."""
        attr = self.attr[tile]
        kind = (attr >> 4) & 7
        for cell in range(4):
            cx = c * 2 + cell % 2
            cy = FIRST_ROW + r * 2 + cell // 2
            index = cy * 40 + cx
            source = tile * 32 + cell * 8
            self.bitmap[index * 8:index * 8 + 8] = \
                self.tiles[source:source + 8]
            side = "left" if cell % 2 == 0 else "right"
            slot = tile + (128 if cell >= 2 else 0)
            self.screen[index] = self.tables["screen_" + side][slot]
            self.color[index] = self.tables["color_" + side][slot]
            solid = (attr >> cell) & 1
            self.solid[index] = solid and (
                DOOR_CELL if kind == TYPE_DOOR else WALL_CELL)
            flame_cell = {TYPE_TORCH_LEFT: 0,
                          TYPE_TORCH_RIGHT: 1}.get(kind)
            if torches and cell == flame_cell and len(self.torches) < 6:
                self.torches.append(BITMAP + index * 8)

    def draw_room(self, room):
        """set_zone, then draw_room: the colour tables are the
        zone's copy from zones.color."""
        self.tiles = load("tiles.bitmap")
        self.attr = load("tiles.attr")
        zone = load("zones.color")[room[ZONE_AT] * 1024:][:1024]
        self.tables = {name: zone[n * 256:(n + 1) * 256] for n, name in
                       enumerate(("screen_left", "screen_right",
                                  "color_left", "color_right"))}
        for r in range(MAP_H):
            for c in range(MAP_W):
                self.draw_tile(c, r, room[r * MAP_W + c])
        self.clear_row(24)
        self.print_text(room[NAME_AT:])

    def open_door(self, room):
        """The open tiles of the room's door or portal (show_door):
        the list of its number in doors.bin."""
        number = room[DOOR_AT]
        data = load("doors.bin")[(number - 1) * DOOR_LIST:][:DOOR_LIST]
        for n in range(0, DOOR_LIST, 3):
            if data[n] == LIST_END:
                break
            self.draw_tile(data[n], data[n + 1], data[n + 2],
                           torches=False)

    def clear_row(self, row):
        self.bitmap[row * 320:row * 320 + 320] = bytes(320)
        self.screen[row * 40:row * 40 + 40] = bytes(40)

    def print_text(self, data):
        column, row, colour = data[0], data[1], data[2]
        for offset, code in enumerate(data[3:]):
            if code == TEXT_END:
                return offset
            index = row * 40 + column + offset
            self.bitmap[index * 8:index * 8 + 8] = \
                self.font[code * 8:code * 8 + 8]
            self.screen[index] = colour << 4
        raise ValueError("string without TEXT_END")

    def print_list(self, data):
        """Strings one after another, up to a TEXT_END that starts
        a string. Returns the bytes used."""
        position = 0
        while data[position] != TEXT_END:
            position += self.print_text(data[position:]) + 4
        return position + 1

    def hud(self, energy, keys, seals, score):
        """Values of the HUD: score is a six-digit number."""
        for cell in range(ENERGY_MAX):
            colour = FULL if cell < energy else LOST
            self.screen[HUD_ROW * 40 + BAR_COLUMN + cell] = colour << 4
        digits = [(KEYS_COLUMN, keys), (SEALS_COLUMN, seals)]
        digits += [(SCORE_COLUMN + i, int(d))
                   for i, d in enumerate(f"{score:06d}")]
        for column, digit in digits:
            self.print_text(bytes([column, HUD_ROW, DIGIT,
                                   GLYPH_ZERO + digit, TEXT_END]))

    def print_big(self, data):
        """print_big: column, row, style, glyph codes, TEXT_END; each
        letter 3 x 5 cells from big.font, the colours of each cell row
        from the style in big.styles."""
        font, styles = load("big.font"), load("big.styles")
        column, row, style = data[0], data[1], data[2]
        colours = styles[style * STYLE_BYTES:][:STYLE_BYTES]
        for code in data[3:]:
            if code == TEXT_END:
                return
            if code:
                glyph = font[(code - 1) * BIG_BYTES:][:BIG_BYTES]
                for line in range(5):
                    index = (row + line) * 40 + column
                    self.bitmap[index * 8:index * 8 + 24] = \
                        glyph[line * 24:line * 24 + 24]
                    for cell in range(3):
                        self.screen[index + cell] = colours[line]
                        self.color[index + cell] = colours[5 + line]
            column += 3
        raise ValueError("big string without TEXT_END")

    def prompt_colour(self, colour):
        """The glow of PRESS FIRE: screen RAM of its cells."""
        start = PROMPT_ROW * 40 + PROMPT_COLUMN
        self.screen[start:start + PROMPT_LENGTH] = \
            bytes([colour]) * PROMPT_LENGTH

    def digits(self, text, column, row):
        for offset, char in enumerate(text):
            self.print_text(bytes([column + offset, row, DIGIT,
                                   GLYPH_ZERO + int(char), TEXT_END]))

    def image(self):
        return c64gfx.decode_screen(self.bitmap, self.screen, self.color)


def expected_screen(hud_frame, slot, values=(8, 0, 0, 0),
                    door_open=False):
    """The screen after print_hud and draw_room of room `slot`, with
    the HUD showing `values` (energy, keys, seals, score) and the
    room's door open or closed. hud_frame: the string list read from
    the program."""
    result = Screen()
    result.print_list(hud_frame)
    result.hud(*values)
    page = result.room_page(slot)
    result.draw_room(page)
    if door_open:
        result.open_door(page)
    return result


def screen_page(name):
    number = SCREEN_PAGES[name]
    return load("screens.bin")[number * ROOM_PAGE:][:ROOM_PAGE]


def expected_title(texts, mode):
    """The title screen after show_title with `mode` chosen. texts:
    the strings read from the program (logo_text, menu_music,
    menu_fx, menu_silent, prompt_text); the cursor and colours of the
    menu lines are set here, as show_menu sets them."""
    result = Screen()
    result.draw_room(screen_page("title"))
    result.print_big(texts["logo_text"])
    for line, name in enumerate(("menu_music", "menu_fx", "menu_silent")):
        data = bytearray(texts[name])
        chosen = line == mode
        data[2] = MENU_YELLOW if chosen else MENU_GREY
        data[3] = CURSOR if chosen else 0
        result.print_text(data)
    result.print_text(texts["prompt_text"])
    return result


def expected_end(texts, how, score, seals, rooms, prompt):
    """The end screen after show_end: `how` is "lost" or "won"; the
    score, the seals and the number of rooms entered; PRESS FIRE once
    END_DELAY has passed (prompt)."""
    result = Screen()
    result.draw_room(screen_page(how))
    result.print_big(texts["lost_word" if how == "lost" else "won_word"])
    result.print_list(texts["stats_text"])
    result.digits(f"{score:06d}", VALUE_COLUMN, STATS_ROW)
    result.digits(f"{seals}", VALUE_COLUMN, STATS_ROW + 1)
    result.digits(f"{rooms:02d}", VALUE_COLUMN, STATS_ROW + 2)
    if prompt:
        result.print_text(texts["prompt_text"])
    return result

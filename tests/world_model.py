"""Python model of the dungeon rules in game/src/world.asm and
game/src/objects.asm.

Exits: a room is left when the explorer's hitbox enters the outermost
ring of cells of the playfield, and the explorer reappears eight pixels
inside the facing edge of the neighbouring room (-4 north, +4 south,
-1 west, +1 east); leaving the start room to the north, through the
open portal, wins the game. Doors: a door that stops the explorer
opens if the explorer carries its key, which is used up; the portal
(door 4) opens with all three seals. Objects: picked up when the
middle of the hitbox is inside their metatile; a potion stays on the
floor while the energy is full. Same order as the main loop:
update_hero, check_exits, check_door, check_objects. The
world also keeps the rooms entered (rooms_seen, for the end screen)
and the sound effects asked for (sounds), and starts in the state the
program has before the first game (every variable 0).
"""
import hero_model as H
import reference

GRID = 4
FIRST_ROW, CELL_ROWS = 3, 20
ENTRY_MARGIN = 8
NORTH_EDGE = FIRST_ROW * 8 + 7 - H.BOX_TOP
SOUTH_EDGE = (FIRST_ROW + CELL_ROWS - 1) * 8 - H.BOX_BOTTOM
WEST_EDGE = 7 - H.BOX_LEFT
EAST_EDGE = 39 * 8 - H.BOX_RIGHT
HIT_X = (H.BOX_LEFT + H.BOX_RIGHT) // 2
HIT_Y = (H.BOX_TOP + H.BOX_BOTTOM) // 2

ENERGY_MAX, POTION_ENERGY = 8, 2
PORTAL, MAX_SEALS = 4, 3
DOOR_NAMES = {1: "door A", 2: "door B", 3: "door C", 4: "portal"}
KIND_SEAL, KIND_TREASURE, KIND_POTION = 4, 5, 6
POINTS = {KIND_SEAL: 1000, KIND_TREASURE: 250}
OBJECT_POINTER = 8                      # sprites at $4200
FRAMES = {1: 0, 2: 0, 3: 0, 4: 1, 5: 2, 6: 3}
COLOURS = {1: 7, 2: 7, 3: 7, 4: 13, 5: 7, 6: 1}


class World:
    def __init__(self, hud_frame, start, over_text=None, won_text=None):
        self.hud_frame = hud_frame
        self.start = start
        self.texts = {"lost": over_text,        # strings of combat.asm:
                      "won": won_text}          # GAME OVER, VICTORY
        self.events = []                # what happened, for the report
        self.sounds = []                # effects asked for (Game.step)
        self.pages = reference.load("rooms.bin")
        self.slot, self.energy, self.key_set, self.seals = 0, 0, 0, 0
        self.score, self.doors_open, self.taken = 0, 0, set()
        self.seen = set()               # before the first game: all 0
        self.ended = None

    def new_game(self):
        """init_game: start room, full energy, nothing taken; then
        enter_room marks the start room as seen."""
        self.slot = self.start
        self.energy, self.key_set, self.seals, self.score = 8, 0, 0, 0
        self.doors_open, self.taken = 0, set()
        self.seen = {self.start}
        self.ended = None               # "lost" or "won"

    def page(self, slot=None):
        slot = self.slot if slot is None else slot
        return self.pages[slot * 256:(slot + 1) * 256]

    def door(self, slot=None):
        """Number of the room's door (0 none, 1-3 keys A-C, 4 the
        portal) and whether it is open."""
        number = self.page(slot)[reference.DOOR_AT]
        return number, bool(number and
                            self.doors_open & (1 << (number - 1)))

    def objects(self, slot=None):
        """(slot index, kind, column, row, number) still in the room."""
        page = self.page(slot)
        found = []
        for n in range(2):
            kind, c, r, number = page[200 + n * 4:204 + n * 4]
            if kind and number not in self.taken:
                found.append((n, kind, c, r, number))
        return found

    def keys(self):
        return bin(self.key_set).count("1")

    def hud_values(self):
        return (self.energy, self.keys(), self.seals, self.score)

    def screen(self, slot=None):
        """Reference screen of a room with the current HUD values;
        at the end of a game the name row shows GAME OVER or VICTORY."""
        slot = self.slot if slot is None else slot
        result = reference.expected_screen(
            self.hud_frame, slot, self.hud_values(), self.door(slot)[1])
        if self.ended:
            result.clear_row(24)
            result.print_text(self.texts[self.ended])
        return result

    def sprites(self):
        """Expected sprites 5 and 6: None, or (pointer, colour, VIC X,
        VIC Y)."""
        shown = [None, None]
        for n, kind, c, r, number in self.objects():
            shown[n] = (OBJECT_POINTER + FRAMES[kind], COLOURS[kind],
                        c * 16 - 4 + 24, r * 16 + 22 + 50)
        return shown

    def check_exits(self, hero):
        """After hero.update(): returns the new room or None. Out of
        the start room to the north (only the open portal leads there)
        the game is won."""
        if hero.y <= NORTH_EDGE and self.slot == self.start:
            self.ended = "won"
            self.events.append("VICTORY")
            self.sounds.append(("end", 2))      # ENDED_WON
            return None
        if hero.y <= NORTH_EDGE:
            hero.y, step = SOUTH_EDGE - ENTRY_MARGIN, -GRID
        elif hero.y >= SOUTH_EDGE:
            hero.y, step = NORTH_EDGE + ENTRY_MARGIN, GRID
        elif hero.x <= WEST_EDGE:
            hero.x, step = EAST_EDGE - ENTRY_MARGIN, -1
        elif hero.x >= EAST_EDGE:
            hero.x, step = WEST_EDGE + ENTRY_MARGIN, 1
        else:
            return None
        self.slot += step
        self.seen.add(self.slot)
        hero.solid = list(self.screen().solid)
        return self.slot

    def check_door(self, hero):
        number, opened = self.door()
        if hero.block != reference.DOOR_CELL or not number or opened:
            return False
        bit = 1 << (number - 1)
        if number == PORTAL:
            if self.seals != MAX_SEALS:
                return False
        elif not self.key_set & bit:
            return False
        else:
            self.key_set ^= bit
        self.doors_open |= bit
        hero.solid = list(self.screen().solid)
        self.events.append(f"{DOOR_NAMES[number]} opened")
        self.sounds.append(("effect", "DOOR"))
        return True

    def check_objects(self, hero):
        column = (hero.x + HIT_X) // 16
        row = (hero.y + HIT_Y - 24) // 16
        taken = []
        for n, kind, c, r, number in self.objects():
            if (c, r) != (column, row):
                continue
            if kind == KIND_POTION:
                if self.energy >= ENERGY_MAX:
                    continue
                self.energy = min(ENERGY_MAX, self.energy + POTION_ENERGY)
            elif kind < KIND_SEAL:
                self.key_set |= 1 << (kind - 1)
            else:
                self.seals += kind == KIND_SEAL
                self.score += POINTS[kind]
            self.taken.add(number)
            taken.append(kind)
            self.events.append(f"object {number} (kind {kind}) taken")
            self.sounds.append(("effect", "PICKUP"))
        return taken

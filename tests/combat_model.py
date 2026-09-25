"""Python model of the combat rules in game/src/combat.asm.

Same rules and the same order as the main loop: check_fire (before
update_hero), then after the dungeon checks update_enemies, check_blade
and check_contact; show_combat gives the sprites. Distances follow
`measure` exactly: 16-bit X, 8-bit Y, 255 for "far".
"""
import hero_model as H

SLASH_FRAMES, BLADE_FRAMES = 20, 8
BLADE_UNTIL = SLASH_FRAMES - BLADE_FRAMES
SAFE_FRAMES = 30
DAMAGE = 2                              # cells of energy a touch
FLASH_FRAMES, DUST_FRAMES = 8, 12
REACH = 12
CHASE_X, CHASE_Y = 120, 90
RING_LEFT, RING_RIGHT, RING_TOP, RING_BOTTOM = 8, 312, 32, 176
MAX_ENEMIES = 3                         # enemy slots in a room page
SKELETON, BAT = 1, 2
HP = {SKELETON: 3, BAT: 1}
POINTS = {SKELETON: 100, BAT: 50}
ENEMIES_AT = 216
STRIKE = {H.DIR_DOWN: (3, 16), H.DIR_UP: (3, -20),
          H.DIR_LEFT: (-20, -1), H.DIR_RIGHT: (20, -1)}
NEAR = {H.DIR_DOWN: (3, 8), H.DIR_UP: (3, -10),       # half way back
        H.DIR_LEFT: (-10, -1), H.DIR_RIGHT: (10, -1)}
FAST_FLAG = 2
ENDED_LOST, ENDED_WON = 1, 2
BLADE_VIC = {H.DIR_DOWN: (28, 62), H.DIR_UP: (28, 34),
             H.DIR_LEFT: (6, 49), H.DIR_RIGHT: (42, 49)}
COMBAT_POINTER = 32                     # sprites at $4800
FRAMES = {SKELETON: COMBAT_POINTER, BAT: COMBAT_POINTER + 2}
DUST_FRAME = COMBAT_POINTER + 4
BLADE_FRAME = COMBAT_POINTER + 5
COLOURS = {SKELETON: 15, BAT: 4}
FLASH_COLOUR, BLADE_COLOUR = 10, 1


def far_x(point, enemy):
    """|point - enemy| as measure computes it (16-bit, 255 if far),
    and whether the point is to the west."""
    difference = (point - enemy) & 0xFFFF
    high, low = difference >> 8, difference & 255
    if high == 0:
        return low, False
    if high == 0xFF:
        negated = (256 - low) & 255
        return (negated or 255), True
    return 255, False


def far_y(point, enemy):
    point &= 255
    return abs(point - enemy), point < enemy


class Enemy:
    def __init__(self, kind, column, row, flags):
        self.kind = kind
        self.x = column * 16 - 4
        self.y = row * 16 + 20
        self.dir = H.DIR_DOWN if flags & 1 else H.DIR_RIGHT
        self.fast = flags & FAST_FLAG
        self.hp = HP.get(kind, 0)
        self.flash = self.dust = self.hit = 0

    def state(self):
        return (self.kind, self.x, self.y, self.dir, self.hp, self.flash,
                self.dust, self.hit, self.fast)

    @classmethod
    def empty(cls):
        """A slot never filled: every byte 0, as before the first
        game."""
        enemy = cls(0, 0, 0, 0)
        enemy.x = enemy.y = enemy.dir = 0
        return enemy


class Combat:
    def __init__(self, world, spawn=True):
        self.world = world
        self.slash = self.blade_dir = self.fire_held = self.safe = 0
        self.ended = 0                  # ENDED_LOST or ENDED_WON
        self.near_hits = 0              # hits only the near point made
        self.enemies = [Enemy.empty() for _ in range(MAX_ENEMIES)]
        if spawn:
            self.spawn()

    def spawn(self):
        page = self.world.page()
        self.enemies = [Enemy(*page[ENEMIES_AT + n * 4:ENEMIES_AT + n * 4 + 4])
                        for n in range(MAX_ENEMIES)]

    def blade_out(self):
        return self.slash > BLADE_UNTIL

    def check_fire(self, joy, hero):
        """Returns the joystick bits update_hero sees."""
        if self.slash:
            self.slash -= 1
        fire = joy & H.JOY_FIRE
        changed = fire != self.fire_held
        self.fire_held = fire
        if changed and fire and not self.slash:
            self.slash = SLASH_FRAMES
            self.blade_dir = hero.dir
            for enemy in self.enemies:
                enemy.hit = 0
            self.world.sounds.append(("effect", "SLASH"))
        return 0 if self.blade_out() else joy

    def blocked(self, enemy, solid):
        def cell(x, y):
            if not (RING_TOP <= y < RING_BOTTOM and
                    RING_LEFT <= x < RING_RIGHT):
                return 1
            return solid[(y // 8) * 40 + x // 8]
        if enemy.dir in (H.DIR_DOWN, H.DIR_UP):
            y = enemy.y + (H.BOX_BOTTOM + 1 if enemy.dir == H.DIR_DOWN
                           else H.BOX_TOP - 1)
            return cell(enemy.x + H.BOX_LEFT, y) or \
                cell(enemy.x + H.BOX_RIGHT, y)
        x = enemy.x + (H.BOX_RIGHT + 1 if enemy.dir == H.DIR_RIGHT
                       else H.BOX_LEFT - 1)
        return cell(x, enemy.y + H.BOX_TOP) or \
            cell(x, enemy.y + H.BOX_BOTTOM)

    def update(self, frame, hero):
        for enemy in reversed(self.enemies):
            if not enemy.kind:
                continue
            if enemy.dust:
                enemy.dust -= 1
                if not enemy.dust:
                    enemy.kind = 0
                continue
            if enemy.flash:
                enemy.flash -= 1
                continue
            if enemy.kind == SKELETON:
                if frame & 1 and not enemy.fast:
                    continue
                if self.blocked(enemy, hero.solid):
                    enemy.dir ^= 1
                else:
                    self.step(enemy, enemy.dir)
            else:
                fx, west = far_x(hero.x, enemy.x)
                fy, north = far_y(hero.y, enemy.y)
                if fx >= CHASE_X or fy >= CHASE_Y:
                    continue
                if frame & 1 == 0:
                    if fx:
                        self.step(enemy, H.DIR_LEFT if west
                                  else H.DIR_RIGHT)
                elif fy:
                    self.step(enemy, H.DIR_UP if north else H.DIR_DOWN)

    @staticmethod
    def step(enemy, direction):
        if direction == H.DIR_LEFT:
            enemy.x -= 1
        elif direction == H.DIR_RIGHT:
            enemy.x += 1
        elif direction == H.DIR_UP:
            enemy.y -= 1
        else:
            enemy.y += 1

    def check_blade(self, hero):
        """Returns the enemies defeated by this frame's blade: all
        enemies against the point ahead, then against the point half
        way back."""
        if not self.blade_out():
            return []
        defeated = []
        for near, (sx, sy) in enumerate((STRIKE[self.blade_dir],
                                         NEAR[self.blade_dir])):
            self.near_hits += self.blade_point(hero, sx, sy, defeated) * near
        return defeated

    def blade_point(self, hero, sx, sy, defeated):
        """Returns how many enemies this point hit."""
        hits = 0
        for n in reversed(range(MAX_ENEMIES)):
            enemy = self.enemies[n]
            if not enemy.kind or enemy.dust or enemy.hit:
                continue
            if far_x(hero.x + sx, enemy.x)[0] >= REACH or \
                    far_y(hero.y + sy, enemy.y)[0] >= REACH:
                continue
            enemy.hit = 1
            hits += 1
            enemy.hp -= 1
            if enemy.hp:
                enemy.flash = FLASH_FRAMES
                self.world.events.append(f"enemy {n} hit")
                self.world.sounds.append(("effect", "HIT"))
            else:
                enemy.dust = DUST_FRAMES
                self.world.score += POINTS[enemy.kind]
                defeated.append(enemy.kind)
                self.world.events.append(f"enemy {n} defeated")
                self.world.sounds.append(("effect", "DUST"))
        return hits

    def check_contact(self, hero):
        """Returns True if the explorer was hurt this frame."""
        if self.safe:
            self.safe -= 1
            return False
        for n in reversed(range(MAX_ENEMIES)):
            enemy = self.enemies[n]
            if not enemy.kind or enemy.dust:
                continue
            if far_x(hero.x, enemy.x)[0] >= REACH or \
                    far_y(hero.y, enemy.y)[0] >= REACH:
                continue
            self.world.energy = max(0, self.world.energy - DAMAGE)
            self.safe = SAFE_FRAMES
            self.world.events.append(f"hurt by enemy {n}")
            self.world.sounds.append(("effect", "HURT"))
            if not self.world.energy:
                self.finish(ENDED_LOST)
                self.world.ended = "lost"
                self.world.events.append("GAME OVER")
                self.world.sounds.append(("end", ENDED_LOST))
            return True
        return False

    def finish(self, how):
        """game_ends: the explorer in view, no blade."""
        self.ended = how
        self.safe = self.slash = 0

    def fire_released(self, joy, armed):
        """fire_released of screens.asm: (let go after a press?, the
        new fire_armed)."""
        fire = joy & H.JOY_FIRE
        changed = fire != self.fire_held
        self.fire_held = fire
        if not changed:
            return False, armed
        if fire:
            return False, 1
        return bool(armed), armed

    def restart(self):
        """init_game clears the blow, the damage timer and the end;
        entering the start room brings its enemies. fire_held and
        blade_dir are kept, as on the C64."""
        self.slash = self.safe = 0
        self.ended = 0
        self.spawn()

    def sprites(self, frame, hero):
        """Expected sprites 0-4: hero shown?, blade, three enemies;
        blade and enemies are None or (pointer, colour, VIC X, VIC Y)."""
        blade = None
        if self.blade_out():
            dx, dy = BLADE_VIC[self.blade_dir]
            blade = (BLADE_FRAME + self.blade_dir, BLADE_COLOUR,
                     hero.x + dx, (hero.y + dy) & 255)
        enemies = []
        for enemy in self.enemies:
            if not enemy.kind:
                enemies.append(None)
                continue
            if enemy.dust:
                pointer = DUST_FRAME
            else:
                shift = 2 if enemy.kind == BAT else 3
                pointer = FRAMES[enemy.kind] + ((frame >> shift) & 1)
            colour = FLASH_COLOUR if enemy.flash else COLOURS[enemy.kind]
            enemies.append((pointer, colour, enemy.x + 24,
                            (enemy.y + 50) & 255))
        return not self.safe & 4, blade, enemies

    def state(self):
        return (self.slash, self.blade_dir, self.fire_held, self.safe,
                self.ended, [e.state() for e in self.enemies])

"""Python model of the explorer rules in game/src/hero.asm.

The tests compare the C64 with this model after every frame: position,
facing, walking frame and timer must be identical. `block` is what
stopped the last step (0 nothing, 1 wall, 2 door), like hero_block.
"""

JOY_UP, JOY_DOWN, JOY_LEFT, JOY_RIGHT, JOY_FIRE = 1, 2, 4, 8, 16
DIR_DOWN, DIR_UP, DIR_LEFT, DIR_RIGHT = 0, 1, 2, 3
DIR_NAMES = {0: "down", 1: "up", 2: "left", 3: "right"}

HERO_SPEED, WALK_RATE = 1, 8
BOX_LEFT, BOX_RIGHT, BOX_TOP, BOX_BOTTOM, BOX_MID = 6, 17, 13, 18, 11
HERO_POINTER = 0          # frames at $4000: pointers 0-7


class HeroModel:
    """Same rules as update_hero/animate_hero in game/src/hero.asm."""

    def __init__(self, solid, x, y):
        self.solid = solid
        self.x, self.y = x, y
        self.dir = DIR_DOWN
        self.moving = 0
        self.frame = 0
        self.timer = 0
        self.steps = 0
        self.block = 0

    def is_solid(self, x, y):
        if x < 0 or x >= 320 or y < 0 or y >= 200:
            return 1
        return self.solid[(y // 8) * 40 + x // 8]

    def blocked(self):
        """Value of the first solid cell ahead, as step_blocked."""
        x, y = self.x, self.y
        if self.dir == DIR_LEFT:
            px = x + BOX_LEFT - 1
            return self.is_solid(px, y + BOX_TOP) or self.is_solid(px, y + BOX_BOTTOM)
        if self.dir == DIR_RIGHT:
            px = x + BOX_RIGHT + 1
            return self.is_solid(px, y + BOX_TOP) or self.is_solid(px, y + BOX_BOTTOM)
        py = y + BOX_TOP - 1 if self.dir == DIR_UP else y + BOX_BOTTOM + 1
        return (self.is_solid(x + BOX_LEFT, py) or self.is_solid(x + BOX_MID, py)
                or self.is_solid(x + BOX_RIGHT, py))

    def update(self, joy):
        self.moving = 0
        self.block = 0
        if joy & (JOY_LEFT | JOY_RIGHT):
            self.dir = DIR_LEFT if joy & JOY_LEFT else DIR_RIGHT
        elif joy & (JOY_UP | JOY_DOWN):
            self.dir = DIR_UP if joy & JOY_UP else DIR_DOWN
        else:
            self.animate()
            return
        for _ in range(HERO_SPEED):
            self.block = self.blocked()
            if self.block:
                break
            if self.dir == DIR_LEFT:
                self.x -= 1
            elif self.dir == DIR_RIGHT:
                self.x += 1
            elif self.dir == DIR_UP:
                self.y -= 1
            else:
                self.y += 1
            self.moving = 1
            self.steps += 1
        self.animate()

    def animate(self):
        if self.moving:
            self.timer += 1
            if self.timer == WALK_RATE:
                self.timer = 0
                self.frame ^= 1
        else:
            self.frame = 0
            self.timer = 0

    @property
    def pointer(self):
        return HERO_POINTER + self.dir * 2 + self.frame

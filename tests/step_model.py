"""The program of a step of the chain (steps 01-06) in Python.

The chain of the book (chain/, tools/make_chain.py) builds the game in
eight steps; steps 07 and 08 are the complete program of
tests/game_model.py. Before step 07 there is no title and no end
screen: the program draws the start room at once and a game begins;
after GAME OVER or VICTORY (game_ended) the room stands still - the
main loop no longer calls play_frame - until the program is started
again. What play_frame does grows with the steps:

  01  no play_frame: the room and its torches
  02  update_hero (joystick, walls, walking frames)
  03  + check_exits (sixteen rooms; the HUD printed, still)
  04  + check_door, check_objects, the portal and VICTORY; hud_update
  05  + check_fire, update_enemies, check_blade, check_contact
  06  + the sound: the mode is START_MODE (MUSIC as assembled)

The rules are the ones of hero_model, world_model and combat_model:
StepGame only leaves out what the step has not got yet, in the order
of play_frame in main.asm, so the test and the route planner compare
each step with the same models as the complete game.
"""
import combat_model as C
import game_model as G
import reference
import world_model as W

FLAME_SHIFT = 3        # the torches change every 2^3 frames (main.asm)
FIRST_HERO, FIRST_EXITS, FIRST_OBJECTS = 2, 3, 4
FIRST_COMBAT, FIRST_SOUND, FIRST_TITLE = 5, 6, 7


class StepWorld(W.World):
    """The dungeon of a step: no HUD before 03, no portal before 04."""

    def __init__(self, step, hud_frame, start, over_text=None,
                 won_text=None):
        super().__init__(hud_frame, start, over_text, won_text)
        self.step = step

    def new_game(self):
        super().new_game()
        if self.step < FIRST_EXITS:     # no energy yet: init_game
            self.energy = 0             # sets the room only

    def screen(self, slot=None):
        if self.step >= FIRST_EXITS:
            return super().screen(slot)
        result = reference.Screen()     # clear_screen, draw_room
        result.draw_room(result.room_page(self.slot if slot is None
                                          else slot))
        return result

    def check_exits(self, hero):
        if self.step < FIRST_OBJECTS and hero.y <= W.NORTH_EDGE and \
                self.slot == self.start:
            raise RuntimeError("step 03: north out of the start room, "
                               "through the portal it has not got")
        return super().check_exits(hero)


class StepGame(G.Game):
    """One step of the chain; the same interface as game_model.Game
    (step(joy) returns what happened), state always "play"."""

    def __init__(self, step, hud_frame, start_room, texts, start_x,
                 start_y, frame=0, mode=G.MODE_MUSIC):
        if not 1 <= step < FIRST_TITLE:
            raise ValueError(f"StepGame is for steps 1-6, not {step}")
        self.step_number = step
        self.start_x, self.start_y = start_x, start_y
        self.world = StepWorld(step, hud_frame, start_room, *texts)
        self.world.new_game()
        self.combat = C.Combat(self.world, spawn=False)
        if step >= FIRST_COMBAT:
            self.combat.restart()       # the start room's enemies
        self.hero = self.new_hero() if step >= FIRST_HERO else None
        self.frame = frame
        self.state = "play"
        self.mode = mode                # START_MODE, from step 06
        self.stick_held = self.fire_armed = self.end_timer = 0
        self.prompt = False

    def has(self, first):
        return self.step_number >= first

    def step(self, joy):
        self.frame = (self.frame + 1) & 0xFFFF
        world = self.world
        world.sounds = []
        result = {"room": None, "opened": False, "taken": [],
                  "defeated": [], "hurt": False, "over": False,
                  "won": False, "screen": None, "menu": False,
                  "prompt": False, "sounds": world.sounds}
        if self.has(FIRST_HERO) and not world.ended:
            self.play_frame(joy, result)
        if not self.has(FIRST_SOUND):
            world.sounds.clear()        # no player before step 06
        return result

    def play_frame(self, joy, result):
        world, combat, hero = self.world, self.combat, self.hero
        if self.has(FIRST_COMBAT):
            joy = combat.check_fire(joy, hero)
        hero.update(joy)
        if self.has(FIRST_EXITS):
            room = world.check_exits(hero)
            if room is not None:
                world.sounds.append(("draw",))
                result["room"] = room
                if self.has(FIRST_COMBAT):
                    combat.spawn()
            if world.ended == "won":            # the portal, from 04
                combat.finish(C.ENDED_WON)
                result["won"] = True
        if self.has(FIRST_OBJECTS):
            result["opened"] = world.check_door(hero)
            result["taken"] = world.check_objects(hero)
        if self.has(FIRST_COMBAT):
            combat.update(self.frame, hero)
            result["defeated"] = combat.check_blade(hero)
            result["hurt"] = combat.check_contact(hero)
            result["over"] = combat.ended == C.ENDED_LOST

    def sprites(self):
        """What sprites 0-6 must show after this frame: explorer shown?,
        blade, three enemies, two objects - as combat_model.sprites and
        world_model.sprites, with what the step has not got left out."""
        if not self.has(FIRST_HERO):
            return None
        if self.has(FIRST_COMBAT):
            shown, blade, enemies = self.combat.sprites(self.frame,
                                                        self.hero)
        else:
            shown, blade, enemies = True, None, [None] * C.MAX_ENEMIES
        objects = self.world.sprites() if self.has(FIRST_OBJECTS) \
            else [None, None]
        return shown, blade, enemies, objects


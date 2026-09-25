"""The whole program in Python: the states of screens.asm - the
title with its menu, the game, the end in the room, the end screen -
and in the game the models of the explorer, the dungeon and the combat
(tests/hero_model.py, world_model.py, combat_model.py), stepped in the
order of main_loop in game/src/main.asm.

One call of step() is one pass of main_loop: frame_count goes up
first, then the routine of the state. In the game: check_fire,
update_hero, check_exits (new room: its enemies come back; out through
the portal: VICTORY), check_door, check_objects, update_enemies,
check_blade, check_contact. step() also returns the sounds asked for,
in order, with ("draw",) where a room was drawn (the interrupt plays
meanwhile), for tests/audio_model.py. The test and the route planner
use the same class.
"""
import combat_model as C
import hero_model as H
import world_model as W

MODE_MUSIC, MODE_FX, MODE_SILENT = 0, 1, 2
ENDING_FRAMES, END_DELAY = 50, 100
STATES = ("title", "play", "ending", "end")


class Game:
    def __init__(self, hud_frame, start_room, texts, start_x, start_y,
                 frame=0):
        """texts: the GAME OVER and VICTORY strings of combat.asm.
        The program starts on the title, MUSIC chosen, before any
        game: every game variable 0."""
        self.start_x, self.start_y = start_x, start_y
        self.world = W.World(hud_frame, start_room, *texts)
        self.hero = None                # no explorer before a game
        self.combat = C.Combat(self.world, spawn=False)
        self.frame = frame              # frame_count, 16 bits
        self.state = "title"
        self.mode = MODE_MUSIC          # the menu's line
        self.stick_held = 0             # up/down bits, last frame
        self.fire_armed = 0
        self.end_timer = 0
        self.prompt = True              # PRESS FIRE on the screen

    def new_hero(self):
        """init_hero, in the room the world is in."""
        return H.HeroModel(list(self.world.screen().solid),
                           self.start_x, self.start_y)

    def step(self, joy):
        """One frame. Returns what happened, for the test's checks."""
        self.frame = (self.frame + 1) & 0xFFFF
        world = self.world
        world.sounds = []
        result = {"room": None, "opened": False, "taken": [],
                  "defeated": [], "hurt": False, "over": False,
                  "won": False, "screen": None, "menu": False,
                  "prompt": False, "sounds": world.sounds}
        getattr(self, self.state + "_frame")(joy, result)
        return result

    # --- title -----------------------------------------------------
    def title_frame(self, joy, result):
        bits = joy & (H.JOY_UP | H.JOY_DOWN)
        if bits != self.stick_held:
            self.stick_held = bits
            mode = self.mode
            if bits & H.JOY_UP:
                mode = max(mode - 1, MODE_MUSIC)
            elif bits:
                mode = min(mode + 1, MODE_SILENT)
            if mode != self.mode:
                self.mode = mode
                self.world.sounds.append(("mode", mode))
                result["menu"] = True
                if mode == MODE_FX:
                    self.world.sounds.append(("effect", "PICKUP"))
        released, self.fire_armed = self.combat.fire_released(
            joy, self.fire_armed)
        if released:
            self.start_game(result)

    def start_game(self, result):
        """start_game: a new game in the chosen mode."""
        self.world.sounds.append(("mode", self.mode))
        self.world.sounds.append(("draw",))
        self.world.new_game()
        self.world.events.append("new game")
        self.hero = self.new_hero()
        self.combat.restart()
        self.state = "play"
        result["screen"] = "play"
        result["room"] = self.world.slot

    # --- the game --------------------------------------------------
    def play_frame(self, joy, result):
        world, combat, hero = self.world, self.combat, self.hero
        hero.update(combat.check_fire(joy, hero))
        room = world.check_exits(hero)
        if room is not None:
            world.sounds.append(("draw",))
            result["room"] = room
            combat.spawn()
        if world.ended == "won":                # victory, in check_exits
            combat.finish(C.ENDED_WON)
            result["won"] = True
        result["opened"] = world.check_door(hero)
        result["taken"] = world.check_objects(hero)
        combat.update(self.frame, hero)
        result["defeated"] = combat.check_blade(hero)
        result["hurt"] = combat.check_contact(hero)
        result["over"] = combat.ended == C.ENDED_LOST
        if result["won"] or result["over"]:
            self.state, self.end_timer = "ending", ENDING_FRAMES

    # --- the end ---------------------------------------------------
    def ending_frame(self, joy, result):
        self.end_timer -= 1
        if not self.end_timer:
            self.state, self.end_timer = "end", END_DELAY
            self.fire_armed = 0
            self.prompt = False
            result["screen"] = "end"

    def end_frame(self, joy, result):
        released, self.fire_armed = self.combat.fire_released(
            joy, self.fire_armed)
        if self.end_timer:
            self.fire_armed = 0
            self.end_timer -= 1
            if not self.end_timer:
                self.prompt = True
                result["prompt"] = True
            return
        if released:
            self.state = "title"
            self.fire_armed = 0
            self.stick_held = joy & (H.JOY_UP | H.JOY_DOWN)
            self.world.sounds.append(("mode", self.mode))
            self.world.sounds.append(("draw",))
            result["screen"] = "title"

    # --- what the screen shows -------------------------------------
    def ended(self):
        return self.world.ended             # "lost" or "won"

    def rooms_seen(self):
        return len(self.world.seen)

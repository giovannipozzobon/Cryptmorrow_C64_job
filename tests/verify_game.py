"""Verify Cryptmorrow 1.0.1, the complete game, in a private VICE.

Usage: python tests/verify_game.py [--step 7|8] [--vice PATH]
                                   [--settle SECONDS]

With --step the program is step 07 or 08 of the chain of the book
(chain/NN-name/game/build) and the report and screenshots go to
chain/evidence/NN-name/. Step 08 is this game byte for byte; step 07
has no unpack (section 0 then checks every block at its address in
the PRG and in memory) and is restarted from `entry`.

0. Unpack: the table of the data blocks follows the PRG in order, no
   block lies above its address or runs into the next; every block is
   the generated file (the music: the assembled bytes) and lies at its
   address. The packed part of the PRG is then written back as LOAD
   leaves it and unpack runs again from `entry`, timed.
1. Restarts the program at `start` and times draw_room of the title
   screen with the raster position (VICE registers LIN and CYC) at
   every cell row, the music interrupt running meanwhile.
2. Compares the title screen - its page, the big letters of the logo,
   the menu, PRESS FIRE, the torches, the sprites - with the reference
   renderer (tests/reference.py).
3. Music on the title: for more than one full loop of the theme, stops
   at the start and at the end of every raster interrupt, measures its
   cost and compares the 25 shadow SID registers with the Python model
   of the player (tests/player_model.py).
4. Plays the route, seven games without loading the PRG again: on the
   title the menu through the three audio modes and both of its ends;
   a game won with the sound effects and the joystick only - every
   opening of the sixteen rooms, every enemy defeated at least once,
   the three keys and doors, the three seals, the portal and out:
   VICTORY - its end screen, Fire too early, Fire, the title; a game
   with the music lost with the joystick only (the explorer waits in a
   skeleton's way), its end screen, the title; short games for the
   other ends - GAME OVER with the effects and in silence, joystick
   only, VICTORY with the music (the test gives the three seals) - and
   a sixth game where the test makes a skeleton slow (every skeleton is
   fast since 1.0.1), moves a bat far away, leaves two cells of energy
   before a potion (four), then one: a touch takes two, energy stops at
   0, GAME OVER; a seventh game begun. Every frame the
   C64 must match the Python models: the state of the program, the
   menu and Fire (tests/game_model.py), in the game the explorer, the
   room, the game state, the 35 bytes of combat state and sprites 0-6
   (hero_model, world_model, combat_model), and always the sound:
   audio mode, effect asked for and playing, song, music counters and
   the 25 shadow SID registers (tests/audio_model.py), the interrupts
   of the frame played in the model at the same point of the game's
   requests. No note is left sounding: every frame the shadow
   registers obey the rules of silence of each mode. Screens are
   compared with the reference whenever they are drawn or change;
   every change of room and of screen is timed; so is the game work of
   every other frame, and the sound interrupt in FX mode, in SILENT
   mode and while a piece of the end plays.
5. In the last game injects HUD values and compares the HUD rows.
6. Checks the torch flames and that nothing else in the bitmap changes,
   on every screen; exports eleven native screenshots; adds the memory
   map of tools/memory_map.py to the report.
The route was planned offline with the same models and is written
out below, so the test itself does not search for paths or aim blows:
`python tools/plan_route.py tools/route_1.0.1.py` prints SCRIPT again.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

from audio_model import AudioModel, MODE_FX, MODE_MUSIC, MODE_SILENT
import combat_model as C
import game_model as G
import hero_model as H
from player_model import PlayerModel
import reference
import world_model as W
from vicemon import (DEFAULT_VICE, PAL_FRAME_CYCLES, PROJECT, Vice,
                     load_labels, note, require)

sys.path.insert(0, str(PROJECT / "tools"))
import memory_map                               # noqa: E402

# Cycles the sound interrupt may use in one frame (19 656 on PAL).
# Measured: the music costs more than the first estimate, 1500.
MUSIC_BUDGET = 2500
PAL_CLOCK = 985248        # cycles a second

U, D, L, R, F = H.JOY_UP, H.JOY_DOWN, H.JOY_LEFT, H.JOY_RIGHT, H.JOY_FIRE
ALIGN = 32              # frame phase: enemies repeat in 16, torches in 32
STATES = G.STATES       # game_state 0-3
MODES = ("MUSIC", "FX", "SILENT")

# The title as screens.asm documents it: sprite corners (screen X, Y)
# of the explorer, the skeleton and the bat; the bat's flutter and the
# glow of PRESS FIRE, a step every 4 frames.
TITLE_HERO, TITLE_SKELETON, TITLE_BAT = (148, 98), (70, 98), (226, 74)
BAT_BOB = [0, 1, 2, 3, 3, 2, 1, 0]
PULSE = [c << 4 for c in (11, 12, 15, 1, 1, 15, 12, 11)]
PROMPT_PRINTED = 1 << 4                 # white, as prompt_text
SPRITE_COLOURS = {0: 5, 2: 15, 3: 4}    # tunic, bones, bat
CHANGE = {"start": "play", "ending": "ending", "end": "end",
          "back": "title"}
TEXTS = ("logo_text", "lost_word", "won_word", "menu_music", "menu_fx",
         "menu_silent", "prompt_text", "stats_text")
# Sound interrupts timed during the route, at most, by kind.
PROBES = {"FX": 4000, "SILENT": 500, "MUSIC, end of a game": 400}

# (joystick, frames, expectation, screenshot). In the game: "blocked":
# no step at all; "moves": at least one step; a number: exactly one
# change of room, into that room; "fight": frames chosen by the planner
# to wait, turn and strike (the models decide what happens). Changes of
# state: "start" (from the title a game begins), "ending" (the game
# ends in the room), "end" (the end screen), "back" (the title again);
# "title" and "still": the state does not change. ("energy", n, "set",
# None): the test writes n into energy (and sets hud_dirty); ("seals",
# n, "set", None) the same for seals. ("enemy", n, (x, y), None): the
# test moves enemy n. ("slow", n, "set", None): the test clears the
# fast flag of enemy n (1.0.1: every skeleton of the dungeon is fast,
# so the slow patrol is shown this way). ("align", m, "idle", None):
# the test waits, stick centred, until frame_count mod 32 = m, the phase
# the planner used, so that enemies (they move on even or odd frames),
# their animations, the title's sprites, the glow of PRESS FIRE and the
# torch flames are in step with the plan and the captures repeat.
SCRIPT = [
    ('align', 0, 'idle', None),                     # frames in step with the plan
    (0, 16, 'title', 'cryptmorrow-title.png'),      # the title, MUSIC chosen
    ('align', 17, 'idle', None),
    (D, 4, 'title', None),                          # down: SOUND FX, an effect as a sample
    (0, 20, 'title', None),                         # the stick back to the centre
    (D, 4, 'title', None),                          # down: SILENT
    (0, 4, 'title', None),                          # centre
    (D, 4, 'title', None),                          # down again: still SILENT, the last line
    (0, 4, 'title', None),                          # centre
    (U | D, 4, 'title', None),                      # up and down together: up wins, SOUND FX
    (0, 4, 'title', None),                          # centre
    (U, 4, 'title', None),                          # up: MUSIC
    (0, 4, 'title', None),                          # centre
    (U, 4, 'title', None),                          # up again: still MUSIC, the first line
    (0, 4, 'title', None),                          # centre
    (D, 4, 'title', None),                          # down: SOUND FX
    (D | F, 6, 'title', None),                      # Fire pressed: nothing yet
    (0, 1, 'start', None),                          # Fire let go: a game with the sound effects
    ('align', 28, 'idle', None),
    # idle at the start
    (0, 16, 'blocked', 'cryptmorrow-moss-gate.png'),
    ('align', 13, 'idle', None),
    (U, 60, 'moves', None),                         # north to the gate
    (U, 8, 'blocked', None),                        # the portal: shut without the three seals
    (D | R, 24, 'moves', None),                     # diagonal: horizontal wins
    (U | D, 8, 'moves', None),                      # both vertical bits: up wins
    (F, 30, 'blocked', None),                       # Fire held: one blow only, standing still
    (0, 4, 'blocked', None),                        # released
    (L | F, 16, 'moves', None),                     # Fire while walking: the explorer stops while the blade is out
    (D, 8, 'moves', None),                          # to the south steps
    (L, 22, 'moves', None),
    (D, 99, 'moves', None),
    (D, 12, 5, None),                               # south opening: Crossroads
    (U, 24, 1, None),                               # north opening: Moss Gate
    (D, 24, 5, None),                               # south again: Crossroads
    (D, 16, 'moves', None),                         # onto the skeleton's row
    (R, 52, 'moves', None),
    (D, 70, 'moves', None),
    (L, 85, 'fight', None),                         # skeleton: three blows
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 16, 'moves', None),                         # to the west opening
    (L, 94, 'moves', None),
    (U, 11, 'moves', None),
    (L, 24, 4, None),                               # west opening: Root Cellar
    (L, 29, 'moves', None),                         # onto the potion: full energy, it stays
    (U, 39, 'moves', None),
    (D, 56, 'moves', None),                         # towards the bat
    (L, 18, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (D, 2, 'moves', None),
    (L, 35, 'moves', None),
    (U, 7, 'moves', None),
    (L, 48, 'moves', None),                         # against the locked door
    (D, 49, 'moves', None),
    (D, 8, 'blocked', None),                        # door A without key: stays shut
    (R, 16, 'moves', None),                         # under the north opening
    (U, 119, 'moves', None),
    (U, 24, 0, None),                               # north opening: Bone Pit
    (U, 1, 'fight', None),                          # the bone pit bat
    (0, 1, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 72, 'moves', None),                         # onto the skeleton's row
    (L, 69, 'moves', None),
    (U, 13, 'moves', None),
    (R, 39, 'fight', None),                         # the bone pit skeleton
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 113, 'moves', None),                        # treasure
    (D, 14, 'moves', None),
    (L, 208, 'moves', None),                        # the potion
    (D, 64, 'moves', None),
    (R, 123, 'moves', None),                        # above the south steps
    (D, 11, 'moves', None),
    (D, 24, 4, None),                               # south opening: Root Cellar
    (D, 16, 'moves', None),                         # down towards the bat
    (D, 5, 'fight', None),                          # an enemy in the way
    (L, 1, 'fight', None),
    (D, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 1, 'moves', None),
    (D, 6, 'moves', None),
    (D, 47, 'moves', None),                         # to the east opening
    (R, 72, 'moves', None),
    (U, 8, 'moves', None),
    (R, 44, 'moves', None),
    (U, 11, 'moves', None),
    (R, 16, 5, None),                               # east opening: Crossroads
    (R, 266, 'moves', None),                        # across the Crossroads
    (R, 20, 6, None),                               # east opening: Long Gallery
    (R, 26, 'moves', None),                         # into the corridor
    (U, 4, 'moves', None),
    (R, 164, 'fight', None),                        # the corridor skeleton
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (D, 56, 'moves', None),                         # down to the lower row
    (L, 5, 'moves', None),
    (D, 9, 'moves', None),
    (L, 74, 'fight', None),                         # the second skeleton
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 144, 'moves', None),                        # treasure
    (U, 2, 'moves', None),
    (R, 1, 'moves', None),                          # along the corridor to the east
    (U, 61, 'moves', None),
    (R, 20, 'moves', None),                         # door B without key: stays shut
    (L, 22, 'moves', None),                         # under the north opening
    (U, 54, 'moves', None),
    (U, 20, 2, None),                               # north opening: Old Well
    (L, 11, 'moves', None),                         # treasure
    (U, 93, 'moves', None),
    (L, 10, 'fight', None),                         # towards the bat
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 23, 'moves', None),
    (D, 3, 'moves', None),
    (L, 175, 'moves', None),                        # key A
    (U, 3, 'moves', None),
    (0, 16, 'blocked', 'cryptmorrow-old-well.png'),
    ('align', 12, 'idle', None),
    (R, 95, 'moves', None),                         # against the well
    (D, 20, 'moves', None),
    (D, 8, 'blocked', None),                        # the well
    (R, 124, 'moves', None),                        # above the south steps
    (D, 71, 'moves', None),
    (D, 24, 6, None),                               # south opening: Long Gallery
    (L, 14, 'moves', None),                         # down into the corridor
    (D, 52, 'moves', None),
    (L, 4, 'fight', None),                          # the corridor skeleton is back
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 225, 'moves', None),                        # to the west opening
    (U, 3, 'moves', None),
    (L, 24, 5, None),                               # west opening: Crossroads
    (L, 262, 'moves', None),                        # to the west opening
    (D, 8, 'moves', None),
    (L, 24, 4, None),                               # west opening: Root Cellar
    (L, 16, 'moves', None),                         # towards the bat
    (D, 19, 'moves', None),
    (L, 64, 'moves', None),
    (F, 1, 'fight', None),                          # an enemy in the way
    (0, 8, 'fight', None),
    (L, 2, 'moves', None),
    (U, 7, 'moves', None),
    (L, 48, 'moves', None),                         # against the door
    (D, 49, 'moves', None),
    (D, 1, 'blocked', None),                        # door A opens with key A
    (D, 30, 8, None),                               # through the door: Ossuary
    (R, 4, 'fight', None),                          # the ossuary bat
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 84, 'moves', None),                         # onto the skeleton's row
    (D, 85, 'moves', None),
    (L, 171, 'fight', None),                        # the ossuary skeleton
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (0, 16, 'blocked', 'cryptmorrow-ossuary.png'),
    ('align', 0, 'idle', None),
    (R, 185, 'moves', None),                        # the potion, energy below full
    (U, 2, 'moves', None),
    (L, 181, 'moves', None),                        # above the south opening
    (D, 11, 'moves', None),
    (D, 24, 12, None),                              # south opening: Catacombs
    (L, 10, 'fight', None),                         # the catacomb bat
    (0, 1, 'fight', None),
    (D, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (D, 2, 'fight', None),                          # the upper skeleton
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 2, 'fight', None),
    (D, 1, 'fight', None),
    (R, 2, 'fight', None),
    (D, 6, 'fight', None),
    (R, 108, 'fight', None),
    (D, 2, 'fight', None),
    (R, 14, 'fight', None),
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 63, 'moves', None),                         # key B
    (D, 5, 'moves', None),
    (L, 3, 'moves', None),                          # onto the lower row
    (D, 83, 'moves', None),
    (L, 105, 'fight', None),                        # the lower skeleton
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 99, 'moves', None),                         # treasure
    (U, 2, 'moves', None),
    (R, 245, 'moves', None),                        # to the east opening
    (U, 19, 'moves', None),
    (R, 16, 13, None),                              # east opening: Bone Shrine
    (R, 12, 'fight', None),                         # the first shrine bat
    (0, 1, 'fight', None),
    (U, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 56, 'moves', None),                         # towards the second bat
    (R, 17, 'fight', None),                         # an enemy in the way
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 48, 'moves', None),
    (R, 19, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 27, 'moves', None),
    (U, 38, 'moves', None),
    (L, 44, 'moves', None),                         # below the skeleton, over the seal
    (D, 62, 'moves', None),
    (R, 1, 'moves', None),                          # seal A
    (U, 67, 'moves', None),
    (U, 6, 'moves', None),                          # up to the altar
    (U, 8, 'blocked', None),                        # the altar
    (D, 48, 'moves', None),                         # to the west opening
    (L, 137, 'moves', None),
    (D, 3, 'moves', None),
    (L, 24, 12, None),                              # west opening: Catacombs, enemies back
    (L, 152, 'moves', None),                        # west along the lower rows
    (L, 23, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 15, 'moves', None),
    (L, 52, 'moves', None),                         # up the left side
    (U, 50, 'moves', None),
    (R, 5, 'fight', None),                          # the upper skeleton is back
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 26, 'moves', None),                         # under the north opening
    (U, 29, 'moves', None),
    (U, 24, 8, None),                               # north opening: Ossuary
    (R, 70, 'fight', None),                         # the ossuary skeleton is back
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 34, 'fight', None),
    (U, 5, 'fight', None),
    (R, 11, 'fight', None),
    (U, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 46, 'moves', None),                         # towards the bat
    (U, 73, 'moves', None),
    (U, 40, 'moves', None),                         # under the north opening
    (U, 24, 4, None),                               # north opening, open door: Root Cellar
    (F, 1, 'fight', None),                          # the cellar bat is back
    (0, 8, 'fight', None),
    (R, 86, 'moves', None),                         # to the east opening
    (U, 40, 'moves', None),
    (R, 46, 'moves', None),
    (U, 10, 'moves', None),
    (R, 16, 5, None),                               # east opening: Crossroads
    (R, 266, 'moves', None),                        # across the Crossroads
    (R, 20, 6, None),                               # east opening: Long Gallery
    (R, 26, 'moves', None),                         # into the corridor
    (U, 4, 'moves', None),
    (R, 164, 'fight', None),                        # the corridor skeleton is back
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 65, 'moves', None),                         # along the corridor to the east
    (D, 1, 'moves', None),
    (R, 20, 'moves', None),                         # door B opens with key B
    (R, 30, 7, None),                               # through door B: Flooded Stair
    (D, 8, 'moves', None),                          # towards the bat
    (R, 128, 'moves', None),
    (R, 6, 'fight', None),                          # an enemy in the way
    (D, 9, 'fight', None),
    (0, 5, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (0, 12, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 22, 'moves', None),
    (U, 5, 'moves', None),
    (R, 24, 'moves', None),                         # beside the skeleton's column
    (R, 39, 'moves', None),                         # the potion
    (U, 47, 'moves', None),
    (L, 105, 'moves', None),                        # under the north opening
    (U, 19, 'moves', None),
    (U, 24, 3, None),                               # north opening: Black Cistern
    (R, 32, 'moves', None),                         # towards the right bat
    (R, 10, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 10, 'moves', None),
    (L, 40, 'moves', None),                         # towards the left bat
    (L, 17, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 43, 'moves', None),
    (L, 60, 'moves', None),                         # up the left side
    (U, 72, 'moves', None),
    (U, 2, 'fight', None),                          # an enemy in the way
    (0, 3, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 1, 'moves', None),
    (U, 12, 'moves', None),
    (D, 71, 'moves', None),                         # key C
    (R, 101, 'moves', None),
    (U, 26, 'moves', None),
    (D, 32, 'moves', None),                         # the potion
    (R, 112, 'moves', None),
    (L, 105, 'moves', None),                        # above the south steps
    (D, 11, 'moves', None),
    (D, 24, 7, None),                               # south opening: Flooded Stair
    (D, 11, 'moves', None),                         # round the water to the south steps
    (L, 40, 'moves', None),
    (D, 48, 'moves', None),
    (R, 16, 'moves', None),
    (R, 22, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 24, 'moves', None),
    (D, 48, 'moves', None),
    (L, 22, 'moves', None),
    (D, 1, 'moves', None),
    (D, 24, 11, None),                              # south opening: Drowned Shrine
    (D, 16, 'moves', None),                         # towards the bat on the left
    (L, 28, 'moves', None),
    (D, 4, 'moves', None),
    (L, 1, 'fight', None),                          # the shrine bat on the left
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (D, 24, 'moves', None),                         # towards the bat on the right
    (R, 8, 'moves', None),
    (R, 17, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 32, 'moves', None),
    (D, 12, 'moves', None),
    (L, 46, 'moves', None),                         # above the skeleton's row
    (D, 22, 'moves', None),
    (L, 2, 'fight', None),                          # the fast skeleton of the shrine
    (D, 5, 'fight', None),
    (L, 1, 'fight', None),
    (D, 7, 'fight', None),
    (L, 3, 'fight', None),
    (D, 1, 'fight', None),
    (0, 3, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 48, 'moves', None),                         # treasure
    (U, 8, 'moves', None),
    (L, 30, 'moves', None),
    (U, 18, 'moves', None),
    (R, 32, 'moves', None),                         # seal B
    (U, 16, 'moves', None),
    (R, 80, 'moves', None),
    (0, 16, 'blocked', 'cryptmorrow-drowned-shrine.png'),
    ('align', 19, 'idle', None),
    (L, 31, 'moves', None),                         # under the north opening
    (U, 28, 'moves', None),
    (R, 22, 'moves', None),
    (U, 23, 'moves', None),
    (U, 24, 7, None),                               # north opening: Flooded Stair
    (L, 72, 'moves', None),                         # round the water to the west opening
    (U, 40, 'moves', None),
    (L, 56, 'moves', None),
    (U, 11, 'moves', None),
    (L, 24, 6, None),                               # west opening, open door B: Long Gallery
    (L, 54, 'fight', None),                         # the corridor skeleton is back
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 207, 'moves', None),                        # along the corridor to the west
    (D, 1, 'moves', None),
    (L, 24, 5, None),                               # west opening: Crossroads
    (L, 52, 'moves', None),                         # above the skeleton's row
    (D, 12, 'moves', None),
    (L, 144, 'fight', None),                        # the crossroads skeleton is back
    (D, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 62, 'moves', None),                         # to the south steps
    (D, 49, 'moves', None),
    (D, 12, 9, None),                               # south opening: Sunken Hall
    (D, 13, 'moves', None),                         # towards the bat
    (L, 32, 'moves', None),
    (D, 7, 'fight', None),                          # an enemy in the way
    (L, 11, 'fight', None),
    (D, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 5, 'moves', None),
    (D, 49, 'moves', None),
    (D, 7, 'moves', None),                          # above the skeleton's row
    (R, 50, 'moves', None),
    (U, 7, 'moves', None),
    (D, 1, 'fight', None),                          # the sunken hall skeleton
    (U, 7, 'fight', None),
    (R, 2, 'fight', None),
    (U, 2, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 12, 'moves', None),                         # treasure
    (D, 36, 'moves', None),
    (U, 12, 'moves', None),                         # to the east door
    (R, 129, 'moves', None),
    (U, 17, 'moves', None),
    (R, 20, 'moves', None),                         # door C opens with key C
    (R, 30, 10, None),                              # through door C: Amber Hall
    (R, 27, 'moves', None),                         # above the lower skeleton's row
    (D, 16, 'moves', None),
    (R, 58, 'fight', None),                         # the lower fast skeleton
    (D, 7, 'fight', None),
    (R, 13, 'fight', None),
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 2, 'moves', None),                          # below the upper skeleton's row
    (U, 38, 'moves', None),
    (U, 4, 'fight', None),                          # the upper fast skeleton
    (0, 2, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 1, 'fight', None),                          # towards the bat
    (0, 11, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 51, 'moves', None),
    (D, 37, 'moves', None),
    (L, 32, 'moves', None),                         # above the south steps
    (D, 24, 'moves', None),
    (D, 24, 14, None),                              # south opening: Treasury
    (D, 20, 'moves', None),                         # above the upper skeleton's row
    (D, 6, 'fight', None),                          # the upper fast skeleton of the treasury
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 6, 'fight', None),
    (0, 6, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 12, 'fight', None),                         # down the left side
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 5, 'moves', None),
    (L, 103, 'moves', None),
    (D, 47, 'moves', None),
    (D, 8, 'moves', None),                          # above the lower skeleton's row
    (R, 60, 'moves', None),
    (D, 8, 'moves', None),
    (F, 1, 'fight', None),                          # the lower fast skeleton of the treasury
    (0, 8, 'fight', None),
    (L, 7, 'fight', None),
    (D, 1, 'fight', None),
    (0, 4, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 48, 'moves', None),                         # treasure
    (U, 68, 'moves', None),
    (R, 208, 'moves', None),                        # treasure
    (0, 16, 'blocked', 'cryptmorrow-treasury.png'),
    ('align', 19, 'idle', None),
    (D, 64, 'moves', None),                         # to the east opening
    (R, 37, 'moves', None),
    (D, 3, 'moves', None),
    (R, 16, 15, None),                              # east opening: Sun Vault
    (D, 7, 'moves', None),                          # towards the lower bat
    (R, 72, 'moves', None),
    (R, 17, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 21, 'moves', None),
    (U, 7, 'moves', None),
    (U, 16, 'moves', None),                         # towards the upper bat
    (L, 1, 'fight', None),                          # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 16, 'moves', None),
    (L, 69, 'moves', None),
    (U, 4, 'moves', None),
    (R, 152, 'moves', None),                        # beside the skeleton's column
    (D, 4, 'moves', None),
    (R, 1, 'fight', None),                          # the fast skeleton of the vault, up and down
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 9, 'fight', None),
    (D, 1, 'fight', None),
    (0, 2, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 97, 'moves', None),                         # seal C
    (U, 4, 'moves', None),
    (L, 48, 'moves', None),                         # to the west opening
    (D, 32, 'moves', None),
    (L, 57, 'moves', None),
    (D, 3, 'moves', None),
    (L, 24, 14, None),                              # west opening: Treasury, enemies back
    (L, 134, 'moves', None),                        # into the middle passage
    (U, 26, 'moves', None),
    (F, 1, 'fight', None),                          # the upper skeleton is back
    (0, 8, 'fight', None),
    (U, 1, 'fight', None),
    (R, 1, 'fight', None),
    (U, 1, 'fight', None),
    (0, 9, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 1, 'moves', None),                          # under the north opening
    (U, 56, 'moves', None),
    (D, 1, 'fight', None),                          # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 3, 'moves', None),
    (U, 24, 10, None),                              # north opening: Amber Hall
    (F, 1, 'fight', None),                          # the lower skeleton is back at once
    (0, 8, 'fight', None),
    (L, 4, 'fight', None),
    (0, 5, 'fight', None),
    (L, 2, 'fight', None),
    (0, 2, 'fight', None),
    (L, 1, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 24, 'moves', None),                         # to the west opening
    (L, 122, 'moves', None),
    (U, 4, 'moves', None),
    (L, 24, 9, None),                               # west opening, open door C: Sunken Hall
    (L, 7, 'fight', None),                          # under the north opening
    (D, 1, 'fight', None),
    (L, 14, 'fight', None),
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 112, 'moves', None),
    (U, 80, 'moves', None),
    (U, 24, 5, None),                               # north opening: Crossroads
    (F, 1, 'fight', None),                          # the crossroads skeleton is back
    (0, 8, 'fight', None),
    (R, 1, 'fight', None),
    (U, 2, 'fight', None),
    (R, 36, 'fight', None),
    (U, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 7, 'fight', None),
    (R, 1, 'fight', None),
    (0, 4, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 38, 'moves', None),                         # under the north opening
    (U, 98, 'moves', None),
    (U, 24, 1, None),                               # north opening: Moss Gate
    (U, 87, 'moves', None),                         # before the gate
    (U, 1, 'blocked', None),                        # the portal opens with the three seals
    (0, 16, 'blocked', 'cryptmorrow-portal.png'),   # the open portal
    ('align', 15, 'idle', None),
    (U, 33, 'ending', None),                        # north through the portal: VICTORY
    (U, 16, 'still', 'cryptmorrow-victory.png'),    # the game stands still
    (0, 4, 'still', None),                          # released
    (F, 2, 'still', None),                          # Fire in the room: nothing
    (0, 2, 'still', None),                          # released
    (0, 25, 'end', None),                           # a second later: the end screen
    (F, 4, 'still', None),                          # Fire at once: too early
    (0, 4, 'still', None),                          # released: nothing
    (0, 92, 'still', None),                         # two seconds: PRESS FIRE appears
    ('align', 6, 'idle', None),
    # the end screen of the won game
    (0, 16, 'still', 'cryptmorrow-victory-screen.png'),
    (F, 4, 'still', None),                          # Fire pressed
    (0, 1, 'back', None),                           # Fire let go: the title again
    ('align', 28, 'idle', None),
    (0, 9, 'title', None),                          # SOUND FX still chosen
    (U, 4, 'title', None),                          # up: MUSIC
    (0, 4, 'title', None),                          # centre
    (F, 2, 'title', None),                          # Fire pressed
    (0, 1, 'start', None),                          # Fire let go: a game with the music
    ('align', 16, 'idle', None),
    (D, 39, 'moves', None),                         # a new game: to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (D, 86, 'moves', None),                         # into the skeleton's way
    (R, 52, 'moves', None),
    (0, 204, 'blocked', None),                      # the skeleton hurts: the explorer blinks
    (0, 45, 'blocked', None),                       # it passes again and again: two cells of energy left
    (U, 1, 'moves', None),                          # facing up, away from the skeleton's row
    (F, 260, 'ending', None),                       # Fire held: one blow, then GAME OVER
    (F, 16, 'still', 'cryptmorrow-game-over.png'),  # Fire still held: the game stands still
    (F, 33, 'end', None),                           # Fire held into the end screen
    (0, 4, 'still', None),                          # released during the delay: nothing
    (0, 96, 'still', None),                         # PRESS FIRE appears
    ('align', 1, 'idle', None),
    # the end screen of the lost game
    (0, 16, 'still', 'cryptmorrow-game-over-screen.png'),
    (0, 50, 'still', None),                         # the piece of GAME OVER is over: every note released
    (D | F, 4, 'still', None),                      # Fire pressed, the stick down
    (D, 1, 'back', None),                           # Fire let go, the stick still down: the title
    (D, 8, 'title', None),                          # the stick held down: the cursor stays on MUSIC
    (0, 4, 'title', None),                          # centre
    (D, 4, 'title', None),                          # down: SOUND FX
    (0, 4, 'title', None),                          # centre
    (F, 2, 'title', None),                          # Fire pressed
    (0, 1, 'start', None),                          # Fire let go: a game with the sound effects
    ('align', 0, 'idle', None),
    (D, 39, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (D, 80, 'moves', None),                         # onto the skeleton's way
    (0, 210, 'blocked', None),                      # the skeleton passes again and again
    (0, 298, 'ending', None),                       # until the energy is gone: GAME OVER, its effect
    (0, 50, 'end', None),                           # the end screen
    (0, 100, 'still', None),                        # PRESS FIRE appears
    (F, 2, 'still', None),                          # Fire pressed
    (0, 1, 'back', None),                           # Fire let go: the title
    (U, 4, 'title', None),                          # up: MUSIC
    (0, 4, 'title', None),                          # centre
    (F, 2, 'title', None),                          # Fire pressed
    (0, 1, 'start', None),                          # Fire let go: a game with the music
    ('align', 3, 'idle', None),
    ('seals', 3, 'set', None),                      # the test gives the three seals
    (U, 60, 'moves', None),                         # north to the gate
    (U, 1, 'blocked', None),                        # the portal opens
    (U, 33, 'ending', None),                        # out through the portal: VICTORY, its music
    (0, 50, 'end', None),                           # the end screen
    (0, 100, 'still', None),                        # PRESS FIRE appears
    (0, 60, 'still', None),                         # the piece of VICTORY is over: every note released
    (F, 2, 'still', None),                          # Fire pressed
    (0, 1, 'back', None),                           # Fire let go: the title
    (D, 4, 'title', None),                          # down: SOUND FX
    (0, 4, 'title', None),                          # centre
    (D, 4, 'title', None),                          # down: SILENT
    (0, 4, 'title', None),                          # centre
    (F, 2, 'title', None),                          # Fire pressed
    (0, 1, 'start', None),                          # Fire let go: a silent game
    ('align', 9, 'idle', None),
    (D, 39, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (D, 80, 'moves', None),                         # onto the skeleton's way
    (0, 210, 'blocked', None),                      # the skeleton passes again and again
    (0, 298, 'ending', None),                       # until the energy is gone: a silent GAME OVER
    (0, 50, 'end', None),                           # the end screen
    (0, 100, 'still', None),                        # PRESS FIRE appears
    (F, 2, 'still', None),                          # Fire pressed
    (0, 1, 'back', None),                           # Fire let go: the title
    (F, 2, 'title', None),                          # Fire pressed
    (0, 1, 'start', None),                          # Fire let go: another silent game
    ('align', 4, 'idle', None),
    (D, 39, 'moves', None),                         # a sixth game goes on as before
    (D, 12, 5, None),                               # south opening: Crossroads
    ('slow', 0, 'set', None),                       # the test makes the skeleton slow
    (0, 48, 'blocked', None),                       # a slow patrol: one pixel every other frame
    (D, 48, 'moves', None),                         # to the west opening
    (L, 128, 'moves', None),
    (D, 10, 'moves', None),
    (L, 24, 4, None),                               # west opening: Root Cellar
    ('enemy', 0, (20, 110), None),                  # the test moves the bat far to the west
    (0, 24, 'blocked', None),                       # a bat 262 pixels away stays asleep
    ('energy', 2, 'set', None),                     # the test leaves two cells of energy
    (L, 29, 'moves', None),                         # the potion: two cells more, four
    (U, 39, 'moves', None),
    (D, 58, 'moves', None),                         # west, below the pillars
    (L, 103, 'moves', None),
    (D, 13, 'moves', None),
    ('energy', 1, 'set', None),                     # the test leaves one cell of energy
    (L, 83, 'ending', None),                        # west: the bat wakes and touches, two cells taken from one: energy 0, GAME OVER
    (0, 50, 'end', None),                           # the end screen
    (0, 100, 'still', None),                        # PRESS FIRE appears
    (F, 2, 'still', None),                          # Fire pressed
    (0, 1, 'back', None),                           # Fire let go: the title
    (F, 2, 'title', None),                          # Fire pressed
    (0, 1, 'start', None),                          # Fire let go: a seventh game
    ('align', 18, 'idle', None),
    (D, 39, 'moves', None),                         # a seventh game goes on as before
    (D, 12, 5, None),                               # south opening: Crossroads
    (0, 12, 'blocked', None),                       # rest
]
SIDES = {-4: "north", 4: "south", -1: "west", 1: "east"}
HUD_TEST = (3, 2, 1, 12345)          # energy, keys, seals, score


def bcd(number):
    """Six decimal digits as three BCD bytes, highest first."""
    text = f"{number:06d}"
    return bytes(int(text[i]) << 4 | int(text[i + 1]) for i in (0, 2, 4))


REQUIRED = (
    "audio_irq", "irq_done", "audio_mode", "irq_frames", "sid_shadow",
    "music_frames", "MUSIC_SPEED", "MUSIC_DATA", "entry", "start",
    "unpack", "copy_back", "whole_pages", "blocks", "BLOCK_COUNT",
    "packed_data", "packed_end", "SPRITE_DATA", "TILE_BITMAP",
    "TILE_ATTR", "FONT", "draw_room",
    "next_cell_row", "title_drawn", "draw_screen", "screen_shown",
    "main_loop", "joy_ready", "frame_count", "torch_phase", "torch_count",
    "torch_lo", "torch_hi", "hud_frame", "hud_update", "hud_ready",
    "hud_dirty", "energy", "key_set", "seals", "score", "rooms_seen",
    "room_slot", "room_blank", "room_drawn", "room_shown", "START_ROOM",
    "ROOM_DATA", "SOLID_MAP", "FLAMES", "HERO_START_X", "HERO_START_Y",
    "NORTH_EDGE", "SOUTH_EDGE", "WEST_EDGE", "EAST_EDGE", "doors_open",
    "taken", "check_door", "OBJECT_SPRITES", "COMBAT_SPRITES",
    "slash_timer", "enemy_slot", "game_ended", "over_text", "won_text",
    "check_fire", "en_x_lo", "en_x_hi", "en_y", "en_fast", "colour_zone",
    "set_zone", "DOOR_TILES", "ZONE_COLOURS", "game_state", "end_timer",
    "fire_armed", "stick_held", "TITLE_PAGE", "BIG_FONT", "BIG_STYLES",
    "song_order_lo", "fx_first", "fx_priority", "SONG_THEME", "FX_SLASH",
    "FX_WON", "SONG_WON", "SONG_LOST") + TEXTS


UNPACK = ("start", "unpack", "copy_back", "whole_pages", "blocks",
          "BLOCK_COUNT", "packed_data", "packed_end")


def verify(args):
    root, evidence_rel = PROJECT, "evidence"
    if args.step:
        found = sorted((PROJECT / "chain").glob(f"{args.step:02d}-*"))
        require(args.step in (7, 8) and len(found) == 1,
                "--step: 7 or 8, generated in chain/")
        root, evidence_rel = found[0], f"chain/evidence/{found[0].name}"
    if args.root:                       # a variant of step 07 or 08
        root = args.root.resolve()
    if args.evidence:
        evidence_rel = args.evidence
    reference.GENERATED = root / "game/assets/generated"   # its own
    memory_map.GENERATED = reference.GENERATED
    for statement in args.set:          # a variant changes the model
        exec(statement, {"game_model": G, "hero_model": H,
                         "world_model": W, "combat_model": C,
                         "reference": reference})
    script = SCRIPT
    if args.script:                     # a variant's route
        spec = importlib.util.spec_from_file_location("route", args.script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        script = module.SCRIPT
    prg = root / "game/build/cryptmorrow.prg"
    labels = load_labels(root / "game/build/cryptmorrow.lbl")
    packed = "unpack" in labels
    for name in REQUIRED:
        require(name in labels or (not packed and name in UNPACK),
                f"Required label missing: {name}")
    evidence = PROJECT / evidence_rel
    evidence.mkdir(parents=True, exist_ok=True)
    report = {"result": "FAIL",
              "scope": "The complete game (1.0.1, harder): the PRG unpacked, "
                       "the title with its menu of "
                       "audio modes and PRESS FIRE, the whole dungeon "
                       "(sixteen rooms in four zones, objects, doors, the "
                       "portal, explorer, sword, skeletons and bats, "
                       "damage, HUD), the end of a game in the room and "
                       "on its end screen with score, seals and rooms, "
                       "the way back to the title; the music, its pieces "
                       "for the end of a game, the sound effects and "
                       "silence, no note left sounding; won and lost "
                       "games with the joystick only, seven games without "
                       "loading again; the memory map",
              "prg_sha256": hashlib.sha256(prg.read_bytes()).hexdigest(),
              "screenshots": [], "segments": [], "transitions": [],
              "screens": [], "events": []}
    geometry = {name: labels[name] for name in
                ("NORTH_EDGE", "SOUTH_EDGE", "WEST_EDGE", "EAST_EDGE")}
    wanted = {"NORTH_EDGE": W.NORTH_EDGE, "SOUTH_EDGE": W.SOUTH_EDGE,
              "WEST_EDGE": W.WEST_EDGE, "EAST_EDGE": W.EAST_EDGE}
    require(geometry == wanted,
            f"Exit thresholds {geometry} differ from the model {wanted}")
    report["exit_thresholds"] = geometry
    vice = Vice(args.vice, prg, root / "game/build/game-test-vice.log",
                evidence_rel)
    try:
        monitor = vice.connect(args.settle)
        note("monitor connected")

        def word(address):
            return struct.unpack("<H", monitor.memory(address, 2))[0]

        # --- 0. unpack: the data blocks at their addresses ---------
        if packed:
            image = prg.read_bytes()
            load = image[0] | image[1] << 8
            body = image[2:]
            count = labels["BLOCK_COUNT"]
            table = monitor.memory(labels["blocks"], count * 6)
            blocks = [struct.unpack("<HHH", table[i:i + 6])
                      for i in range(0, count * 6, 6)]
            require(blocks[0][0] == labels["packed_data"] and
                    blocks[-1][0] + blocks[-1][2] == labels["packed_end"]
                    == load + len(body),
                    "The blocks do not fill the PRG from packed_data to "
                    "its end")
            for (source, address, length), (after, next_address, _) in zip(
                    blocks, blocks[1:] + [(None, 0x10000, 0)]):
                require(source <= address, f"Block {address:#06x} lies "
                        f"above its address in the PRG")
                require(after is None or source + length == after,
                        f"Block {address:#06x} not followed by the next")
                require(address + length <= next_address,
                        f"Block {address:#06x} runs into the next")
            files = {labels[name]: name_file for name, name_file in (
                ("SPRITE_DATA", "hero.sprites"),
                ("OBJECT_SPRITES", "objects.sprites"),
                ("COMBAT_SPRITES", "combat.sprites"),
                ("BIG_FONT", "big.font"), ("BIG_STYLES", "big.styles"),
                ("TILE_BITMAP", "tiles.bitmap"), ("TILE_ATTR", "tiles.attr"),
                ("FLAMES", "flames.bin"), ("FONT", "font.bin"),
                ("DOOR_TILES", "doors.bin"), ("TITLE_PAGE", "screens.bin"),
                ("ROOM_DATA", "rooms.bin"), ("ZONE_COLOURS", "zones.color"))}
            require(len(files) == count - 1 and
                    blocks[-1][1] == labels["MUSIC_DATA"],
                    "The table does not list the generated files and the music")

            def check_blocks(when):
                for source, address, length in blocks:
                    data = body[source - load:source - load + length]
                    if address in files:
                        require(data == reference.load(files[address]),
                                f"The PRG block for {address:#06x} is not "
                                f"{files[address]}")
                    require(monitor.memory(address, length) == data,
                            f"{when}: block {address:#06x} not in place")

            check_blocks("After the start")
            # Unpack again, timed: the packed part of the PRG written back
            # as LOAD leaves it, then the program from entry. Every stop
            # (a block, a page) is less than a frame from the last one.
            monitor.poke(labels["packed_data"],
                         body[labels["packed_data"] - load:])
            points = [monitor.checkpoint(labels[name]) for name in
                      ("copy_back", "whole_pages", "start")]
            monitor.set_pc(labels["entry"])
            previous, unpack_cycles, stops = monitor.raster_time(), 0, 0
            while True:
                stop = monitor.run_until_stop()
                now = monitor.raster_time()
                unpack_cycles += (now - previous) % PAL_FRAME_CYCLES
                previous = now
                stops += 1
                if stop == labels["start"]:
                    break
            for number in points:
                monitor.delete_checkpoint(number)
            check_blocks("After unpack")
            packed = labels["packed_end"] - labels["packed_data"]
            report["unpack"] = {
                "prg_bytes": len(image),
                "prg_load": f"${load:04x}-${load + len(body) - 1:04x}",
                "blocks": count, "block_bytes": packed,
                "unpacked_end": f"${blocks[-1][1] + blocks[-1][2] - 1:04x}",
                "prg_bytes_with_holes": 2 + blocks[-1][1] + blocks[-1][2]
                - load,
                "cycles": unpack_cycles,
                "seconds": round(unpack_cycles / PAL_CLOCK, 3),
                "stops": stops,
                "checks": "table in PRG order, no block above its address, "
                          "no block into the next; every block equal to its "
                          "generated file (the music to the assembled PRG "
                          "bytes) at its address, after the start and after "
                          "a timed second unpack from the PRG image"}
            note(f"unpack: {count} blocks, {packed} bytes, {unpack_cycles} "
                 f"cycles")
        else:                           # step 07: no unpack
            image = prg.read_bytes()
            load = image[0] | image[1] << 8
            body = image[2:]
            placed = []
            for name, name_file in (
                    ("SPRITE_DATA", "hero.sprites"),
                    ("OBJECT_SPRITES", "objects.sprites"),
                    ("COMBAT_SPRITES", "combat.sprites"),
                    ("BIG_FONT", "big.font"), ("BIG_STYLES", "big.styles"),
                    ("TILE_BITMAP", "tiles.bitmap"),
                    ("TILE_ATTR", "tiles.attr"), ("FLAMES", "flames.bin"),
                    ("FONT", "font.bin"), ("DOOR_TILES", "doors.bin"),
                    ("TITLE_PAGE", "screens.bin"),
                    ("ROOM_DATA", "rooms.bin"),
                    ("ZONE_COLOURS", "zones.color")):
                address, data = labels[name], reference.load(name_file)
                require(body[address - load:address - load + len(data)]
                        == data and monitor.memory(address, len(data)) ==
                        data, f"{name_file} not at {name}")
                placed.append(name_file)
            music = body[labels["MUSIC_DATA"] - load:]
            require(monitor.memory(labels["MUSIC_DATA"], len(music)) ==
                    music, "The music data not as assembled")
            require(labels["code_end"] <= labels["SPRITE_DATA"],
                    "The code runs into the data")
            report["unpack"] = {
                "prg_bytes": len(image),
                "prg_load": f"${load:04x}-${load + len(body) - 1:04x}",
                "no_unpack": "step 07: every block assembled at its "
                             "address, so the PRG has holes",
                "blocks_checked": placed + ["music"],
                "checks": "every block equal to its generated file (the "
                          "music to the assembled bytes) in the PRG and "
                          "in memory at its address"}
            note(f"no unpack: {len(placed) + 1} blocks at their "
                 f"addresses")

        # --- 1. time draw_room of the title ------------------------
        points = [monitor.checkpoint(labels[name]) for name in
                  ("draw_room", "next_cell_row", "title_drawn")]
        monitor.set_pc(labels["start"] if packed    # unpack ran once
                       else labels["entry"])
        monitor.run_to(labels["draw_room"])
        require(monitor.read_registers()["01"] & 7 == 6,
                "$01 must be $36: RAM visible at $a000")
        require(monitor.memory(0xD011, 1)[0] & 0x10 == 0,
                "Display not blanked before drawing the title")
        irq_start = word(labels["irq_frames"])
        previous = monitor.raster_time()
        intervals = []
        while True:
            stop = monitor.run_until_stop()
            now = monitor.raster_time()
            intervals.append((now - previous) % PAL_FRAME_CYCLES)
            previous = now
            if stop == labels["title_drawn"]:
                break
            require(stop == labels["next_cell_row"],
                    f"Unexpected stop at {stop:#06x}")
        require(len(intervals) == 21, f"{len(intervals)} intervals, not 21")
        cycles = sum(intervals)
        played = (word(labels["irq_frames"]) - irq_start) & 0xFFFF
        require(played >= int(cycles / PAL_FRAME_CYCLES),
                f"Sound interrupt stopped during draw_room: {played}")
        report["title_draw_room"] = {
            "cycles": cycles, "pal_frames": round(cycles /
                                                  PAL_FRAME_CYCLES, 2),
            "longest_cell_row_cycles": max(intervals[:-1]),
            "interrupts_meanwhile": played,
            "method": "raster position (LIN*63+CYC) at every cell row of "
                      "the title page; each interval shorter than a "
                      "frame; includes the sound interrupt"}
        note(f"title draw_room: {cycles} cycles")
        for number in points:
            monitor.delete_checkpoint(number)

        # --- 2. the title against the reference -------------------
        main_point = monitor.checkpoint(labels["main_loop"])
        monitor.run_to(labels["main_loop"])
        texts = {name: monitor.memory(labels[name], 96) for name in TEXTS}
        hud_frame = monitor.memory(labels["hud_frame"], 256)
        start_room = labels["START_ROOM"]
        flames = reference.load("flames.bin")

        def pulse(frame):
            return PULSE[(frame >> 2) & 7]

        def compare(wanted, what, torches=True):
            """The whole screen against a reference: bitmap (flame
            cells hold the flame of torch_phase), screen RAM, Color
            RAM, walkability map, torch list."""
            count = monitor.memory(labels["torch_count"], 1)[0]
            low = monitor.memory(labels["torch_lo"], 6)
            high = monitor.memory(labels["torch_hi"], 6)
            listed = [low[i] | high[i] << 8 for i in range(count)]
            require(listed == wanted.torches,
                    f"{what}: torch list {listed} != {wanted.torches}")
            offsets = {a - 0x6000 + i for a in listed for i in range(8)}
            bitmap = monitor.memory(0x6000, 8000)
            for i in range(8000):
                if i not in offsets and bitmap[i] != wanted.bitmap[i]:
                    raise RuntimeError(f"{what}: bitmap differs from the "
                                       f"reference at cell {i // 8}")
            if torches:
                phase = monitor.memory(labels["torch_phase"], 1)[0]
                for address in listed:
                    require(monitor.memory(address, 8) ==
                            flames[phase * 8:phase * 8 + 8],
                            f"{what}: flame at {address:#06x}")
            for name, address, size, table in (
                    ("screen RAM", 0x4400, 1000, wanted.screen),
                    ("walkability map", labels["SOLID_MAP"], 1000,
                     wanted.solid)):
                actual = monitor.memory(address, size)
                if actual != bytes(table):
                    first = next(i for i in range(size)
                                 if actual[i] != table[i])
                    raise RuntimeError(f"{what}: {name} differs at "
                                       f"{first}")
            colour = bytes(b & 15 for b in monitor.memory(0xD800, 1000))
            if colour != bytes(wanted.color):
                first = next(i for i in range(1000)
                             if colour[i] != wanted.color[i])
                raise RuntimeError(f"{what}: Color RAM differs at {first}")

        def title_reference(mode, frame):
            wanted = reference.expected_title(texts, mode)
            wanted.prompt_colour(pulse(frame))
            return wanted

        def check_title_sprites(frame):
            vic = monitor.memory(0xD000, 0x2F)
            pointers = monitor.memory(0x47F8, 8)
            skeleton = C.FRAMES[C.SKELETON] + ((frame >> 3) & 1)
            bat = C.FRAMES[C.BAT] + ((frame >> 2) & 1)
            wanted = {
                0: (H.HERO_POINTER, TITLE_HERO[0] + 24,
                    TITLE_HERO[1] + 50),
                2: (skeleton, TITLE_SKELETON[0] + 24,
                    TITLE_SKELETON[1] + 50),
                3: (bat, TITLE_BAT[0] + 24,
                    TITLE_BAT[1] + 50 + BAT_BOB[(frame >> 2) & 7])}
            require(vic[0x15] == 0b1101 and vic[0x1C] == 0b1101 and
                    vic[0x10] == 0, f"Frame {frame}: title sprites "
                    f"on {vic[0x15]:08b}, multicolour {vic[0x1C]:08b}, "
                    f"ninth bits {vic[0x10]:08b}")
            for sprite, (pointer, x, y) in wanted.items():
                actual = (pointers[sprite], vic[2 * sprite],
                          vic[2 * sprite + 1], vic[0x27 + sprite] & 15)
                require(actual == (pointer, x, y, SPRITE_COLOURS[sprite]),
                        f"Frame {frame}: title sprite {sprite} {actual}")

        def check_prompt(colour, frame):
            start = 0x4400 + reference.PROMPT_ROW * 40 + \
                reference.PROMPT_COLUMN
            cells = monitor.memory(start, reference.PROMPT_LENGTH)
            require(cells == bytes([colour]) * reference.PROMPT_LENGTH,
                    f"Frame {frame}: PRESS FIRE colours {cells.hex()}, "
                    f"not {colour:02x}")

        first_frame = word(labels["frame_count"])
        compare(title_reference(MODE_MUSIC, first_frame), "Title")
        check_title_sprites(first_frame)
        require(monitor.memory(labels["game_state"], 1)[0] == 0 and
                monitor.memory(labels["audio_mode"], 1)[0] == MODE_MUSIC,
                "The program does not start on the title with MUSIC")
        report["title"] = {
            "reference_match": ["bitmap", "screen RAM", "Color RAM",
                                "walkability map", "torch list",
                                "sprites 0, 2, 3"],
            "big_letters": texts["logo_text"][3:14].hex()}
        monitor.delete_checkpoint(main_point)

        # --- 3. music on the title: model and cost -----------------
        memory = bytearray(65536)
        memory[0x0801:0x4000] = monitor.memory(0x0801, 0x4000 - 0x0801)
        memory[0xC000:0xD000] = monitor.memory(0xC000, 0x1000)
        model = PlayerModel(memory, labels)
        speed = labels["MUSIC_SPEED"]
        songs = json.loads((reference.GENERATED / "assets.json")
                           .read_text())["music"]
        loop_frames = songs["loop_frames"]
        irq_points = [monitor.checkpoint(labels["audio_irq"]),
                      monitor.checkpoint(labels["irq_done"])]
        costs, compared, previous_count = [], 0, None
        while compared < loop_frames + 16 * speed:
            stop = monitor.run_until_stop()
            if stop != labels["audio_irq"]:
                continue
            start = monitor.raster_time()
            monitor.run_to(labels["irq_done"])
            costs.append((monitor.raster_time() - start) %
                         PAL_FRAME_CYCLES)
            count = word(labels["music_frames"])
            if previous_count is not None:
                require(count == previous_count + 1,
                        f"Interrupt skipped: {previous_count} -> {count}")
            previous_count = count
            while model.frames < count:
                model.play()
            shadow = list(monitor.memory(labels["sid_shadow"], 25))
            require(shadow == model.shadow,
                    f"Frame {count}: SID shadow {shadow} differs from "
                    f"the model {model.shadow}")
            compared += 1
            if compared % 500 == 0:
                note(f"music: {compared} interrupts compared")
        for number in irq_points:
            monitor.delete_checkpoint(number)
        report["music"] = {
            "interrupts_compared": compared,
            "loop_frames": loop_frames,
            "first_frame": count - compared + 1, "last_frame": count,
            "cycles_max": max(costs),
            "cycles_mean": round(sum(costs) / len(costs)),
            "cycles_95th_percentile": sorted(costs)[
                int(len(costs) * 0.95)],
            "frames_over_1500": sum(c > 1500 for c in costs),
            "budget_cycles": MUSIC_BUDGET,
            "method": "on the title, MUSIC mode: raster position at "
                      "audio_irq and irq_done; SID shadow equal to "
                      "tests/player_model.py after every interrupt"}
        require(max(costs) < MUSIC_BUDGET,
                f"Music interrupt too slow: {max(costs)} cycles")
        note(f"music: max {max(costs)} cycles, mean "
             f"{report['music']['cycles_mean']}")

        # --- 4. the route ------------------------------------------
        for name in ("main_loop", "joy_ready"):
            monitor.checkpoint(labels[name])
        monitor.run_to(labels["main_loop"])
        frames = labels["frame_count"]
        zp = labels["joy_state"] if "joy_state" in labels else 2
        state_at = labels["room_slot"]         # game state block
        state_size = labels["hud_dirty"] + 1 - state_at
        combat_at = labels["slash_timer"]      # combat state block
        combat_size = labels["enemy_slot"] - combat_at
        require(combat_size == 5 + 10 * C.MAX_ENEMIES,
                f"Combat state block of {combat_size} bytes")
        audio_at = labels["audio_mode"]        # sound state block
        audio_size = labels["sid_shadow"] + 25 - audio_at
        require(audio_size == 36, f"Sound state block of {audio_size}")

        def hero():
            data = monitor.memory(zp, 8)
            vic = monitor.memory(0xD000, 0x2F)
            pointers = monitor.memory(0x47F8, 8)
            return {"joy": data[0], "x": data[1] | data[2] << 8,
                    "y": data[3], "dir": data[4], "moving": data[5],
                    "frame": data[6], "timer": data[7],
                    "pointer": pointers[0], "pointers": pointers,
                    "vic": vic, "vic_x": vic[0] + 256 * (vic[0x10] & 1),
                    "vic_y": vic[1], "d011": vic[0x11]}

        def game_state():
            data = monitor.memory(state_at, state_size)
            digits = data[9:12].hex()
            require(digits.isdigit(), f"Score {digits} is not BCD")
            seen = data[12] | data[13] << 8
            return {"room": data[0], "energy": data[1],
                    "key_set": data[2], "seals": data[3],
                    "doors_open": data[4],
                    "taken": {n for n in range(32)
                              if data[5 + n // 8] >> (n % 8) & 1},
                    "score": int(digits),
                    "seen": {n for n in range(16) if seen >> n & 1}}

        def check_state():
            world = game.world
            actual = game_state()
            wanted = {"room": world.slot, "energy": world.energy,
                      "key_set": world.key_set, "seals": world.seals,
                      "doors_open": world.doors_open,
                      "taken": world.taken, "score": world.score,
                      "seen": world.seen}
            require(actual == wanted, f"Frame {frame}: game state "
                                      f"{actual} != model {wanted}")
            program = monitor.memory(labels["game_state"], 4)
            wanted = (STATES.index(game.state), game.end_timer,
                      game.fire_armed, game.stick_held)
            require(tuple(program) == wanted,
                    f"Frame {frame}: state, end_timer, fire_armed, "
                    f"stick_held {tuple(program)} != model {wanted}")
            require(monitor.memory(labels["audio_mode"], 1)[0] ==
                    game.mode, f"Frame {frame}: audio mode")

        def check_combat():
            """slash_timer ... en_fast on the C64 against the model."""
            data = monitor.memory(combat_at, combat_size)
            n = C.MAX_ENEMIES
            enemies = []
            for slot in range(n):
                kind, low, high, y, way, hp, flash, dust, hit, fast = (
                    data[5 + i * n + slot] for i in range(10))
                enemies.append((kind, low | high << 8, y, way, hp, flash,
                                dust, hit, fast))
            actual = (*data[:5], enemies)
            fight = game.combat
            wanted = (fight.slash, fight.blade_dir, fight.fire_held,
                      fight.safe, fight.ended,
                      [(kind, x & 0xFFFF, y & 255, *rest) for
                       kind, x, y, *rest in (e.state()
                                             for e in fight.enemies)])
            require(actual == wanted, f"Frame {frame}: combat state "
                                      f"{actual} != model {wanted}")

        audio_seen = {"frames": {m: 0 for m in MODES}, "effects": set()}
        # No note left sounding: rules on the C64's own shadow
        # registers, which the next interrupt sends to the SID.
        pieces = json.loads((reference.GENERATED / "assets.json")
                            .read_text())["music"]["songs"]
        piece_frames = {labels["SONG_WON"]: pieces["won"]["frames"],
                        labels["SONG_LOST"]: pieces["lost"]["frames"]}
        quiet = {"SILENT: volume 0": 0,
                 "SOUND FX: voices 2 and 3 never gated": 0,
                 "SOUND FX, no effect: voice 1 gate off": 0,
                 "MUSIC, piece of VICTORY over: every gate off": 0,
                 "MUSIC, piece of GAME OVER over: every gate off": 0}

        def check_audio():
            data = monitor.memory(audio_at, audio_size)
            actual = {"mode": data[0], "fx_next": data[3],
                      "fx_pos": data[4], "fx_prio": data[5],
                      "song": data[7], "music_tick": data[8],
                      "music_frames": data[9] | data[10] << 8,
                      "shadow": list(data[11:36])}
            require((data[1] | data[2] << 8) == audio.irq_frames,
                    f"Frame {frame}: interrupt count "
                    f"{data[1] | data[2] << 8}, model {audio.irq_frames}")
            wanted = audio.state()
            if actual != wanted:
                diff = {k: (actual[k], wanted[k]) for k in actual
                        if actual[k] != wanted[k]}
                raise RuntimeError(f"Frame {frame}: sound state differs "
                                   f"from the model (C64, model): {diff}")
            audio_seen["frames"][MODES[audio.mode]] += 1
            if audio.fx_pos:
                audio_seen["effects"].add(audio.fx_prio)
            shadow = actual["shadow"]
            gates = [shadow[4] & 1, shadow[11] & 1, shadow[18] & 1]
            if actual["mode"] == MODE_SILENT:
                require(shadow[24] & 15 == 0,
                        f"Frame {frame}: SILENT with volume "
                        f"{shadow[24] & 15}")
                quiet["SILENT: volume 0"] += 1
            elif actual["mode"] == MODE_FX:
                require(not gates[1] and not gates[2],
                        f"Frame {frame}: a note left on voice 2 or 3 in "
                        f"SOUND FX mode, gates {gates}")
                quiet["SOUND FX: voices 2 and 3 never gated"] += 1
                if not actual["fx_pos"] and not actual["fx_next"]:
                    require(not gates[0], f"Frame {frame}: voice 1 "
                            f"still gated with no effect playing")
                    quiet["SOUND FX, no effect: voice 1 gate off"] += 1
            elif actual["song"] in piece_frames and \
                    actual["music_frames"] >= piece_frames[actual["song"]]:
                require(not any(gates), f"Frame {frame}: gates {gates} "
                        f"after the piece of the end is over")
                won_piece = actual["song"] == labels["SONG_WON"]
                quiet[f"MUSIC, piece of "
                      f"{'VICTORY' if won_piece else 'GAME OVER'} over: "
                      f"every gate off"] += 1

        seen = {"blade": set(), "enemy_pointers": set(), "hidden": 0,
                "flash": 0}

        def check_sprites(state):
            """Sprites 0-6 against the models: explorer shown or not,
            blade, three enemies, two objects."""
            vic, pointers, on = state["vic"], state["pointers"], state[
                "vic"][0x15]
            shown, blade, enemies = combat_shown
            require(bool(on & 1) == shown,
                    f"Frame {frame}: explorer "
                    f"{'shown' if on & 1 else 'hidden'}, model "
                    f"{'shown' if shown else 'hidden'}")
            wanted = [(1, blade)]
            wanted += [(2 + n, e) for n, e in enumerate(enemies)]
            wanted += [(5 + n, o) for n, o in
                       enumerate(game.world.sprites())]
            for sprite, model_sprite in wanted:
                visible = bool(on >> sprite & 1)
                require(visible == (model_sprite is not None),
                        f"Frame {frame}: sprite {sprite} "
                        f"{'on' if visible else 'off'}, model {model_sprite}")
                if model_sprite is None:
                    continue
                actual = (pointers[sprite], vic[0x27 + sprite] & 15,
                          vic[2 * sprite] + 256 * (vic[0x10] >> sprite & 1),
                          vic[2 * sprite + 1])
                require(actual == model_sprite,
                        f"Frame {frame}: sprite {sprite} {actual} != "
                        f"model {model_sprite}")
            require(on & 0x80 == 0, f"Frame {frame}: sprite 7 switched on")
            require(vic[0x1C] & 0x7F == 0x7D, f"Frame {frame}: multicolour "
                    f"bits {vic[0x1C]:08b}, the blade alone is high-res")
            seen["hidden"] += not shown
            if blade:
                seen["blade"].add(blade[0])
            for enemy in enemies:
                if enemy:
                    seen["enemy_pointers"].add(enemy[0])
                    seen["flash"] += enemy[1] == C.FLASH_COLOUR

        def check_hud():
            wanted = game.world.screen()
            require(monitor.memory(0x6000, 3 * 320) ==
                    bytes(wanted.bitmap[:3 * 320]) and
                    monitor.memory(0x4400, 3 * 40) ==
                    bytes(wanted.screen[:3 * 40]),
                    f"Frame {frame}: HUD differs from the reference for "
                    f"{game.world.hud_values()}")

        def current():
            """The reference of what the screen shows now."""
            if game.state == "title":
                return title_reference(game.mode, frame)
            if game.state == "end":
                world = game.world
                wanted = reference.expected_end(
                    texts, world.ended, world.score, world.seals,
                    len(world.seen), game.prompt)
                if game.prompt and frame != prompt_frame:
                    wanted.prompt_colour(pulse(frame))
                return wanted
            return game.world.screen()

        def change_of_room(old_slot, joy):
            """C64 side of a change of room (or of the start of a
            game, which enters the start room), after joy_ready."""
            marks = [monitor.checkpoint(labels[name]) for name in
                     ("room_blank", "next_cell_row", "room_drawn",
                      "room_shown")]
            irq_before = word(labels["irq_frames"])
            monitor.poke(zp, bytes([joy]))
            require(monitor.run_until_stop() == labels["room_blank"],
                    "No change of room started")
            require(monitor.memory(0xD011, 1)[0] & 0x10 == 0,
                    "Display not blanked before drawing")
            previous, cycles, rows = monitor.raster_time(), 0, 0
            while True:
                stop = monitor.run_until_stop()
                now = monitor.raster_time()
                cycles += (now - previous) % PAL_FRAME_CYCLES
                previous = now
                if stop == labels["room_drawn"]:
                    break
                require(stop == labels["next_cell_row"],
                        f"Unexpected stop at {stop:#06x}")
                rows += 1
            require(rows == 20, f"{rows} cell rows drawn, not 20")
            require(monitor.memory(0xD011, 1)[0] & 0x10 == 0,
                    "Display switched on during the drawing")
            require(monitor.run_until_stop() == labels["room_shown"],
                    "enter_room did not reach room_shown")
            require(monitor.memory(0xD011, 1)[0] & 0x7F == 0x3B,
                    "Display not switched on again")
            blank = (word(labels["irq_frames"]) - irq_before) & 0xFFFF
            for number in marks:
                monitor.delete_checkpoint(number)
            return {"from": old_slot, "draw_cycles": cycles,
                    "blank_frames": blank}

        def change_of_screen(joy):
            """C64 side of a new title or end screen, after joy_ready:
            draw_screen clears the screen, then draw_room draws the
            page; screen_on shows it."""
            marks = [monitor.checkpoint(labels[name]) for name in
                     ("draw_screen", "draw_room", "next_cell_row",
                      "screen_shown")]
            irq_before = word(labels["irq_frames"])
            monitor.poke(zp, bytes([joy]))
            require(monitor.run_until_stop() == labels["draw_screen"],
                    "No new screen started")
            require(monitor.memory(0xD011, 1)[0] & 0x10 == 0 and
                    monitor.memory(0xD015, 1)[0] == 0,
                    "Display or sprites on before drawing a screen")
            require(monitor.run_until_stop() == labels["draw_room"],
                    "draw_screen did not reach draw_room")
            previous, cycles, rows = monitor.raster_time(), 0, 0
            while rows < 20:
                require(monitor.run_until_stop() ==
                        labels["next_cell_row"], "Unexpected stop")
                now = monitor.raster_time()
                cycles += (now - previous) % PAL_FRAME_CYCLES
                previous = now
                rows += 1
            require(monitor.run_until_stop() == labels["screen_shown"],
                    "screen_on did not show the screen")
            require(monitor.memory(0xD011, 1)[0] & 0x7F == 0x3B,
                    "Display not switched on again")
            blank = (word(labels["irq_frames"]) - irq_before) & 0xFFFF
            for number in marks:
                monitor.delete_checkpoint(number)
            return {"draw_room_cycles": cycles, "blank_frames": blank}

        def check_hero():
            state = hero()
            model = game.hero
            require(word(frames) == frame and game.frame == frame & 0xFFFF,
                    f"Frame count off at {frame}")
            wanted = {"x": model.x, "y": model.y, "dir": model.dir,
                      "moving": model.moving, "frame": model.frame,
                      "timer": model.timer, "pointer": model.pointer}
            actual = {k: state[k] for k in wanted}
            require(actual == wanted, f"Frame {frame}: C64 {actual} != "
                                      f"model {wanted}")
            require(state["vic_x"] == model.x + 24 and
                    state["vic_y"] == model.y + 50,
                    f"Sprite registers do not follow at {frame}")
            return state

        def check_frame():
            """The checks of every frame, by state."""
            global_state = game.state
            if global_state in ("play", "ending"):
                state = check_hero()
                pointers.add(state["pointer"])
                check_sprites(state)
            else:
                require(word(frames) == frame, f"Frame count off at {frame}")
                if global_state == "title":
                    check_title_sprites(frame)
                    check_prompt(pulse(frame), frame)
                else:
                    require(monitor.memory(0xD015, 1)[0] == 0,
                            f"Frame {frame}: sprites on the end screen")
                    if game.prompt:
                        check_prompt(PROMPT_PRINTED if frame ==
                                     prompt_frame else pulse(frame), frame)
            check_state()
            check_combat()

        probe = {"on": False, "points": [], "costs": {k: [] for k in
                                                      PROBES}}

        def probe_kind():
            kind = None
            if audio.mode == MODE_FX:
                kind = "FX"
            elif audio.mode == MODE_SILENT:
                kind = "SILENT"
            elif game.state in ("ending", "end") and audio.player.song:
                kind = "MUSIC, end of a game"
            if kind and len(probe["costs"][kind]) < PROBES[kind]:
                return kind
            return None

        def set_probe(wanted):
            if wanted == probe["on"]:
                return
            if wanted:
                probe["points"] = [monitor.checkpoint(labels[name])
                                   for name in ("audio_irq", "irq_done")]
            else:
                for number in probe["points"]:
                    monitor.delete_checkpoint(number)
            probe["on"] = wanted

        def advance(target):
            """run_to(target), timing the sound interrupts met."""
            begin = None
            while True:
                stop = monitor.run_until_stop()
                if stop == target:
                    return
                if stop == labels["audio_irq"]:
                    begin = monitor.raster_time()
                elif stop == labels["irq_done"] and begin is not None:
                    kind = probe_kind()
                    if kind:
                        probe["costs"][kind].append(
                            (monitor.raster_time() - begin) %
                            PAL_FRAME_CYCLES)
                    begin = None

        def play_sounds(sounds, drawn):
            """The requests of a frame, with the interrupts that came
            while its room or screen was drawn: at ("draw",), or after
            the requests if the frame has no such mark."""
            if ("draw",) not in sounds:
                sounds = list(sounds) + [("draw",)]
            for item in sounds:
                if item == ("draw",):
                    for _ in range(drawn):
                        audio.irq()
                else:
                    audio.request(item)

        start_frame = word(frames)
        texts_end = [monitor.memory(labels[name], 32)
                     for name in ("over_text", "won_text")]
        game = G.Game(hud_frame, start_room, texts_end,
                      labels["HERO_START_X"], labels["HERO_START_Y"],
                      frame=start_frame)
        audio = AudioModel(memory, labels)
        c64_audio = monitor.memory(audio_at, audio_size)
        while audio.player.frames != (c64_audio[9] | c64_audio[10] << 8):
            audio.player.play()             # the theme since the title
        audio.irq_frames = c64_audio[1] | c64_audio[2] << 8
        frame, pointers, blocked_frames = start_frame, set(), 0
        prompt_frame = None
        visited, openings = set(), set()
        combat_shown = None
        check_frame()
        check_audio()
        costs, total_steps, end_states = [], 0, []
        menu_seen, menu_changes, early = {MODE_MUSIC}, 0, 0
        last_hud = game.world.hud_values()
        game_help = []                  # what the test did in this game
        for joy, count, expectation, shot in script:
            if joy in ("energy", "seals", "enemy", "slow"):
                game_help.append(joy)
            if joy == "slow":                   # a slow skeleton
                monitor.poke(labels["en_fast"] + count, b"\x00")
                game.combat.enemies[count].fast = 0
                report["events"].append({
                    "frame": frame, "room": game.world.slot,
                    "event": f"test makes enemy {count} slow"})
                continue
            if joy == "energy":                 # set by the test
                monitor.poke(labels["energy"], bytes([count]))
                monitor.poke(labels["hud_dirty"], b"\x01")
                game.world.energy = count
                report["events"].append({"frame": frame,
                                         "event": f"test sets energy "
                                                  f"to {count}"})
                continue
            if joy == "seals":                  # set by the test
                monitor.poke(labels["seals"], bytes([count]))
                monitor.poke(labels["hud_dirty"], b"\x01")
                game.world.seals = count
                report["events"].append({"frame": frame,
                                         "event": f"test sets seals "
                                                  f"to {count}"})
                continue
            if joy == "enemy":                  # placed by the test
                slot, (x, y) = count, expectation
                for name, value in (("en_x_lo", x & 255), ("en_x_hi", x >> 8),
                                    ("en_y", y)):
                    monitor.poke(labels[name] + slot, bytes([value]))
                enemy = game.combat.enemies[slot]
                enemy.x, enemy.y = x, y
                report["events"].append({
                    "frame": frame, "room": game.world.slot,
                    "event": f"test moves enemy {slot} to ({x}, {y})"})
                continue
            if joy == "align":                  # in step with the plan
                joy, count = 0, (count - frame) % ALIGN
            hero_now = game.hero
            start = (game.state, game.world.slot, hero_now and hero_now.x,
                     hero_now and hero_now.y)
            steps0 = hero_now.steps if hero_now else 0
            entered, changes = [], []
            for _ in range(count):
                old_slot, model_before = game.world.slot, game.hero
                steps_before = model_before.steps if model_before else 0
                events_before = len(game.world.events)
                state_before = game.state
                result = game.step(joy)
                drawing = result["room"] is not None or \
                    result["screen"] is not None
                set_probe(bool(probe_kind()) and not drawing)
                advance(labels["joy_ready"])
                interrupts = (word(labels["irq_frames"]) -
                              audio.irq_frames) & 0xFFFF
                require(interrupts == 1 - early, f"Frame {frame + 1}: "
                        f"{interrupts} interrupts since the last frame")
                for _ in range(interrupts):
                    audio.irq()
                early = 0
                change = screen = None
                if not drawing:
                    begin = monitor.raster_time()
                    monitor.poke(zp, bytes([joy]))
                    advance(labels["main_loop"])
                    end = monitor.raster_time()
                    require(end > begin, f"Frame {frame + 1}: the work "
                                         f"ran past the frame")
                    costs.append((end - begin, frame + 1, game.state,
                                  game.world.slot,
                                  result["over"] or result["won"]))
                    play_sounds(result["sounds"], 0)
                elif result["room"] is not None:
                    change = change_of_room(old_slot, joy)
                    play_sounds(result["sounds"], change["blank_frames"])
                    monitor.run_to(labels["main_loop"])
                else:
                    screen = change_of_screen(joy)
                    play_sounds(result["sounds"], screen["blank_frames"])
                    monitor.run_to(labels["main_loop"])
                frame += 1
                if game.state != state_before:
                    changes.append(game.state)
                model = game.hero
                if (game.state == "play" and joy & 15 and
                        model is model_before and
                        model.steps == steps_before):
                    blocked_frames += 1
                if result["prompt"]:
                    prompt_frame = frame
                if game.state == "play" or result["over"] or result["won"]:
                    combat_shown = game.combat.sprites(frame, model)
                check_frame()
                check_audio()
                if change is not None:
                    compare(current(), f"Room {game.world.slot}")
                    new_slot = game.world.slot
                    zone = game.world.page()[reference.ZONE_AT]
                    require(monitor.memory(labels["colour_zone"], 1)[0]
                            == zone, f"Room {new_slot}: colour_zone is "
                                     f"not zone {zone}")
                    change["zone"] = zone
                    if result["screen"] == "play":
                        side = "start"
                        visited.add(new_slot)
                    else:
                        side = SIDES[new_slot - old_slot]
                        openings.add((old_slot, side))
                        visited.add(new_slot)
                        entered.append(new_slot)
                    change.update(to=new_slot, side=side, frame=frame,
                                  mode=MODES[game.mode],
                                  entry=[model.x, model.y],
                                  door_open=game.world.door()[1],
                                  objects_left=len(game.world.objects()),
                                  enemies=sum(bool(e.kind) for e in
                                              game.combat.enemies))
                    report["transitions"].append(change)
                    note(f"room {old_slot} -> {new_slot} ({side}): "
                         f"{change['draw_cycles']} cycles, "
                         f"{change['blank_frames']} blank frames")
                if screen is not None:
                    compare(current(), f"Screen {game.state}")
                    screen.update(to=game.state, frame=frame,
                                  mode=MODES[game.mode],
                                  ended=game.world.ended)
                    report["screens"].append(screen)
                    note(f"screen {game.state}: "
                         f"{screen['blank_frames']} frames")
                if result["menu"]:
                    menu_seen.add(game.mode)
                    menu_changes += 1
                    compare(current(), f"Title, {MODES[game.mode]}")
                if result["prompt"]:
                    compare(current(), "End screen, PRESS FIRE")
                if result["opened"] or result["over"] or result["won"]:
                    compare(current(), f"Room {game.world.slot}")
                if result["over"] or result["won"]:
                    world = game.world
                    end_states.append({
                        "how": world.ended,
                        "frame": frame, "room": world.slot,
                        "mode": MODES[game.mode],
                        "energy": world.energy,
                        "keys": world.keys(), "seals": world.seals,
                        "score": world.score,
                        "doors_open": world.doors_open,
                        "rooms_seen": len(world.seen),
                        "objects_taken": sorted(world.taken),
                        "test_help": sorted(set(game_help)),
                        "joystick_only": not game_help})
                if game.state == "play" and \
                        game.world.hud_values() != last_hud:
                    check_hud()
                    last_hud = game.world.hud_values()
                if result["screen"] == "play":
                    last_hud = game.world.hud_values()
                    game_help.clear()           # a new game
                report["events"].extend(
                    {"frame": frame, "room": game.world.slot,
                     "event": event}
                    for event in game.world.events[events_before:])
                if frame % 8 == 0:
                    phase = (frame >> 3) & 3
                    require(monitor.memory(labels["torch_phase"], 1)[0]
                            == phase, f"Torch phase wrong at {frame}")
                    for address in current().torches:
                        require(monitor.memory(address, 8) ==
                                flames[phase * 8:phase * 8 + 8],
                                f"Flame at {address:#06x} not phase {phase}")
                if frame % 64 == 0:
                    wanted_now = current()
                    offsets = {a - 0x6000 + i for a in wanted_now.torches
                               for i in range(8)}
                    bitmap = monitor.memory(0x6000, 8000)
                    require(all(bitmap[i] == wanted_now.bitmap[i]
                                for i in range(8000) if i not in offsets),
                            f"Bitmap changed outside the torches ({frame})")
            hero_now = game.hero
            steps = (hero_now.steps - steps0 if hero_now is not None and
                     start[0] == "play" and game.state == "play" and
                     "play" not in changes else None)
            total_steps += steps or 0
            note(f"joy={joy:05b} x{count}: {start} -> {game.state} "
                 f"{game.world.slot}, {steps} steps")
            if expectation in CHANGE:
                require(changes == [CHANGE[expectation]],
                        f"Segment joy={joy:05b} expected {expectation}, "
                        f"changes {changes}")
            elif expectation == "idle":
                require(not changes and not entered and not steps,
                        f"Segment joy={joy:05b} expected idle")
            elif expectation in ("title", "still"):
                require(not changes and (game.state == "title") ==
                        (expectation == "title") and game.state != "play",
                        f"Segment joy={joy:05b} expected {expectation}, "
                        f"state {game.state}, changes {changes}")
            elif isinstance(expectation, int):
                require(entered == [expectation] and not changes,
                        f"Segment joy={joy:05b} expected room "
                        f"{expectation}, entered {entered}")
            else:
                require(not entered and not changes and
                        game.state == "play",
                        f"Unexpected change {entered} {changes}")
                if expectation == "blocked":
                    require(steps == 0, f"Segment joy={joy:05b} expected "
                                        f"{expectation}, made {steps} steps")
                elif expectation == "moves":
                    require(steps, f"Segment joy={joy:05b} expected "
                                   f"moves, made {steps} steps")
            report["segments"].append({
                "joy": f"{joy:05b}", "frames": count, "from": list(start),
                "to": [game.state, game.world.slot,
                       hero_now and hero_now.x, hero_now and hero_now.y],
                "steps": steps, "expected": expectation})
            if shot:
                set_probe(False)
                capture = vice.screenshot(shot)
                capture.update(frame=frame, state=game.state,
                               room=game.world.slot,
                               mode=MODES[game.mode],
                               hud=list(game.world.hud_values()))
                # the text monitor lets the machine run while exporting,
                # and it stops again at a checkpoint: read the stops
                # that came meanwhile, then run on to the end of a frame
                monitor.read_registers()
                monitor.run_to(labels["main_loop"])
                idle = word(frames) - frame
                require(0 < idle <= 200,
                        f"Odd drift after screenshot {idle}")
                events_before = len(game.world.events)
                state_before = game.state
                for _ in range(idle):
                    result = game.step(0)
                    require(not result["sounds"] and
                            game.state == state_before,
                            "Something happened while idle")
                    audio.irq()
                require(len(game.world.events) == events_before,
                        "Something happened while idle")
                # exporting runs the machine to the end of a frame: the
                # interrupt of the next frame may have come already
                early = ((word(labels["irq_frames"]) - audio.irq_frames)
                         & 0xFFFF)
                require(early in (0, 1), f"{early} interrupts early")
                for _ in range(early):
                    audio.irq()
                frame += idle
                if game.state == "play":
                    combat_shown = game.combat.sprites(frame, game.hero)
                check_frame()
                check_audio()
                capture["idle_frames_during_export"] = idle
                report["screenshots"].append(capture)
        set_probe(False)
        require(pointers == set(range(8)),
                f"Not all eight hero frames shown: {sorted(pointers)}")
        require(len(report["screenshots"]) == 11,
                "Eleven screenshots needed")
        summary = json.loads((reference.GENERATED / "assets.json")
                             .read_text())
        rooms = {room["slot"] for room in summary["rooms"]}
        needed = {(room["slot"], side) for room in summary["rooms"]
                  for side in room["exits"]}
        require(visited == rooms, f"Rooms visited {visited}, not {rooms}")
        require(openings == needed,
                f"Openings used {sorted(openings)}, not {sorted(needed)}")

        # --- 5. HUD values, in the seventh game --------------------
        hud_points = [monitor.checkpoint(labels[name]) for name in
                      ("hud_update", "hud_ready")]

        def show_hud(values):
            energy, keys, seals, score = values
            monitor.run_to(labels["main_loop"])
            monitor.poke(labels["energy"], bytes([energy]))
            monitor.poke(labels["key_set"], bytes([(1 << keys) - 1]))
            monitor.poke(labels["seals"], bytes([seals]))
            monitor.poke(labels["score"], bcd(score))
            monitor.poke(labels["hud_dirty"], b"\x01")
            monitor.run_to(labels["hud_update"])
            start = monitor.raster_time()
            monitor.run_to(labels["hud_ready"])
            cost = (monitor.raster_time() - start) % PAL_FRAME_CYCLES
            require(monitor.memory(labels["hud_dirty"], 1)[0] == 0,
                    "hud_update did not clear hud_dirty")
            screen = reference.expected_screen(hud_frame, game.world.slot,
                                               values)
            for name, address, wanted_bytes in (
                    ("HUD bitmap", 0x6000, screen.bitmap[:3 * 320]),
                    ("HUD screen RAM", 0x4400, screen.screen[:3 * 40])):
                actual = monitor.memory(address, len(wanted_bytes))
                require(actual == bytes(wanted_bytes),
                        f"{name} differs from the reference for {values}")
            return cost

        hud_costs = [show_hud(HUD_TEST), show_hud((8, 0, 0, 0))]
        for number in hud_points:
            monitor.delete_checkpoint(number)
        report["hud"] = {
            "values_tested": [list(HUD_TEST), [8, 0, 0, 0]],
            "hud_update_cycles": max(hud_costs),
            "method": "in the last game: values written by the test "
                      "(keys as bits of key_set), hud_dirty set; HUD rows "
                      "compared with the reference after hud_update"}

        # --- coverage and figures ----------------------------------
        events = [(e.get("room"), e["event"]) for e in report["events"]]
        pages = reference.load("rooms.bin")
        dungeon = {(slot, n): pages[slot * 256 + C.ENEMIES_AT + n * 4]
                   for slot in rooms for n in range(C.MAX_ENEMIES)
                   if pages[slot * 256 + C.ENEMIES_AT + n * 4]}
        defeated = {(room, int(event.split()[1])) for room, event in events
                    if event.startswith("enemy") and
                    event.endswith("defeated")}
        require(defeated == set(dungeon), "Enemies never defeated: "
                f"{sorted(set(dungeon) - defeated)}")
        kinds = [dungeon[(room, int(event.split()[1]))]
                 for room, event in events
                 if event.startswith("enemy") and event.endswith("defeated")]

        def tally(test):
            return sum(1 for _, event in events if test(event))
        count = {
            "blows_that_only_hurt": tally(
                lambda e: e.startswith("enemy") and e.endswith(" hit")),
            "skeletons_defeated": kinds.count(C.SKELETON),
            "bats_defeated": kinds.count(C.BAT),
            "explorer_hurt": tally(lambda e: e.startswith("hurt")),
            "game_over": tally(lambda e: e == "GAME OVER"),
            "victory": tally(lambda e: e == "VICTORY"),
            "new_game": tally(lambda e: e == "new game")}
        require(count["blows_that_only_hurt"] > 0 and
                count["explorer_hurt"] > 1 and count["game_over"] == 4 and
                count["victory"] == 2 and count["new_game"] == 7,
                f"Combat coverage {count}")
        blades = {C.BLADE_FRAME + d for d in range(4)}
        require(seen["blade"] == blades,
                f"Blade frames shown {sorted(seen['blade'])}")
        figures = set(range(C.COMBAT_POINTER, C.DUST_FRAME + 1))
        require(seen["enemy_pointers"] == figures,
                f"Enemy frames shown {sorted(seen['enemy_pointers'])}")
        require(seen["hidden"] and seen["flash"],
                "Blinking explorer or flashing enemy never seen")
        require(game.combat.near_hits > 0,
                "No enemy hit by the point half way back")
        endings = [(e["how"], e["mode"]) for e in end_states]
        require(endings == [("won", "FX"), ("lost", "MUSIC"),
                            ("lost", "FX"), ("won", "MUSIC"),
                            ("lost", "SILENT"), ("lost", "SILENT")],
                f"Ends of the games seen: {endings}")
        helped = [(e["how"], e["mode"], e["test_help"]) for e in end_states
                  if not e["joystick_only"]]
        require(helped == [("won", "MUSIC", ["seals"]),
                           ("lost", "SILENT", ["enemy", "energy", "slow"])],
                f"Games the test helped: {helped}")
        won = end_states[0]
        kinds_by_number = {}
        for slot in rooms:
            for n in range(2):
                kind, _, _, number = pages[slot * 256 + 200 + n * 4:
                                           slot * 256 + 204 + n * 4]
                if kind:
                    kinds_by_number[number] = kind
        needed_objects = {number for number, kind in kinds_by_number.items()
                          if kind != 6}             # potions: if needed
        require(needed_objects <= set(won["objects_taken"]),
                "Keys, treasures or seals left: "
                f"{sorted(needed_objects - set(won['objects_taken']))}")
        require(won["doors_open"] == 15 and won["seals"] == 3 and
                won["keys"] == 0 and won["room"] == start_room and
                won["rooms_seen"] == 16 and won["mode"] == "FX",
                f"State at VICTORY {won}")
        potions = {number for number, kind in kinds_by_number.items()
                   if kind == 6}
        taken_events = [event for _, event in events
                        if event.startswith("object")]
        world = game.world
        require(menu_seen == {MODE_MUSIC, MODE_FX, MODE_SILENT},
                f"Menu lines chosen {menu_seen}")
        numbers = {labels[f"FX_{name}"]: name for name in
                   ("SLASH", "HIT", "DUST", "PICKUP", "DOOR", "HURT",
                    "LOST", "WON")}
        require(set(audio.started) == set(numbers),
                f"Effects started {sorted(audio.started)}")
        require(audio.refused > 0 and audio.replaced > 0,
                "Priorities never tested: "
                f"{audio.refused} refused, {audio.replaced} replaced")
        require(labels["SONG_LOST"] in audio.songs and
                labels["SONG_WON"] in audio.songs,
                f"Songs started {audio.songs}")
        require(all(audio_seen["frames"].values()),
                f"Frames by audio mode {audio_seen['frames']}")
        require(game.state == "play" and game.mode == MODE_SILENT,
                "The last game is not a silent game")

        blank = [t["blank_frames"] for t in report["transitions"]]
        draw = [t["draw_cycles"] for t in report["transitions"]]
        report["changes_of_room"] = {
            "count": len(blank), "openings_used": sorted(
                f"{slot} {side}" for slot, side in openings),
            "draw_cycles_min": min(draw), "draw_cycles_max": max(draw),
            "blank_frames_min": min(blank), "blank_frames_max": max(blank),
            "method": "raster position at every cell row of draw_room "
                      "and show_door (display off); blank frames counted "
                      "by the sound interrupt (irq_frames) from the start "
                      "of the frame to room_shown; the start of a game "
                      "clears the screen and draws the HUD first"}
        starts = [t["blank_frames"] for t in report["transitions"]
                  if t["side"] == "start"]
        report["changes_of_room"]["frames_to_start_a_game"] = starts
        report["changes_of_screen"] = {
            "count": len(report["screens"]),
            "frames": {kind: sorted({s["blank_frames"] for s in
                                     report["screens"] if s["to"] == kind})
                       for kind in ("title", "end")},
            "draw_room_cycles_max": max(s["draw_room_cycles"]
                                        for s in report["screens"]),
            "method": "draw_screen: clear_screen, the page by draw_room "
                      "(timed at every cell row), big letters and words; "
                      "frames counted by the sound interrupt"}
        cycles = sorted(c[0] for c in costs)
        worst = max(costs)
        playing = max(c for c in costs if c[2] == "play" and not c[4])
        by_state = {state: max((c[0] for c in costs if c[2] == state),
                               default=0) for state in STATES}
        report["frame_work"] = {
            "frames_measured": len(costs),
            "cycles_max": worst[0], "worst_frame": worst[1],
            "worst_state": worst[2], "worst_room": worst[3],
            "worst_ends_the_game": worst[4],
            "cycles_max_while_playing": playing[0],
            "worst_playing_frame": playing[1],
            "worst_playing_room": playing[3],
            "cycles_max_by_state": by_state,
            "cycles_mean": round(sum(cycles) / len(cycles)),
            "cycles_95th_percentile": cycles[int(len(cycles) * 0.95)],
            "share_of_frame_max": round(worst[0] / PAL_FRAME_CYCLES, 3),
            "method": "raster position at joy_ready and at the next "
                      "main_loop (the state's frame, HUD, torches); "
                      "frames that draw a room or a screen are not "
                      "counted; the end must come before the start of "
                      "the next frame"}
        note(f"frame work: max {worst[0]} cycles "
             f"({report['frame_work']['share_of_frame_max']:.0%})")
        irq = {kind: {"interrupts": len(values), "cycles_max": max(values),
                      "cycles_mean": round(sum(values) / len(values))}
               for kind, values in probe["costs"].items() if values}
        require(set(irq) == set(PROBES),
                f"Sound interrupt timed in {sorted(irq)} only")
        require(all(v["cycles_max"] < MUSIC_BUDGET for v in irq.values()),
                f"Sound interrupt too slow: {irq}")
        started = {numbers[n]: times for n, times in
                   sorted(audio.started.items())}
        require(all(quiet.values()), f"Silence rules not all met: {quiet}")
        report["no_stuck_notes"] = dict(
            frames_checked=quiet,
            method="every frame, on the shadow SID registers of the C64 "
                   "(the next interrupt sends them to the SID): in "
                   "SILENT the volume is 0; in SOUND FX voices 2 and 3 "
                   "are never gated and voice 1 is not gated when no "
                   "effect plays or is asked for; in MUSIC, once a "
                   "piece of the end has played its "
                   f"{pieces['won']['frames']} frames, no voice is "
                   "gated. The route crosses deaths, victories, the "
                   "menu and restarts in every mode")
        report["sound"] = {
            "frames_compared_by_mode": audio_seen["frames"],
            "effects_started": started,
            "effects_refused_less_important": audio.refused,
            "effects_over_another": audio.replaced,
            "songs_started": [["THEME", "WON", "LOST"][s]
                              for s in audio.songs],
            "interrupt_cycles": irq,
            "method": "every frame: audio_mode, irq_frames, fx_next, "
                      "fx_pos, fx_prio, music_song, music_tick, "
                      "music_frames and the 25 shadow SID registers "
                      "equal to tests/audio_model.py, the frame's "
                      "interrupts played in the model where they came "
                      "(before the requests of the frame, or while its "
                      "room or screen was drawn); interrupt cost by "
                      "raster position at audio_irq and irq_done"}
        report["states"] = {
            "menu_lines_chosen": sorted(MODES[m] for m in menu_seen),
            "menu_changes": menu_changes,
            "ending_frames": G.ENDING_FRAMES,
            "end_delay_frames": G.END_DELAY,
            "method": "game_state, end_timer, fire_armed, stick_held and "
                      "audio_mode equal to tests/game_model.py every "
                      "frame; the title and end screens compared with "
                      "the reference when drawn, the menu when it "
                      "changes, PRESS FIRE when it appears and its glow "
                      "every frame; title sprites every frame"}
        report["combat"] = dict(
            count, enemies_in_dungeon=len(dungeon),
            every_enemy_defeated=True,
            blade_frames=sorted(seen["blade"]),
            enemy_frames=sorted(seen["enemy_pointers"]),
            explorer_hidden_frames=seen["hidden"],
            flash_sprite_frames=seen["flash"],
            hits_by_the_near_point=game.combat.near_hits,
            method="enemies, blow and damage timer compared with "
                   "tests/combat_model.py every frame")
        report["game"] = {
            "state_at_victory": won, "ends_of_games": end_states,
            "potions": sorted(potions),
            "potions_left_in_the_won_game": sorted(
                potions - set(won["objects_taken"])),
            "objects_taken_events": len(taken_events),
            "note": "a potion is taken only below full energy; the "
                    "others are left on the floor"}
        zones = [t for t in report["transitions"] if "zone" in t]
        changes_of_zone = [b for a, b in zip(zones, zones[1:])
                           if a["zone"] != b["zone"] and b["side"] != "start"]
        report["zones"] = {
            "changes_of_zone": len(changes_of_zone),
            "blank_frames_with_zone_change": sorted(
                {t["blank_frames"] for t in changes_of_zone}),
            "method": "colour_zone read after every change of room; the "
                      "screen compared with the reference, which uses "
                      "the zone's colour tables from zones.color"}
        report["final_state"] = {
            "state": game.state, "mode": MODES[game.mode],
            "room": world.slot, "energy": world.energy,
            "keys": world.keys(), "seals": world.seals,
            "score": world.score, "doors_open": world.doors_open,
            "objects_taken": sorted(world.taken),
            "note": "after the seventh game has begun"}
        report.update(
            result="PASS", video="PAL", checked_frames=frame - start_frame,
            total_steps=total_steps, blocked_frames=blocked_frames,
            final_hero=[game.hero.x, game.hero.y],
            checks=["the PRG without holes: every data block at its "
                    "address after unpack, equal to its generated file",
                    "$01 = $36 before draw_room",
                    "the title's draw_room timed at every cell row, the "
                    "sound interrupt running",
                    "title, end screens and rooms equal to the reference "
                    "renderer (bitmap, screen RAM, Color RAM, "
                    "walkability map, torch list) when drawn; the menu "
                    "when it changes; PRESS FIRE when it appears",
                    "the program starts on the title with MUSIC; up and "
                    "down move the cursor one line per push, stopping "
                    "at both ends, up winning over down; the mode "
                    "changes at once; a stick held when the title "
                    "comes does not move it",
                    "Fire starts a game only when let go after a press "
                    "seen on the title; on the end screen only after "
                    "two seconds and with a new press",
                    "the end of a game: GAME OVER or VICTORY in the room "
                    "for 50 frames, then the end screen with score, "
                    "seals and rooms entered, then the title",
                    "music interrupt every frame for more than a loop on "
                    "the title, SID shadow equal to the player model, "
                    "cost measured",
                    "sound state and SID shadow equal to the sound model "
                    "every frame in the three modes: theme, piece of "
                    "the lost game, silence, every effect, priorities",
                    "no note left sounding: SILENT at volume 0, no gate "
                    "in SOUND FX without an effect, none after a piece "
                    "of the end, through deaths, victories and restarts",
                    "a won game and three lost games with the joystick "
                    "only; seven games without loading the PRG again",
                    "explorer, room, game state (rooms entered "
                    "included), combat state (35 bytes) and sprites 0-6 "
                    "equal to the Python models every frame of a game",
                    "title sprites and the glow of PRESS FIRE every frame",
                    "every opening of the sixteen rooms used; entry "
                    "positions as world_model.py",
                    "each room in the colours of its zone",
                    "fast skeletons, and one made slow by the test; patrols "
                    "across and up and down",
                    "a blow hits an enemy on top of the explorer too",
                    "every enemy of the dungeon defeated at least once",
                    "blade in the four directions; one blow per press",
                    "enemies come back when a room is entered again",
                    "damage: two cells, then 30 frames safe, blinking",
                    "doors A, B, C and the portal as the model",
                    "keys, treasures, potions and seals as the model",
                    "display off while a room or screen is drawn",
                    "all eight hero frames displayed",
                    "game work of every frame measured in every state: "
                    "it ends inside the frame",
                    "flame phase of every torch every 8 frames, on "
                    "every screen",
                    "bitmap unchanged outside the torch cells",
                    "HUD values rewritten by hud_update as the reference",
                    "eleven native 384x272 PAL screenshots",
                    "memory map: every area from $0801 to $CFFF, no "
                    "overlap"])
        report["memory"] = memory_map.build(
            labels, prg.read_bytes(), root / "game/src/memory.asm")
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        vice.close()
        (evidence / "game-test.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8",
            newline="\n")
    print(json.dumps({k: report[k] for k in
                      ("result", "unpack", "title_draw_room", "music",
                       "sound", "no_stuck_notes", "memory",
                       "changes_of_room", "changes_of_screen", "frame_work",
                       "combat", "states", "final_state", "checked_frames",
                       "total_steps")}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", type=int, default=None,
                        help="7 or 8: that step of the chain")
    parser.add_argument("--root", type=Path, default=None,
                        help="another copy of the step (a variant)")
    parser.add_argument("--evidence", default=None,
                        help="folder of the report, inside the project")
    parser.add_argument("--script", type=Path, default=None,
                        help="another route, a module with SCRIPT")
    parser.add_argument("--set", action="append", default=[],
                        help="a Python statement that changes the model, "
                             "e.g. 'game_model.END_DELAY = 50'")
    parser.add_argument("--vice", type=Path, default=DEFAULT_VICE)
    parser.add_argument("--settle", type=float, default=6.0,
                        help="seconds to wait for autostart")
    args = parser.parse_args()
    try:
        verify(args)
    except Exception as error:
        print(f"Game verification FAILED: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

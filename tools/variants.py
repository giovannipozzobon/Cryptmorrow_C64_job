"""The guided variants and the "Where it breaks" versions of the chain.

Read by tools/make_variants.py, which builds each one in
variants/NN-name/ID/ from chain/NN-name/, proves it and writes its
README.md.

A variant is one idea changed in one place of the step: the same
change is made in the Python model (`model`, statements run before the
test and the planner), so the test compares the changed program with
the changed model frame by frame, on the step's own route or on one of
its own (`route`, planned into tests/routes/variant_ID.py); `expect`
are the facts of its report that show the change. A break is a
classic mistake made on purpose: the step's own test must stop it
(`fails`, a pattern of the failure message) and `shot` photographs it
(tools/shoot.py: a route and how many of its entries to play).

Edits: (file in the step folder, old text, new text); the old text
must be there exactly once. Everything the reader reads (README) is in
English.
"""

VARIANTS = [
    # --- step 01: the first room --------------------------------------
    dict(id="01a-faster-flames", step=1, kind="variant",
         title="Faster flames",
         summary="The torches flicker twice as fast: a new flame every "
                 "4 frames instead of every 8.",
         edits=[("game/src/main.asm",
                 "        and #7\n"
                 "        bne frame_done\n"
                 "        lda frame_count         ; phase = frame / 8 mod 4\n"
                 "        lsr a\n"
                 "        lsr a\n"
                 "        lsr a\n"
                 "        and #3",
                 "        and #3\n"
                 "        bne frame_done\n"
                 "        lda frame_count         ; phase = frame / 4 mod 4\n"
                 "        lsr a\n"
                 "        lsr a\n"
                 "        and #3")],
         model=["step_model.FLAME_SHIFT = 2"],
         where="`game/src/main.asm`, at `frame_end`: the mask that picks "
               "the frames that animate, and the shifts that turn the "
               "frame count into the flame phase.",
         see="Every torch changes its flame every 4 frames, 12.5 times "
             "a second on a PAL machine; the four flames still come in "
             "the same order.",
         limits="Mask and shifts go together: `and #1` with one `lsr a` "
                "(every 2 frames), `and #3` with two, `and #7` with three, "
                "`and #15` with four. The final `and #3` stays: there are "
                "four flames in `FLAMES`. Change only the mask and nothing "
                "visible happens (the phase still moves every 8 frames).",
         depends="Nothing else: `animate_torches` draws whatever phase it "
                 "is given. The test's model has the same period "
                 "(`FLAME_SHIFT`).",
         expect=[("the four flames every 4 frames",
                  "r['shows']['the four flame phases'] == [0, 1, 2, 3]")]),
    dict(id="01b-more-torches", step=1, kind="variant",
         title="Two more torches",
         summary="The Moss Gate is data: two more torch tiles in its map "
                 "and the room has six burning torches.",
         edits=[("game/assets/rooms/moss_gate.txt",
                 "#####T###GG###t#####",
                 "###T#T###GG###t#t###")],
         model=[],
         where="`game/assets/rooms/moss_gate.txt`, the second row of the "
               "map: `T` is a wall torch with its flame on the left, `t` "
               "on the right.",
         see="Six torches along the north wall and on the sides, all "
             "burning; `draw_room` finds them while it draws and puts "
             "them in its list, the main loop animates the list.",
         limits="A torch needs floor below it. At most six torches a room "
                "(`MAX_TORCHES` in `room.asm`): the asset builder refuses "
                "a seventh; in the engine it would keep the flame "
                "painted in its tile and never move. The asset builder checks the map and the "
                "number of metatiles (128 at most; this map needs no new "
                "one).",
         depends="The same room is the start of the game in every later "
                 "step; nothing else changes.",
         expect=[("six torches listed at the start",
                  "r['starts'][0]['torches'] == 6")]),
    # --- step 02: the explorer ----------------------------------------
    dict(id="02a-faster-explorer", step=2, kind="variant",
         title="A faster explorer",
         summary="The explorer walks two pixels a frame instead of one.",
         edits=[("game/src/hero.asm",
                 "HERO_SPEED   = 1        ; pixels per frame",
                 "HERO_SPEED   = 2        ; pixels per frame")],
         model=["hero_model.HERO_SPEED = 2"],
         route="route_variant_02a.py", shows=False,
         where="`game/src/hero.asm`, the constant `HERO_SPEED`.",
         see="The explorer crosses the Moss Gate in half the time; walls "
             "and pillars still stop it exactly at their edge, because "
             "`update_hero` tests the next pixel before each of the "
             "`HERO_SPEED` steps.",
         limits="1 or 2. From step 03 `world.asm` refuses more "
                "(`.cerror HERO_SPEED > WEST_EDGE + 1`): at 3 pixels the "
                "explorer could step over the west edge and X would wrap "
                "round.",
         depends="The walking frames count frames, not pixels "
                 "(`WALK_RATE`): the legs move at the same pace.",
         expect=[("two pixels in a frame",
                  "any(s['steps'] == 2 * s['frames'] > 0 "
                  "for s in r['segments'])")]),
    dict(id="02b-quicker-steps", step=2, kind="variant",
         title="Quicker steps",
         summary="The walking frames alternate every 4 frames instead of "
                 "every 8.",
         edits=[("game/src/hero.asm",
                 "WALK_RATE    = 8        ; frames between walk frames",
                 "WALK_RATE    = 4        ; frames between walk frames")],
         model=["hero_model.WALK_RATE = 4"],
         where="`game/src/hero.asm`, the constant `WALK_RATE`, used by "
               "`animate_hero`.",
         see="The legs move twice as fast; the explorer does not: its "
             "speed is `HERO_SPEED`.",
         limits="1 to 255 frames. With 1 the two frames alternate every "
                "frame and blur into one.",
         depends="Nothing else.",
         expect=[("all eight walking frames",
                  "r['shows']['all eight walking frames'] == "
                  "list(range(8))")]),
    # --- step 03: the dungeon -----------------------------------------
    dict(id="03a-autumn-moss", step=3, kind="variant",
         title="Autumn moss",
         summary="The atrium in other colours: the moss turns orange and "
                 "yellow, with the same pixels.",
         edits=[("game/assets/tiles.py",
                 '    "atrio": {},                                '
                 '# moss green, unchanged',
                 '    "atrio": {GREEN: ORANGE, LIGHT_GREEN: YELLOW},  '
                 '# autumn moss')],
         model=[],
         where="`game/assets/tiles.py`, `ZONE_PALETTES`: each zone maps "
               "the catalogue's colours to its own; the atrium, `atrio` "
               "in the code, kept them all.",
         see="The seven rooms of the atrium with orange and yellow moss; "
             "`set_zone` copies the atrium's tables as before, only their "
             "bytes have changed.",
         limits="Any of the 16 colours, per colour of the catalogue. "
                "Colours not listed stay. Keep the floor and the walls "
                "apart, or the explorer will not stand out.",
         depends="Only `zones.color` changes; the asset builder writes "
                 "it again (`run-game.ps1` does).",
         expect=[("the rooms as the reference with the new tables",
                  "r['result'] == 'PASS'")]),
    dict(id="03b-green-energy", step=3, kind="variant",
         title="A green energy bar",
         summary="The cells of energy left are light green instead of "
                 "light red.",
         edits=[("game/src/hud.asm",
                 "        .byte BAR_COLUMN, HUD_ROW, LIGHT_RED",
                 "        .byte BAR_COLUMN, HUD_ROW, LIGHT_GREEN"),
                ("game/src/hud.asm",
                 "        lda #LIGHT_RED << 4",
                 "        lda #LIGHT_GREEN << 4")],
         model=["reference.FULL = 13"],
         where="`game/src/hud.asm`: the colour of the bar in `hud_frame` "
               "(printed once) and in `hud_update` (every change).",
         see="Eight light green cells after ENERGY.",
         limits="One colour in two places: `hud_update` repaints the bar "
                "in the same call as `hud_frame`, so changing only "
                "`hud_frame` changes nothing, and changing only "
                "`hud_update` changes the whole bar at once. Keep "
                "it far from dark grey, the colour of the cells lost.",
         depends="Nothing else. (A constant for the colour would keep "
                 "the two places together: a challenge for the reader.)",
         expect=[("the HUD as the reference, bar in light green",
                  "r['result'] == 'PASS'")]),
    # --- step 04: objects and doors -----------------------------------
    dict(id="04a-generous-potion", step=4, kind="variant",
         title="A more generous potion",
         summary="A potion gives back four cells of energy instead of "
                 "two.",
         edits=[("game/src/objects.asm",
                 "POTION_ENERGY  = 2      ; cells of the bar per potion",
                 "POTION_ENERGY  = 4      ; cells of the bar per potion")],
         model=["world_model.POTION_ENERGY = 4"],
         where="`game/src/objects.asm`, the constant `POTION_ENERGY`.",
         see="In step 04 nothing takes energy away, so a potion stays on "
             "the floor: the bar is full. The test writes 4 into "
             "`energy`; then the potion of the Root Cellar fills the "
             "bar again.",
         limits="1 to 8: the energy never goes above `ENERGY_MAX` "
                "(`use_object` stops it there). A potion stays on the "
                "floor while the bar is full.",
         depends="Nothing else in this step; with the combat (step 05) "
                 "the game becomes easier.",
         expect=[("the potion from four cells to eight",
                  "r['result'] == 'PASS'")]),
    dict(id="04b-richer-treasures", step=4, kind="variant",
         title="Richer treasures",
         summary="A treasure is worth 500 points instead of 250.",
         edits=[("game/src/objects.asm",
                 "points_low:     .byte $00, $50  ; seal 1000, treasure 250",
                 "points_low:     .byte $00, $00  ; seal 1000, treasure 500"),
                ("game/src/objects.asm",
                 "points_middle:  .byte $10, $02",
                 "points_middle:  .byte $10, $05")],
         model=["world_model.POINTS[5] = 500"],
         where="`game/src/objects.asm`, the tables `points_low` and "
               "`points_middle`: the points of a seal and of a treasure "
               "in BCD, two digits a byte.",
         see="The won game ends with 7000 points: three seals (3000) and "
             "eight treasures (4000).",
         limits="Each byte holds two decimal digits, $00 to $99: 500 is "
                "$05 $00, not $01 $F4. The score has six digits.",
         depends="The score of the HUD and, from step 07, of the end "
                 "screen.",
         expect=[("7000 points at VICTORY",
                  "r['ends_of_games'][0]['score'] == 7000")]),
    # --- step 05: combat ----------------------------------------------
    dict(id="05a-gentler-damage", step=5, kind="variant",
         title="Gentler damage",
         summary="A touch takes one cell of energy instead of two.",
         edits=[("game/src/combat.asm",
                 "DAMAGE        = 2       ; cells of energy a touch",
                 "DAMAGE        = 1       ; cells of energy a touch")],
         model=["combat_model.DAMAGE = 1"],
         route="route_variant_05a.py", shows=False,
         where="`game/src/combat.asm`, the constant `DAMAGE`, used by "
               "`check_contact`.",
         see="The explorer survives eight touches instead of four.",
         limits="From 1 up. With 0 no touch ever hurts; with 8 or more one "
                "touch always ends the game, because the energy stops at "
                "zero.",
         depends="`SAFE_FRAMES` (30 frames of protection after a touch) "
                 "stays as it is.",
         expect=[("eight touches before GAME OVER",
                  "sum(1 for e in r['events'] if e['game'] == 1 and "
                  "e['event'].startswith('hurt')) == 8")]),
    dict(id="05b-lazy-bats", step=5, kind="variant",
         title="Lazy bats",
         summary="A bat wakes only when the explorer comes within 60 "
                 "pixels across and 45 up or down, instead of 120 and 90.",
         edits=[("game/src/combat.asm",
                 "CHASE_X       = 120     ; a bat chases the explorer",
                 "CHASE_X       = 60      ; a bat chases the explorer"),
                ("game/src/combat.asm",
                 "CHASE_Y       = 90      ; inside this distance",
                 "CHASE_Y       = 45      ; inside this distance")],
         model=["combat_model.CHASE_X = 60", "combat_model.CHASE_Y = 45"],
         route="route_variant_05b.py", shows=False,
         where="`game/src/combat.asm`, the constants `CHASE_X` and "
               "`CHASE_Y`, used by `bat_step`, which `update_enemies` calls.",
         see="In the Root Cellar the bat stays still while the explorer "
             "stands 66 pixels away; closer, it wakes and comes.",
         limits="1 to 254: `measure` gives 255 for any distance it cannot "
                "hold in a byte. Two values, one idea: the box around "
                "the bat.",
         depends="Only bats; skeletons patrol whatever the distance.",
         expect=[("the bat still at 66 pixels",
                  "any(s['frames'] >= 40 and s['enemies_from'] == "
                  "s['enemies_to'] and s['enemies_from'] and "
                  "s['enemies_from'][0][0] == 2 for s in r['segments'])")]),
    # --- step 06: sound -----------------------------------------------
    dict(id="06a-effects-first", step=6, kind="variant",
         title="Start with the sound effects",
         summary="The program starts in SOUND FX mode instead of MUSIC.",
         edits=[("game/src/main.asm",
                 "START_MODE  = MODE_MUSIC  ; or MODE_FX, MODE_SILENT",
                 "START_MODE  = MODE_FX     ; or MODE_MUSIC, MODE_SILENT")],
         model=[],
         route="route_variant_06a.py", shows=False,
         where="`game/src/main.asm`, the constant `START_MODE`.",
         see="No theme: the blade, the hits and the dust have their "
             "sounds on voice 1.",
         limits="`MODE_MUSIC`, `MODE_FX` or `MODE_SILENT`. In step 07 "
                "the menu of the title chooses and `START_MODE` goes.",
         depends="Nothing else: `start_audio` sets the mode it finds in "
                 "`audio_mode`.",
         expect=[("effects only",
                  "r['totals']['frames_by_mode']['MUSIC'] == 0 and "
                  "r['totals']['frames_by_mode']['FX'] > 0 and "
                  "len(r['totals']['effects_started']) >= 3")]),
    dict(id="06b-faster-music", step=6, kind="variant",
         title="Faster music",
         summary="The theme and the pieces of the end at 150 beats a "
                 "minute instead of 125.",
         edits=[("game/assets/score.py",
                 "SPEED = 6            # frames per step: 50 / 6 * 60 / 4 "
                 "= 125 BPM (PAL)",
                 "SPEED = 5            # frames per step: 50 / 5 * 60 / 4 "
                 "= 150 BPM (PAL)")],
         model=[],
         route="route_variant_06b.py", shows=False,
         where="`game/assets/score.py`, `SPEED`: frames per sixteenth "
               "note; the asset builder writes it into `music.asm` as "
               "`MUSIC_SPEED`.",
         see="The same notes, quicker; the piece of GAME OVER ends "
             "sooner and then every note is released.",
         limits="Above `GATE_TICK`, 4: the gate is released on frame 4 of "
                "the last step of a note, and with 4 frames a step or "
                "fewer that frame never comes, so repeated notes no "
                "longer attack; lower `GATE_TICK` with it for very "
                "fast music. 12 is slow. Envelopes and vibrato do not "
                "change.",
         depends="Only the music: the game counts its own frames.",
         expect=[("theme and piece of GAME OVER, then silence",
                  "r['totals']['songs'] == [0, 2] and "
                  "r['sound']['no_stuck_notes']"
                  "['MUSIC, piece of GAME OVER over: every gate off'] > 0")]),
    # --- step 07: title and end screens --------------------------------
    dict(id="07a-another-name", step=7, kind="variant",
         title="Another name on the title",
         summary="The big letters of the title spell BONE CRYPT.",
         edits=[("game/src/screens.asm",
                 '        .byte 4, 1, STYLE_LOGO\n'
                 '        .text "CRYPTMORROW"',
                 '        .byte 5, 1, STYLE_LOGO\n'
                 '        .text "BONE CRYPT"')],
         model=[],
         where="`game/src/screens.asm`, `logo_text`: column, row, style "
               "and the letters.",
         see="BONE CRYPT in the big letters, centred: ten characters, "
             "each 3 cells wide, from column 5.",
         limits="Capital letters and spaces (the big font has A to Z); "
                "at most 13 characters in 40 columns; the column is "
                "(40 - 3 x characters) / 2.",
         depends="Nothing else; the game keeps its name everywhere else.",
         expect=[("the title as the reference", "r['result'] == 'PASS'")]),
    dict(id="07b-shorter-wait", step=7, kind="variant",
         title="A shorter wait at the end",
         summary="Fire counts on the end screen after one second instead "
                 "of two.",
         edits=[("game/src/screens.asm",
                 "END_DELAY     = 100     ; two seconds before Fire counts",
                 "END_DELAY     = 50      ; one second before Fire counts")],
         model=["game_model.END_DELAY = 50"],
         route="route_variant_07b.py",
         where="`game/src/screens.asm`, the constant `END_DELAY`.",
         see="PRESS FIRE appears one second after the end screen.",
         limits="1 to 255 frames. Too short, and a player still hammering "
                "Fire from the last fight leaves the end screen before "
                "reading it: after the wait, one press and one release "
                "are enough.",
         depends="Nothing else.",
         expect=[("the complete route, replanned", "r['result'] == 'PASS'")]),
]

BREAKS = [
    dict(id="01x-hires", step=1, kind="break",
         title="The multicolour bit forgotten",
         summary="`$08` instead of `$18` in $D016: the VIC shows the "
                 "multicolour bitmap as a high-resolution one.",
         edits=[("game/src/main.asm",
                 "        lda #$18                ; multicolour, 40 columns",
                 "        lda #$08                ; multicolour, 40 columns")],
         symptom="The Moss Gate in thin coloured stripes: every pair of "
                 "bits is read as two pixels, and the colours come from "
                 "screen RAM only.",
         cause="Bit 4 of $D016 switches multicolour mode on. The bitmap, "
               "screen RAM and Color RAM are all right: only the way the "
               "VIC reads them is wrong.",
         fails="VIC set up",
         shot=("tests/routes/step_01.py", "1")),
    dict(id="02x-missing-jump", step=2, kind="break",
         title="A missing jump",
         summary="Without `jmp try_move` after the left direction the "
                 "code falls into the right one: left walks right.",
         edits=[("game/src/hero.asm",
                 "        lda #DIR_LEFT\n"
                 "        sta hero_dir\n"
                 "        jmp try_move\n"
                 "go_right:",
                 "        lda #DIR_LEFT\n"
                 "        sta hero_dir\n"
                 "go_right:")],
         symptom="Pushed left, the explorer turns and walks right.",
         cause="Assembly has no `else`: after the left branch the "
               "processor goes on with the next instruction, which "
               "stores DIR_RIGHT.",
         fails=r"Frame \d+: C64",
         shot=("tests/routes/step_02.py", "2")),
    dict(id="03x-high-byte", step=3, kind="break",
         title="A high byte left behind",
         summary="`exit_east` sets the low byte of X and forgets the high "
                 "one: X is a 16-bit number on a 320-pixel screen.",
         edits=[("game/src/world.asm",
                 "        lda #0\n"
                 "        sta hero_x+1\n"
                 "        lda #1                  ; a room right",
                 "        lda #1                  ; a room right")],
         symptom="Through an opening to the east the explorer appears "
                 "near the east wall of the next room, not by the opening "
                 "it came through, and walks on towards the next exit.",
         cause="The explorer left at X 295 or more, so `hero_x+1` is 1; the new low "
               "byte, 9, makes X = 256 + 9 = 265.",
         fails=r"Frame \d+: C64",
         shot=("tests/routes/step_03.py",
               "[i for i, e in enumerate(s) if e[2] == 5][1] + 1")),
    dict(id="04x-key-kept", step=4, kind="break",
         title="A key that is never used up",
         summary="`ora` instead of `eor` when a door opens: the key "
                 "stays.",
         edits=[("game/src/objects.asm",
                 "        eor key_set             ; the key is used up",
                 "        ora key_set             ; the key is used up")],
         symptom="Door A opens and the HUD still shows the key.",
         cause="The key's bit is set: `eor` clears it, `ora` leaves it "
               "set.",
         fails="game state",
         shot=("tests/routes/step_04.py",
               "next(i for i, e in enumerate(s) if e[2] == 8) + 1")),
    dict(id="05x-no-floor", step=5, kind="break",
         title="Energy below zero",
         summary="Without `lda #0` the subtraction wraps: one cell minus "
                 "two is 255.",
         edits=[("game/src/combat.asm",
                 "        lda #0                  ; not below zero",
                 "        nop                     ; not below zero")],
         symptom="With one cell left a touch fills the bar, and the game "
                 "that should be over goes on.",
         cause="Energy is one unsigned byte: 1 - 2 = 255 with the carry "
               "clear; `bcs` skips the fix only when there was enough.",
         fails=r"Frame \d+",
         shot=("tests/routes/step_05.py",
               "[i for i, e in enumerate(s) if e[2] == 'ending'][-1] + 1")),
    dict(id="06x-stuck-note", step=6, kind="break",
         title="A blade without a sound",
         summary="Without `inc fx_pos` every sound effect stays on its "
                 "first frame, the one with the gate off: the effects "
                 "fall silent.",
         edits=[("game/src/player.asm",
                 "        inc fx_pos",
                 "        nop")],
         symptom="In SOUND FX mode the first blow of the sword makes no "
                 "sound, and from then on no effect is heard.",
         cause="`fx_pos` never reaches the end mark of the effect, so the "
               "interrupt plays the same step every frame: the first "
               "one, whose gate is off. `fx_prio` stays set, so every "
               "later effect is accepted and stays on its own first "
               "step too.",
         fails="sound state differs",
         shot=None),
    dict(id="07x-held-stick", step=7, kind="break",
         title="A stick held into the title",
         summary="`show_title` forgets the stick already pushed: the menu "
                 "moves by itself.",
         edits=[("game/src/screens.asm",
                 "        lda joy_state           ; a stick already pushed",
                 "        lda #0                  ; a stick already pushed")],
         symptom="Coming back to the title with the stick held down, the "
                 "cursor moves down a line by itself (from MUSIC to "
                 "SOUND FX), the theme stops and the pickup sounds.",
         cause="`stick_held` is 0, so the push the player has been "
               "holding looks new to `title_frame`.",
         fails="Frame|Segment",
         shot=("tests/verify_game.py",
               "next(i for i, e in enumerate(s) if e[0] == 2 and "
               "e[1] == 8 and e[2] == 'title') + 1")),
    dict(id="08x-first-block", step=8, kind="break",
         title="The first block left behind",
         summary="`bne` instead of `bcs` in unpack: the loop stops before "
                 "the first block.",
         edits=[("game/src/unpack.asm",
                 "        bcs unpack_block        ; until below the first",
                 "        bne unpack_block        ; until below the first")],
         symptom="The explorer's sprite on the title is made of the "
                 "packed bytes that happen to be at $4000.",
         cause="X counts 6 bytes a block down to 0: `bne` leaves when X "
               "becomes 0, before copying block 0; `bcs` goes on until "
               "the subtraction borrows.",
         fails="not in place",
         shot=("tests/verify_game.py", "2")),
]

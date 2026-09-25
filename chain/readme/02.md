# Cryptmorrow, step 02 - The explorer

The explorer in the Moss Gate: joystick in port 2, four directions
(horizontal wins over vertical), two walking frames for each direction,
walls and pillars that stop it through the walkability map drawn in step
01. `update_hero` remembers what stopped it (`hero_block`): a wall, or a
door, which the next steps will open.

New or changed: `hero.asm` (new); `main.asm` reads the joystick and runs `play_frame`.

Not yet: The openings do not lead anywhere yet: the map simply ends.

## Build and play

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) exports the assets,
checks the line length, assembles `game/src/main.asm` with 64tass and
starts VICE (PAL, SID 6581); keypad 8/2/4/6 moves the explorer. With other installations add
`-Python`, `-Assembler` and `-Vice`.

The program is `game/build/cryptmorrow.prg`. This step is generated from
the source of the complete game (`tools/make_chain.py` in the project):
every file, routine and address here is the one of the finished game.

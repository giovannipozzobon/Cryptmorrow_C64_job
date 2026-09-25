# Cryptmorrow, step 06 - Sound

The SID in a raster interrupt, once a frame: the theme in MUSIC mode,
eight sound effects on voice 1 in FX mode, with priorities, silence in
SILENT mode; a short piece or effect at the end of a game. `START_MODE`
in `main.asm` chooses the mode: MUSIC, or change it to `MODE_FX` to hear
the effects.

New or changed: `player.asm` (new); the effects asked for in `combat.asm` and `objects.asm`.

Not yet: The modes are exclusive; the menu to choose them comes in step 07.

## Build and play

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) exports the assets,
checks the line length, assembles `game/src/main.asm` with 64tass and
starts VICE (PAL, SID 6581); keypad 8/2/4/6 moves, 0 strikes. With other installations add
`-Python`, `-Assembler` and `-Vice`.

The program is `game/build/cryptmorrow.prg`. This step is generated from
the source of the complete game (`tools/make_chain.py` in the project):
every file, routine and address here is the one of the finished game.

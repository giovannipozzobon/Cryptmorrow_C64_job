# Cryptmorrow, step 03 - The dungeon

Sixteen rooms on a grid of 4 x 4. Walking through an opening draws the
next room with the display off and shows it from the top of a frame; the
explorer enters on the opposite edge. Each zone has its own colours
(`set_zone` copies them). The HUD shows energy, keys, seals and score on
row 1, with its rules.

New or changed: `hud.asm` (new); `world.asm` gains the exits; `text.asm` prints lists.

Not yet: The HUD values do not change yet; doors and the portal stay shut.

## Build and play

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) exports the assets,
checks the line length, assembles `game/src/main.asm` with 64tass and
starts VICE (PAL, SID 6581); keypad 8/2/4/6 moves the explorer. With other installations add
`-Python`, `-Assembler` and `-Vice`.

The program is `game/build/cryptmorrow.prg`. This step is generated from
the source of the complete game (`tools/make_chain.py` in the project):
every file, routine and address here is the one of the finished game.

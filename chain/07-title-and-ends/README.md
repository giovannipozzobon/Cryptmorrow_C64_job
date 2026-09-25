# Cryptmorrow, step 07 - Title and end screens

A title with the logo in big letters over the Moss Gate, its menu of
audio modes (MUSIC, SOUND FX, SILENT) and PRESS FIRE; after GAME OVER
or VICTORY the room stands still for a second, then the end screen with
score, seals and rooms explored; Fire goes back to the title and a new
game begins without loading again. This is the complete game.

New or changed: `screens.asm` (new); `main.asm` runs a state machine.

Not yet: The program file still has holes between its data (48 KB).

## Build and play

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) exports the assets,
checks the line length, assembles `game/src/main.asm` with 64tass and
starts VICE (PAL, SID 6581); on the title 8/2 choose the mode, 0 (pressed and let go) starts. With other installations add
`-Python`, `-Assembler` and `-Vice`.

The program is `game/build/cryptmorrow.prg`. This step is generated from
the source of the complete game (`tools/make_chain.py` in the project):
every file, routine and address here is the one of the finished game.

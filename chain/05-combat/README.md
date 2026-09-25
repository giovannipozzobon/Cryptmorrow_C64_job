# Cryptmorrow, step 05 - Combat

The sword (Fire), skeletons that patrol, bats that chase the explorer
when it comes near; enemies come back each time a room is entered. A
touch takes two cells of energy, then 30 frames of safety with the
explorer blinking; without energy: GAME OVER.

New or changed: `combat.asm` complete.

Not yet: Silent. After the end load the program again.

## Build and play

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) exports the assets,
checks the line length, assembles `game/src/main.asm` with 64tass and
starts VICE (PAL, SID 6581); keypad 8/2/4/6 moves, 0 strikes. With other installations add
`-Python`, `-Assembler` and `-Vice`.

The program is `game/build/cryptmorrow.prg`. This step is generated from
the source of the complete game (`tools/make_chain.py` in the project):
every file, routine and address here is the one of the finished game.

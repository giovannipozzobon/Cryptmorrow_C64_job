# Cryptmorrow, step 04 - Objects and doors

Keys, treasures, potions and seals as sprites 5 and 6; what is taken is
kept in bits for the whole game. A door opens with its key (and uses it
up), the portal of the Moss Gate with the three seals; out through it:
VICTORY in place of the room's name, and the game stops. The HUD values
follow the game. This is already a complete game, without enemies.

New or changed: `objects.asm` (new); `combat.asm` begins with the end of a game.

Not yet: No enemies yet. After VICTORY load the program again to play again.

## Build and play

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) exports the assets,
checks the line length, assembles `game/src/main.asm` with 64tass and
starts VICE (PAL, SID 6581); keypad 8/2/4/6 moves the explorer. With other installations add
`-Python`, `-Assembler` and `-Vice`.

The program is `game/build/cryptmorrow.prg`. This step is generated from
the source of the complete game (`tools/make_chain.py` in the project):
every file, routine and address here is the one of the finished game.

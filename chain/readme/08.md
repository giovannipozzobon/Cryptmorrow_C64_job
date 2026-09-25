# Cryptmorrow, step 08 - The complete game

The game of step 07, with its data packed behind the code: the program
file drops from 48 KB to 25 KB and `unpack` puts every block at its
address when the program starts. This is Cryptmorrow 1.0.1, byte for byte.

New or changed: `unpack.asm` (new); `data.asm` assembles each block for its address.

## Build and play

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) exports the assets,
checks the line length, assembles `game/src/main.asm` with 64tass and
starts VICE (PAL, SID 6581); on the title 8/2 choose the mode, 0 (pressed and let go) starts. With other installations add
`-Python`, `-Assembler` and `-Vice`.

The program is `game/build/cryptmorrow.prg`. This step is generated from
the source of the complete game (`tools/make_chain.py` in the project):
every file, routine and address here is the one of the finished game.

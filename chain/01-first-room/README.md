# Cryptmorrow, step 01 - The first room

The Moss Gate on the screen, drawn by the tile engine: VIC-II bank
`$4000`-`$7FFF`, multicolour bitmap at `$6000`, screen RAM at `$4400`,
Color RAM. A room is a page of 256 bytes at `ROOM_DATA`: a map of 20 x 10
metatiles (2 x 2 cells each), its zone and its name. `draw_room` draws
bitmap, colours and the walkability map cell row by cell row, keeps a
list of the torches and prints the name with the cell font; the main loop
waits for each frame and animates the flames every 8 frames.

New or changed: `main.asm`, `memory.asm`, `room.asm`, `text.asm`, `world.asm`, `data.asm`.

Not yet: No explorer, no joystick: the room only.

## Build and play

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) exports the assets,
checks the line length, assembles `game/src/main.asm` with 64tass and
starts VICE (PAL, SID 6581). With other installations add
`-Python`, `-Assembler` and `-Vice`.

The program is `game/build/cryptmorrow.prg`. This step is generated from
the source of the complete game (`tools/make_chain.py` in the project):
every file, routine and address here is the one of the finished game.

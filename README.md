# Cryptmorrow

The code of **Cryptmorrow**, Volume 2 of the C64 Game Manual Series
(CODE & BOOKS) by Eric A. Norton: a complete game for the Commodore 64,
written in assembly language for its 6510 processor, and every step of
it as the book builds it.

Under the hill of Morrow lies a crypt of sixteen rooms in four zones.
The explorer walks it with a sword: three keys for three locked doors,
treasures and potions, skeletons and bats, and three seals that open
the portal of the Moss Gate. Out through the portal, the game is won.
The title offers music, sound effects or silence.

The repository is the companion of the book. Every listing printed in
the book is a part of a file here, line for line, and every program
here can be rebuilt and compared byte for byte (`verify.py`).

## Play without building

`releases/cryptmorrow-1.0.1.prg` is the complete game, Cryptmorrow
1.0.1, 25 233 bytes. `releases/cryptmorrow-1.0.1.d64` holds the same
program on a 1541 disk image. Start either in VICE:

```text
x64sc -pal -autostartprgmode 1 -joydev2 1 -autostart releases/cryptmorrow-1.0.1.prg
```

`-autostartprgmode 1` puts the program straight into memory; without
it VICE loads it through its emulated 1541, which takes about a minute,
as on a real C64. With the disk image, attach it to drive 8 and type
`LOAD"CRYPTMORROW",8,1`, then `RUN`.

- Joystick in port 2. `-joydev2 1` puts it on the numeric keypad: 8, 2,
  4 and 6 move, 0 is Fire.
- On the title, up and down choose MUSIC, SOUND FX or SILENT; Fire,
  pressed and let go, starts a game.
- In the game the stick walks and Fire strikes. After GAME OVER or
  VICTORY, PRESS FIRE appears after two seconds; Fire goes back to the
  title.

The game is written for a PAL C64 and was tested in VICE's PAL C64
with a 6581 SID. It was not tested on a real C64 or on an NTSC machine.

SHA-256 of the PRG:
`a51f4f5eca5c318c4f85ea32f2be05bcadbad36995b862db453cf4d62cb9e2c6`

## What is here

```text
game/          the complete game, 1.0.1: the master source (game/src),
               whose comments also say in which steps each line exists,
               and the tools and data of its graphics, rooms and sound
               (game/assets)
chain/         the eight steps of the book, 01 to 08: each folder has
               its own copy of every source and tool it needs and
               builds on its own
variants/      22 experiments of the book, each a step with one change:
               14 guided variants and 8 "Where it breaks" versions,
               with a README and the report of its test (evidence/)
tests/         the tests the book relies on (chapter 14)
tools/         run-game.ps1, which builds and plays, and the tools
               named in the book
reference/     the reference programs of the steps and variants
releases/      the complete game, as a PRG and as a D64 disk image
verify.py      builds everything again and compares it byte for byte
CHAPTERS.md    chapter by chapter: its step, variants and tools
TESTING.md     what was tested, with which versions, and the limits
SHA256SUMS.txt the SHA-256 of every file
LICENSE        MIT
```

## What you need

None of these programs is included; download them from their sites.

- **64tass** 1.60.3243, the assembler (tass64.sourceforge.net).
  1.59.3120 gives the same bytes; another version may not.
- **VICE** 3.10, the emulator, whose `x64sc` is the C64
  (vice-emu.sourceforge.io; for Windows, GTK3VICE).
- **Python** 3.10 or later (python.org). Everything uses its standard
  library only.
- On Windows, PowerShell, which comes with Windows, for
  `tools/run-game.ps1`.

`run-game.ps1` and `verify.py` look for `64tass`, `x64sc` and `python`
on the PATH.

## Build and play a step

Open PowerShell in a step folder, for example `chain/01-first-room`,
and type:

```text
.\tools\run-game.ps1 -Mode Build
.\tools\run-game.ps1 -Mode Play
```

`Build` writes the data (`game/assets/build_assets.py`), checks that no
source line is longer than 60 characters (`tools/check_lines.py`) and
assembles `game/src/main.asm` into `game/build/cryptmorrow.prg`, with
the listing (`.lst`) and the labels for VICE's monitor (`.lbl`). `Play`
builds, then starts `x64sc` as a PAL C64 with a 6581 SID
(`-Model 8580` for the other SID). If a program is not on the PATH, give
its full path with `-Assembler`, `-Vice` or `-Python`. If PowerShell
refuses the script, run it for this one command:

```text
powershell -ExecutionPolicy Bypass -File tools\run-game.ps1 -Mode Play
```

The same script works in every folder of `chain` and `variants`, and at
the root of the repository, where it builds `game/`, the complete game;
there `-Mode Verify` also runs its test.

Without PowerShell, on Linux for example, the same stages by hand, in
the step folder:

```text
python3 game/assets/build_assets.py
python3 tools/check_lines.py
mkdir -p game/build
64tass --cbm-prg -Wall -Werror --vice-labels-numeric \
    -l game/build/cryptmorrow.lbl -L game/build/cryptmorrow.lst \
    -o game/build/cryptmorrow.prg game/src/main.asm
x64sc -pal -autostart game/build/cryptmorrow.prg
```

Work on a copy of a step, not on the step itself (chapter 1): the book
and `verify.py` compare your programs with the steps as they are.

## Check that you build the book's programs

```text
python verify.py
```

`verify.py` checks every file against `SHA256SUMS.txt`, builds the
complete game, the eight steps and the 22 variants again in a temporary
folder, and compares every program, byte for byte, with the one in
`reference/` or `releases/`; it also reads the program back from the
disk image. A file you changed on purpose is reported as changed.

The programs of the steps:

| Step | Bytes | SHA-256 |
|---|---|---|
| `chain/01-first-room` | 47 105 | `ceeeccddefcb89970439978d9de7ccbee0dde15a195152f5a9306614587a330a` |
| `chain/02-explorer` | 47 105 | `69f27de19fa7a1930180a0d0e9d3b9455288189142224ffb0caa67ee409109c6` |
| `chain/03-dungeon` | 47 105 | `9353b9965e51da6b9b2a383020abcb4ef43d8f1f8ab30a2de52059c5bfe75b9a` |
| `chain/04-objects-doors` | 47 105 | `01e118c38a015b1241669f58a27425aeb55b8d6666ffacd03d90a791964a7058` |
| `chain/05-combat` | 47 105 | `5d2798d9d1045c8750b93ed33a18a1d6a5cddf68d5fc185dee479db59a6b3e00` |
| `chain/06-sound` | 48 238 | `9f6dc56e40f0d7839fd97ddb89d9739a9990cf50a0240425f2d617abd9d5273c` |
| `chain/07-title-and-ends` | 48 238 | `e7cdd0e41ab37be1fb75c4b18de73d4f058fe46599afab5d4ab93181a178496e` |
| `chain/08-complete` | 25 233 | `a51f4f5eca5c318c4f85ea32f2be05bcadbad36995b862db453cf4d62cb9e2c6` |

## Run the tests

```text
python tests/verify_step.py --step 1 --vice PATH
python tests/verify_game.py --step 8 --vice PATH
```

`verify_step.py` checks steps 01 to 06, `verify_game.py` steps 07 and
08; each starts VICE itself, plays a planned route with the joystick
and compares every frame with models written in Python. `PATH` is the
full path of `x64sc`. Build the step first (`-Mode Build` in its
folder): a test reads `game/build`. The report goes to
`chain/evidence/NN-name/`. On Linux without a display, start the
tests and the tools that run VICE under `xvfb-run`.
[TESTING.md](TESTING.md) tells what was checked, and how.

## Rights

The contents of this repository, source code, data, tools, tests and
programs, including the graphics, rooms, font, sprites, music and sound
effects in `game/assets`, are released under the MIT License: see
[LICENSE](LICENSE). Copyright (c) 2026 Eric A. Norton.

The book is not part of this repository and is not covered by this
license: its text, figures, layout and cover are copyright (c) 2026
Eric A. Norton, all rights reserved. Book by Eric A. Norton; music and
history edited by Jorah Sallow.

Everything in the game was made for it: graphics, rooms, font, sprites,
music and sound effects. No ROM, emulator or assembler is included.
Commodore 64 and the other product names are used to identify the
machine and the tools; this is an independent project, not affiliated
with or endorsed by their owners.

# What was tested, and the limits

Everything here ran in VICE, the emulator. Nothing was run on a real
Commodore 64, and nothing on an NTSC machine. Chapter 14 of the book
("How this book was checked") tells how the tests work; this page gives
the results, the versions and what the repository cannot repeat.

## The versions

| Program | Versions used |
|---|---|
| 64tass | 1.60.3243 on Windows; 1.59.3120 on Linux: the same bytes for every program |
| VICE, `x64sc` | 3.10 on Windows and on Linux; 3.7.1 on Linux |
| Python | 3.10 and 3.11, standard library only |
| PowerShell | On Windows, the steps were built and played with an earlier version of `run-game.ps1`; this version was run with PowerShell 7.4.6 on Linux |

Every test used a PAL C64 with the 6581 SID.

## The results printed in the book

| Check | Result |
|---|---|
| Tests of steps 01 to 06 (`tests/verify_step.py`), frames compared | 514, 1 117, 3 039, 11 545, 17 567, 18 719: all PASS |
| Tests of steps 07 and 08 (`tests/verify_game.py`) | 20 081 frames each: PASS |
| The route of the complete game | Seven games; one won with the joystick only, every room entered, every one of the 34 enemies defeated at least once, every opening used |
| One-line defects put in on purpose | Steps 01 to 06: 18 of 18 stopped (`tools/mutate_steps.py`); 1.0.1: 49 of 49 stopped |
| Variants and "Where it breaks" versions | 14 PASS; 8 stopped by their test, as they must be |
| Figures | 41 figures, 66 captures, each taken twice and identical |
| Screenshots of the step tests, Windows against Linux | 37 of 37 identical |
| Instructions run by the tests (`tools/exec_coverage.py`) | 2 386 of 2 392 |
| Work of a frame, at most | About 13 500 cycles, 69% of a frame, as a game ends; about 8 950 while playing |
| Listings of the book | Every one compared with its source; no line over 60 characters |

The six instructions that no test reaches are defences for a change of
map or speed, and the first instruction of the program, where the
monitor cannot stop:

| File, line | Instruction | Why no test reaches it |
|---|---|---|
| `hero.asm`, 245 | `lda #1` | The explorer never leaves the screen in these rooms |
| `hero.asm`, 246 | `rts` | The same |
| `main.asm`, 26 | `sei` | Runs at every start; the monitor cannot stop on the instruction it starts from |
| `objects.asm`, 176 | `inc obj_x_high` | Only for an object in column 15; none is there |
| `room.asm`, 128 | `inc room_ptr+1` | Only if a map row crossed a page; none does |
| `text.asm`, 127 | `inc text_scr+1` | Only if a string crossed a page of screen RAM; none does |

(Lines of `chain/08-complete/game/src`.)

## Checked again for this repository

The repository as it is here was checked on 25 September 2026, on
Linux, from a copy of this folder: Python 3.11.15, 64tass 1.59.3120,
VICE 3.10 and 3.7.1, PowerShell 7.4.6.

| Check | Result |
|---|---|
| `python verify.py` | Every file unchanged; the complete game, the 8 steps and the 22 variants built again: 31 of 31 identical to their reference; the 22 test reports of the variants name the programs here; the D64 holds the release byte for byte |
| The tests of the steps, VICE 3.10 | Steps 01 to 06: 514, 1 117, 3 039, 11 545, 17 567 and 18 719 frames, PASS; steps 07 and 08: 20 081 frames each, PASS. The numbers of the book |
| `tools/mutate_steps.py`, VICE 3.10 | 18 of 18 defects stopped |
| `tools/make_chain.py --out` another folder | The eight steps and `chain/coverage.csv` identical to those here |
| `tools/make_variants.py` in a copy | READMEs, `variants.json` and programs identical to those here |
| `tools/plan_route.py`, steps 01 to 06 | Steps 01, 02, 04, 05 and 06: the routes of `tests/routes`, byte for byte. Step 03: a route of the same length that takes other turns where two ways cost the same; the test passes with it too, 3 039 frames. The route in `tests/routes` is the one the book counts |
| `tools/load_time.py`, VICE 3.10 | 119 045 440 and 63 128 042 cycles, 120.83 and 64.07 seconds: the measures of chapter 13 |
| `tools/sid_writes.py`, VICE 3.7.1 | The same writes as the measure of chapter 11, which was taken with VICE 3.10 |
| `tools/measure_routine.py`, `sid_silence` of step 06 | 390 cycles, as in chapter 11 |
| `tools/run-game.ps1`, PowerShell 7.4.6 | Build in a step and at the root gives the reference programs; Play starts `x64sc` with the options of chapter 1; a program missing from the PATH is named |
| `releases/cryptmorrow-1.0.1.d64`, VICE 3.10, 1541 with true drive emulation | Loads (`LOAD"*",8,1`, 100 blocks) and the title appears |
| The listings of the book, 147, and the file names it prints, 89 | All compared with the files here: identical, all present |

`run-game.ps1` in this form has not yet been run on Windows: the steps
of the book were built and played there with an earlier version, which
found the programs in the author's folders rather than on the PATH.

## What the repository cannot repeat

- **The 49 defects of 1.0.1.** They were put into the complete game,
  and stopped by its test, in the author's project before the steps
  were made; that harness is not here. `tools/mutate_steps.py` repeats
  the 18 defects of steps 01 to 06.
- **The figures of the book.** They were captured by an editorial tool
  that is not part of the repository. `tools/shoot.py` takes the same
  kind of screenshot, and the pictures of the "Where it breaks"
  versions are in their `evidence/` folders.
- **The reports of the steps' tests.** They are not included: running
  a test writes its report again, in `chain/evidence/NN-name/`. The
  reports of the variants' tests are in their folders.

## Limits

- A test compares the program with models written in Python for this
  purpose. A model could be wrong in the same way as the program; the
  reference renderer (`tests/reference.py`), written again from the
  data rather than from the assembly, and the defects above, which the
  tests had to stop, are there to make that unlikely, not impossible.
- A route is one way through the game. It enters every room, uses every
  opening and defeats every enemy, but it cannot try every timing.
- `verify.py` proves that the programs are built byte for byte as in
  the book. After your own changes it will report differences, as it
  should; only playing and testing tell whether a change works.
- The 8580 SID of `run-game.ps1 -Model 8580` was not part of the tests.

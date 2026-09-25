# The chapters and their folders

The book builds the game in eight steps. Each chapter works on one step
of `chain/`; its experiments are in `variants/`, in the folder of the
same step. A variant is the step with one change: a guided variant
shows what a value or a table does, a "Where it breaks" version makes
on purpose a mistake the chapter explains, and its test must fail.

| Chapter | Title | Step | Experiments | Tools |
|---|---|---|---|---|
| 1 | Your workshop | `chain/01-first-room` | | `tools/run-game.ps1`, `tools/check_lines.py` |
| 2 | Memory and the VIC-II | `chain/01-first-room` | `01x-hires` | |
| 3 | The tile engine | `chain/01-first-room` | `01b-more-torches` | `tools/measure_routine.py` |
| 4 | Text, torches and the frame | `chain/01-first-room` | `01a-faster-flames` | |
| 5 | The explorer | `chain/02-explorer` | `02a-faster-explorer`, `02b-quicker-steps`, `02x-missing-jump` | |
| 6 | The dungeon and the HUD | `chain/03-dungeon` | `03a-autumn-moss`, `03b-green-energy`, `03x-high-byte` | |
| 7 | Objects, doors and the portal | `chain/04-objects-doors` | `04a-generous-potion`, `04b-richer-treasures`, `04x-key-kept` | |
| 8 | The enemies | `chain/05-combat` | `05b-lazy-bats` | |
| 9 | The blade and the damage | `chain/05-combat` | `05a-gentler-damage`, `05x-no-floor` | |
| 10 | The SID and the music | `chain/06-sound` | `06a-effects-first`, `06b-faster-music` | |
| 11 | Effects and sound modes | `chain/06-sound` | `06x-stuck-note` | `tools/measure_routine.py`, `tools/sid_writes.py` |
| 12 | States, title and end screens | `chain/07-title-and-ends` | `07a-another-name`, `07b-shorter-wait`, `07x-held-stick` | |
| 13 | Packing, loading, measuring | `chain/08-complete` | `08x-first-block` | `tools/memory_map.py`, `tools/load_time.py` |
| 14 | Reading and checking the game | `chain/08-complete`, `game` | | `tests/`, `tools/plan_route.py`, `tools/mutate_steps.py`, `tools/exec_coverage.py`, `tools/measure_routine.py`, `tools/memory_map.py` |
| 15 | Glossary and index | | | |

Step 08 is the complete game, Cryptmorrow 1.0.1, byte for byte; `game/`
holds its master source, from which `tools/make_chain.py` makes the
eight steps.

## The experiments

| Folder | Chapter | Kind | Title | Its test |
|---|---|---|---|---|
| `variants/01-first-room/01x-hires` | 2 | where it breaks | The multicolour bit forgotten | FAIL, as it must |
| `variants/01-first-room/01b-more-torches` | 3 | variant | Two more torches | PASS |
| `variants/01-first-room/01a-faster-flames` | 4 | variant | Faster flames | PASS |
| `variants/02-explorer/02a-faster-explorer` | 5 | variant | A faster explorer | PASS |
| `variants/02-explorer/02b-quicker-steps` | 5 | variant | Quicker steps | PASS |
| `variants/02-explorer/02x-missing-jump` | 5 | where it breaks | A missing jump | FAIL, as it must |
| `variants/03-dungeon/03a-autumn-moss` | 6 | variant | Autumn moss | PASS |
| `variants/03-dungeon/03b-green-energy` | 6 | variant | A green energy bar | PASS |
| `variants/03-dungeon/03x-high-byte` | 6 | where it breaks | A high byte left behind | FAIL, as it must |
| `variants/04-objects-doors/04a-generous-potion` | 7 | variant | A more generous potion | PASS |
| `variants/04-objects-doors/04b-richer-treasures` | 7 | variant | Richer treasures | PASS |
| `variants/04-objects-doors/04x-key-kept` | 7 | where it breaks | A key that is never used up | FAIL, as it must |
| `variants/05-combat/05b-lazy-bats` | 8 | variant | Lazy bats | PASS |
| `variants/05-combat/05a-gentler-damage` | 9 | variant | Gentler damage | PASS |
| `variants/05-combat/05x-no-floor` | 9 | where it breaks | Energy below zero | FAIL, as it must |
| `variants/06-sound/06a-effects-first` | 10 | variant | Start with the sound effects | PASS |
| `variants/06-sound/06b-faster-music` | 10 | variant | Faster music | PASS |
| `variants/06-sound/06x-stuck-note` | 11 | where it breaks | A blade without a sound | FAIL, as it must |
| `variants/07-title-and-ends/07a-another-name` | 12 | variant | Another name on the title | PASS |
| `variants/07-title-and-ends/07b-shorter-wait` | 12 | variant | A shorter wait at the end | PASS |
| `variants/07-title-and-ends/07x-held-stick` | 12 | where it breaks | A stick held into the title | FAIL, as it must |
| `variants/08-complete/08x-first-block` | 13 | where it breaks | The first block left behind | FAIL, as it must |

Every folder has a README: where the change is, the lines before and
after, what you will see, the limits, what else depends on it, how it
was verified and how to restore the step.

## The tools

| File | What it does |
|---|---|
| `tools/run-game.ps1` | Builds a step, a variant or the complete game and starts it in VICE (chapter 1); every folder has a copy |
| `tools/check_lines.py` | Stops the build if a source line is longer than 60 characters, the width of the book's listings |
| `tools/make_chain.py` | Makes the steps of `chain/` from the master source `game/src` and its step tags |
| `tools/make_variants.py`, `tools/variants.py` | Make `variants/` again from the steps and the list of changes. Each folder is made from nothing, so its `evidence/` goes: `--test` runs the tests and writes the reports again (`--plan` first plans the variants' own routes) |
| `tools/plan_route.py` | Plans the joystick routes of the tests with the Python models, from the goals in `tools/route_*.py`; the planned routes are in `tests/routes` and in `tests/verify_game.py` |
| `tools/shoot.py` | Takes a screenshot of a program at a point of a route |
| `tools/measure_routine.py` | Counts the cycles between two labels in VICE |
| `tools/sid_writes.py` | Records what reaches the SID when the sword asks for an effect (chapter 11) |
| `tools/load_time.py` | Times the loading of a program from a 1541 disk image (chapter 13) |
| `tools/memory_map.py` | The memory of the complete game, area by area, and the free gaps |
| `tools/exec_coverage.py` | Which instructions the route of a test runs, and which it never reaches |
| `tools/mutate_steps.py` | Puts one-line defects into copies of steps 01 to 06; each must be stopped by the step's test |

`tests/` holds the tests themselves: `verify_step.py` for steps 01 to
06, `verify_game.py` for steps 07 and 08 and the complete game, the
models they compare with (`step_model.py`, `game_model.py` and the
modules they use), `reference.py`, which draws rooms, HUD and screens
again from the data files, and `vicemon.py`, which drives VICE through
its monitor.

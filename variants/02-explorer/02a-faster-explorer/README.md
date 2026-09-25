# Cryptmorrow, step 02 - variant 02a: A faster explorer

The explorer walks two pixels a frame instead of one.

This folder is step 02 (`chain/02-explorer` in the project) with one change.

## Where

`game/src/hero.asm`, the constant `HERO_SPEED`.

## Before (`game/src/hero.asm`)

```asm
HERO_SPEED   = 1        ; pixels per frame
```

## After

```asm
HERO_SPEED   = 2        ; pixels per frame
```

## What you will see

The explorer crosses the Moss Gate in half the time; walls and pillars still stop it exactly at their edge, because `update_hero` tests the next pixel before each of the `HERO_SPEED` steps.

## Allowed values and limits

1 or 2. From step 03 `world.asm` refuses more (`.cerror HERO_SPEED > WEST_EDGE + 1`): at 3 pixels the explorer could step over the west edge and X would wrap round.

## What else depends on it

The walking frames count frames, not pixels (`WALK_RATE`): the legs move at the same pace.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_step.py --step 2 --root variants/02-explorer/02a-faster-explorer --evidence variants/02-explorer/02a-faster-explorer/evidence --set "hero_model.HERO_SPEED = 2" --script tests/routes/variant_02a.py --no-shows`): every frame compared with the model of the game changed in the same way (`hero_model.HERO_SPEED = 2`). Result: PASS, 463 frames; shown: two pixels in a frame. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/02-explorer`.

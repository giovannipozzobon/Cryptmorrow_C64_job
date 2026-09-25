# Cryptmorrow, step 02 - variant 02b: Quicker steps

The walking frames alternate every 4 frames instead of every 8.

This folder is step 02 (`chain/02-explorer` in the project) with one change.

## Where

`game/src/hero.asm`, the constant `WALK_RATE`, used by `animate_hero`.

## Before (`game/src/hero.asm`)

```asm
WALK_RATE    = 8        ; frames between walk frames
```

## After

```asm
WALK_RATE    = 4        ; frames between walk frames
```

## What you will see

The legs move twice as fast; the explorer does not: its speed is `HERO_SPEED`.

## Allowed values and limits

1 to 255 frames. With 1 the two frames alternate every frame and blur into one.

## What else depends on it

Nothing else.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_step.py --step 2 --root variants/02-explorer/02b-quicker-steps --evidence variants/02-explorer/02b-quicker-steps/evidence --set "hero_model.WALK_RATE = 4"`): every frame compared with the model of the game changed in the same way (`hero_model.WALK_RATE = 4`). Result: PASS, 1117 frames; shown: all eight walking frames. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/02-explorer`.

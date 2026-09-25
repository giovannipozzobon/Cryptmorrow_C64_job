# Cryptmorrow, step 04 - variant 04b: Richer treasures

A treasure is worth 500 points instead of 250.

This folder is step 04 (`chain/04-objects-doors` in the project) with one change.

## Where

`game/src/objects.asm`, the tables `points_low` and `points_middle`: the points of a seal and of a treasure in BCD, two digits a byte.

## Before (`game/src/objects.asm`)

```asm
points_low:     .byte $00, $50  ; seal 1000, treasure 250
```

## After

```asm
points_low:     .byte $00, $00  ; seal 1000, treasure 500
```

### Before (`game/src/objects.asm`)

```asm
points_middle:  .byte $10, $02
```

### After

```asm
points_middle:  .byte $10, $05
```

## What you will see

The won game ends with 7000 points: three seals (3000) and eight treasures (4000).

## Allowed values and limits

Each byte holds two decimal digits, $00 to $99: 500 is $05 $00, not $01 $F4. The score has six digits.

## What else depends on it

The score of the HUD and, from step 07, of the end screen.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_step.py --step 4 --root variants/04-objects-doors/04b-richer-treasures --evidence variants/04-objects-doors/04b-richer-treasures/evidence --set "world_model.POINTS[5] = 500"`): every frame compared with the model of the game changed in the same way (`world_model.POINTS[5] = 500`). Result: PASS, 11545 frames; shown: 7000 points at VICTORY. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/04-objects-doors`.

# Cryptmorrow, step 04 - variant 04a: A more generous potion

A potion gives back four cells of energy instead of two.

This folder is step 04 (`chain/04-objects-doors` in the project) with one change.

## Where

`game/src/objects.asm`, the constant `POTION_ENERGY`.

## Before (`game/src/objects.asm`)

```asm
POTION_ENERGY  = 2      ; cells of the bar per potion
```

## After

```asm
POTION_ENERGY  = 4      ; cells of the bar per potion
```

## What you will see

In step 04 nothing takes energy away, so a potion stays on the floor: the bar is full. The test writes 4 into `energy`; then the potion of the Root Cellar fills the bar again.

## Allowed values and limits

1 to 8: the energy never goes above `ENERGY_MAX` (`use_object` stops it there). A potion stays on the floor while the bar is full.

## What else depends on it

Nothing else in this step; with the combat (step 05) the game becomes easier.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_step.py --step 4 --root variants/04-objects-doors/04a-generous-potion --evidence variants/04-objects-doors/04a-generous-potion/evidence --set "world_model.POTION_ENERGY = 4"`): every frame compared with the model of the game changed in the same way (`world_model.POTION_ENERGY = 4`). Result: PASS, 11545 frames; shown: the potion from four cells to eight. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/04-objects-doors`.

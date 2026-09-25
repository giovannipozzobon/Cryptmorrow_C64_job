# Cryptmorrow, step 05 - variant 05a: Gentler damage

A touch takes one cell of energy instead of two.

This folder is step 05 (`chain/05-combat` in the project) with one change.

## Where

`game/src/combat.asm`, the constant `DAMAGE`, used by `check_contact`.

## Before (`game/src/combat.asm`)

```asm
DAMAGE        = 2       ; cells of energy a touch
```

## After

```asm
DAMAGE        = 1       ; cells of energy a touch
```

## What you will see

The explorer survives eight touches instead of four.

## Allowed values and limits

From 1 up. With 0 no touch ever hurts; with 8 or more one touch always ends the game, because the energy stops at zero.

## What else depends on it

`SAFE_FRAMES` (30 frames of protection after a touch) stays as it is.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_step.py --step 5 --root variants/05-combat/05a-gentler-damage --evidence variants/05-combat/05a-gentler-damage/evidence --set "combat_model.DAMAGE = 1" --script tests/routes/variant_05a.py --no-shows`): every frame compared with the model of the game changed in the same way (`combat_model.DAMAGE = 1`). Result: PASS, 1336 frames; shown: eight touches before GAME OVER. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/05-combat`.

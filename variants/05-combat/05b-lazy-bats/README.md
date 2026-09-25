# Cryptmorrow, step 05 - variant 05b: Lazy bats

A bat wakes only when the explorer comes within 60 pixels across and 45 up or down, instead of 120 and 90.

This folder is step 05 (`chain/05-combat` in the project) with one change.

## Where

`game/src/combat.asm`, the constants `CHASE_X` and `CHASE_Y`, used by `bat_step`, which `update_enemies` calls.

## Before (`game/src/combat.asm`)

```asm
CHASE_X       = 120     ; a bat chases the explorer
```

## After

```asm
CHASE_X       = 60      ; a bat chases the explorer
```

### Before (`game/src/combat.asm`)

```asm
CHASE_Y       = 90      ; inside this distance
```

### After

```asm
CHASE_Y       = 45      ; inside this distance
```

## What you will see

In the Root Cellar the bat stays still while the explorer stands 66 pixels away; closer, it wakes and comes.

## Allowed values and limits

1 to 254: `measure` gives 255 for any distance it cannot hold in a byte. Two values, one idea: the box around the bat.

## What else depends on it

Only bats; skeletons patrol whatever the distance.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_step.py --step 5 --root variants/05-combat/05b-lazy-bats --evidence variants/05-combat/05b-lazy-bats/evidence --set "combat_model.CHASE_X = 60" --set "combat_model.CHASE_Y = 45" --script tests/routes/variant_05b.py --no-shows`): every frame compared with the model of the game changed in the same way (`combat_model.CHASE_X = 60`, `combat_model.CHASE_Y = 45`). Result: PASS, 488 frames; shown: the bat still at 66 pixels. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/05-combat`.

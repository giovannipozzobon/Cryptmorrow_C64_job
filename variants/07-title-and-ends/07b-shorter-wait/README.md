# Cryptmorrow, step 07 - variant 07b: A shorter wait at the end

Fire counts on the end screen after one second instead of two.

This folder is step 07 (`chain/07-title-and-ends` in the project) with one change.

## Where

`game/src/screens.asm`, the constant `END_DELAY`.

## Before (`game/src/screens.asm`)

```asm
END_DELAY     = 100     ; two seconds before Fire counts
```

## After

```asm
END_DELAY     = 50      ; one second before Fire counts
```

## What you will see

PRESS FIRE appears one second after the end screen.

## Allowed values and limits

1 to 255 frames. Too short, and a player still hammering Fire from the last fight leaves the end screen before reading it: after the wait, one press and one release are enough.

## What else depends on it

Nothing else.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_game.py --step 7 --root variants/07-title-and-ends/07b-shorter-wait --evidence variants/07-title-and-ends/07b-shorter-wait/evidence --set "game_model.END_DELAY = 50" --script tests/routes/variant_07b.py`): every frame compared with the model of the game changed in the same way (`game_model.END_DELAY = 50`). Result: PASS, 19891 frames; shown: the complete route, replanned. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/07-title-and-ends`.

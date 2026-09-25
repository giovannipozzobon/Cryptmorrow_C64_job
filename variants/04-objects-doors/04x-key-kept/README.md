# Cryptmorrow, step 04 - where it breaks: A key that is never used up

`ora` instead of `eor` when a door opens: the key stays.

This folder is step 04 (`chain/04-objects-doors` in the project) with a mistake made on purpose.

## Before (`game/src/objects.asm`)

```asm
        eor key_set             ; the key is used up
```

## After

```asm
        ora key_set             ; the key is used up
```

## Symptom

Door A opens and the HUD still shows the key.

## Cause

The key's bit is set: `eor` clears it, `ora` leaves it set.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How the test catches it

`python tests/verify_step.py --step 4 --root variants/04-objects-doors/04x-key-kept --evidence variants/04-objects-doors/04x-key-kept/evidence` stops: "Step verification FAILED: game 1, Frame 3905: game state {'room': 4, 'energy': 8, 'key_set': 1, 'seals': 0, 'score': 750, 'doors_open': 1, 'taken': {0, 2, 3, 7}, 'ended': 0} != model {'room': 4, 'energy': 8, 'key_set': 0, 'seals': 0, 'score': 750, 'doors_open': 1, 'taken': {0, 2, 3, 7}, 'ended': 0}".

Picture: `evidence/04x-key-kept.png`, after 3933 frames of the step's route.

## Repair

Put back the lines of *Before*, or start again from `chain/04-objects-doors`.

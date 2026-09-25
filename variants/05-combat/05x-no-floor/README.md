# Cryptmorrow, step 05 - where it breaks: Energy below zero

Without `lda #0` the subtraction wraps: one cell minus two is 255.

This folder is step 05 (`chain/05-combat` in the project) with a mistake made on purpose.

## Before (`game/src/combat.asm`)

```asm
        lda #0                  ; not below zero
```

## After

```asm
        nop                     ; not below zero
```

## Symptom

With one cell left a touch fills the bar, and the game that should be over goes on.

## Cause

Energy is one unsigned byte: 1 - 2 = 255 with the carry clear; `bcs` skips the fix only when there was enough.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How the test catches it

`python tests/verify_step.py --step 5 --root variants/05-combat/05x-no-floor --evidence variants/05-combat/05x-no-floor/evidence` stops: "Step verification FAILED: game 3, Frame 658: explorer hidden".

Picture: `evidence/05x-no-floor.png`, after 17486 frames of the step's route.

## Repair

Put back the lines of *Before*, or start again from `chain/05-combat`.

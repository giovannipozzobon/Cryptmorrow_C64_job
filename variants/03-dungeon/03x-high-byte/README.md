# Cryptmorrow, step 03 - where it breaks: A high byte left behind

`exit_east` sets the low byte of X and forgets the high one: X is a 16-bit number on a 320-pixel screen.

This folder is step 03 (`chain/03-dungeon` in the project) with a mistake made on purpose.

## Before (`game/src/world.asm`)

```asm
        lda #0
        sta hero_x+1
        lda #1                  ; a room right
```

## After

```asm
        lda #1                  ; a room right
```

## Symptom

Through an opening to the east the explorer appears near the east wall of the next room, not by the opening it came through, and walks on towards the next exit.

## Cause

The explorer left at X 295 or more, so `hero_x+1` is 1; the new low byte, 9, makes X = 256 + 9 = 265.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How the test catches it

`python tests/verify_step.py --step 3 --root variants/03-dungeon/03x-high-byte --evidence variants/03-dungeon/03x-high-byte/evidence` stops: "Step verification FAILED: game 1, Frame 1221: C64 {'x': 265, 'y': 88, 'dir': 3, 'moving': 1, 'frame': 0, 'timer': 6, 'pointer': 6} != model {'x': 9, 'y': 88, 'dir': 3, 'moving': 1, 'frame': 0, 'timer': 6, 'pointer': 6}".

Picture: `evidence/03x-high-byte.png`, after 1225 frames of the step's route.

## Repair

Put back the lines of *Before*, or start again from `chain/03-dungeon`.

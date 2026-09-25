# Cryptmorrow, step 02 - where it breaks: A missing jump

Without `jmp try_move` after the left direction the code falls into the right one: left walks right.

This folder is step 02 (`chain/02-explorer` in the project) with a mistake made on purpose.

## Before (`game/src/hero.asm`)

```asm
        lda #DIR_LEFT
        sta hero_dir
        jmp try_move
go_right:
```

## After

```asm
        lda #DIR_LEFT
        sta hero_dir
go_right:
```

## Symptom

Pushed left, the explorer turns and walks right.

## Cause

Assembly has no `else`: after the left branch the processor goes on with the next instruction, which stores DIR_RIGHT.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How the test catches it

`python tests/verify_step.py --step 2 --root variants/02-explorer/02x-missing-jump --evidence variants/02-explorer/02x-missing-jump/evidence` stops: "Step verification FAILED: game 1, Frame 18: C64 {'x': 149, 'y': 111, 'dir': 3, 'moving': 1, 'frame': 0, 'timer': 1, 'pointer': 6} != model {'x': 147, 'y': 111, 'dir': 2, 'moving': 1, 'frame': 0, 'timer': 1, 'pointer': 4}".

Picture: `evidence/02x-missing-jump.png`, after 136 frames of the step's route.

## Repair

Put back the lines of *Before*, or start again from `chain/02-explorer`.

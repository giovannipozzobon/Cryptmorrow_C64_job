# Cryptmorrow, step 08 - where it breaks: The first block left behind

`bne` instead of `bcs` in unpack: the loop stops before the first block.

This folder is step 08 (`chain/08-complete` in the project) with a mistake made on purpose.

## Before (`game/src/unpack.asm`)

```asm
        bcs unpack_block        ; until below the first
```

## After

```asm
        bne unpack_block        ; until below the first
```

## Symptom

The explorer's sprite on the title is made of the packed bytes that happen to be at $4000.

## Cause

X counts 6 bytes a block down to 0: `bne` leaves when X becomes 0, before copying block 0; `bcs` goes on until the subtraction borrows.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How the test catches it

`python tests/verify_game.py --step 8 --root variants/08-complete/08x-first-block --evidence variants/08-complete/08x-first-block/evidence` stops: "Game verification FAILED: After the start: block 0x4000 not in place".

Picture: `evidence/08x-first-block.png`, after 16 frames of the step's route.

## Repair

Put back the lines of *Before*, or start again from `chain/08-complete`.

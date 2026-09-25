# Cryptmorrow, step 01 - where it breaks: The multicolour bit forgotten

`$08` instead of `$18` in $D016: the VIC shows the multicolour bitmap as a high-resolution one.

This folder is step 01 (`chain/01-first-room` in the project) with a mistake made on purpose.

## Before (`game/src/main.asm`)

```asm
        lda #$18                ; multicolour, 40 columns
```

## After

```asm
        lda #$08                ; multicolour, 40 columns
```

## Symptom

The Moss Gate in thin coloured stripes: every pair of bits is read as two pixels, and the colours come from screen RAM only.

## Cause

Bit 4 of $D016 switches multicolour mode on. The bitmap, screen RAM and Color RAM are all right: only the way the VIC reads them is wrong.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How the test catches it

`python tests/verify_step.py --step 1 --root variants/01-first-room/01x-hires --evidence variants/01-first-room/01x-hires/evidence` stops: "Step verification FAILED: VIC set up as {'$d011': 59, '$d016': 8, '$d018': 24, 'bank': 2}, not {'$d011': 59, '$d016': 24, '$d018': 24, 'bank': 2}".

Picture: `evidence/01x-hires.png`, after 64 frames of the step's route.

## Repair

Put back the lines of *Before*, or start again from `chain/01-first-room`.

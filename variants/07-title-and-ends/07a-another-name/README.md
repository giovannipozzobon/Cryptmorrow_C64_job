# Cryptmorrow, step 07 - variant 07a: Another name on the title

The big letters of the title spell BONE CRYPT.

This folder is step 07 (`chain/07-title-and-ends` in the project) with one change.

## Where

`game/src/screens.asm`, `logo_text`: column, row, style and the letters.

## Before (`game/src/screens.asm`)

```asm
        .byte 4, 1, STYLE_LOGO
        .text "CRYPTMORROW"
```

## After

```asm
        .byte 5, 1, STYLE_LOGO
        .text "BONE CRYPT"
```

## What you will see

BONE CRYPT in the big letters, centred: ten characters, each 3 cells wide, from column 5.

## Allowed values and limits

Capital letters and spaces (the big font has A to Z); at most 13 characters in 40 columns; the column is (40 - 3 x characters) / 2.

## What else depends on it

Nothing else; the game keeps its name everywhere else.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_game.py --step 7 --root variants/07-title-and-ends/07a-another-name --evidence variants/07-title-and-ends/07a-another-name/evidence`): every frame compared with the model of the game changed in the same way (no change to the model). Result: PASS, 20081 frames; shown: the title as the reference. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/07-title-and-ends`.

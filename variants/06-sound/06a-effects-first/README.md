# Cryptmorrow, step 06 - variant 06a: Start with the sound effects

The program starts in SOUND FX mode instead of MUSIC.

This folder is step 06 (`chain/06-sound` in the project) with one change.

## Where

`game/src/main.asm`, the constant `START_MODE`.

## Before (`game/src/main.asm`)

```asm
START_MODE  = MODE_MUSIC  ; or MODE_FX, MODE_SILENT
```

## After

```asm
START_MODE  = MODE_FX     ; or MODE_MUSIC, MODE_SILENT
```

## What you will see

No theme: the blade, the hits and the dust have their sounds on voice 1.

## Allowed values and limits

`MODE_MUSIC`, `MODE_FX` or `MODE_SILENT`. In step 07 the menu of the title chooses and `START_MODE` goes.

## What else depends on it

Nothing else: `start_audio` sets the mode it finds in `audio_mode`.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_step.py --step 6 --root variants/06-sound/06a-effects-first --evidence variants/06-sound/06a-effects-first/evidence --script tests/routes/variant_06a.py --no-shows`): every frame compared with the model of the game changed in the same way (no change to the model). Result: PASS, 362 frames; shown: effects only. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/06-sound`.

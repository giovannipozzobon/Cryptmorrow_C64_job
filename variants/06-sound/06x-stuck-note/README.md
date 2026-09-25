# Cryptmorrow, step 06 - where it breaks: A blade without a sound

Without `inc fx_pos` every sound effect stays on its first frame, the one with the gate off: the effects fall silent.

This folder is step 06 (`chain/06-sound` in the project) with a mistake made on purpose.

## Before (`game/src/player.asm`)

```asm
        inc fx_pos
```

## After

```asm
        nop
```

## Symptom

In SOUND FX mode the first blow of the sword makes no sound, and from then on no effect is heard.

## Cause

`fx_pos` never reaches the end mark of the effect, so the interrupt plays the same step every frame: the first one, whose gate is off. `fx_prio` stays set, so every later effect is accepted and stays on its own first step too.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How the test catches it

`python tests/verify_step.py --step 6 --root variants/06-sound/06x-stuck-note --evidence variants/06-sound/06x-stuck-note/evidence` stops: "Step verification FAILED: game 2, Frame 119: sound state differs from the model (C64, model): {'fx_pos': (1, 2)}".

## Repair

Put back the lines of *Before*, or start again from `chain/06-sound`.

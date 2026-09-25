# Cryptmorrow, step 07 - where it breaks: A stick held into the title

`show_title` forgets the stick already pushed: the menu moves by itself.

This folder is step 07 (`chain/07-title-and-ends` in the project) with a mistake made on purpose.

## Before (`game/src/screens.asm`)

```asm
        lda joy_state           ; a stick already pushed
```

## After

```asm
        lda #0                  ; a stick already pushed
```

## Symptom

Coming back to the title with the stick held down, the cursor moves down a line by itself (from MUSIC to SOUND FX), the theme stops and the pickup sounds.

## Cause

`stick_held` is 0, so the push the player has been holding looks new to `title_frame`.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How the test catches it

`python tests/verify_game.py --step 7 --root variants/07-title-and-ends/07x-held-stick --evidence variants/07-title-and-ends/07x-held-stick/evidence` stops: "Game verification FAILED: Frame 20425: state, end_timer, fire_armed, stick_held (0, 0, 0, 0) != model (0, 0, 0, 2)".

Picture: `evidence/07x-held-stick.png`, after 17264 frames of the step's route.

## Repair

Put back the lines of *Before*, or start again from `chain/07-title-and-ends`.

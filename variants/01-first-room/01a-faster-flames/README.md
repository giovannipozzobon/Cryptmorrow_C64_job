# Cryptmorrow, step 01 - variant 01a: Faster flames

The torches flicker twice as fast: a new flame every 4 frames instead of every 8.

This folder is step 01 (`chain/01-first-room` in the project) with one change.

## Where

`game/src/main.asm`, at `frame_end`: the mask that picks the frames that animate, and the shifts that turn the frame count into the flame phase.

## Before (`game/src/main.asm`)

```asm
        and #7
        bne frame_done
        lda frame_count         ; phase = frame / 8 mod 4
        lsr a
        lsr a
        lsr a
        and #3
```

## After

```asm
        and #3
        bne frame_done
        lda frame_count         ; phase = frame / 4 mod 4
        lsr a
        lsr a
        and #3
```

## What you will see

Every torch changes its flame every 4 frames, 12.5 times a second on a PAL machine; the four flames still come in the same order.

## Allowed values and limits

Mask and shifts go together: `and #1` with one `lsr a` (every 2 frames), `and #3` with two, `and #7` with three, `and #15` with four. The final `and #3` stays: there are four flames in `FLAMES`. Change only the mask and nothing visible happens (the phase still moves every 8 frames).

## What else depends on it

Nothing else: `animate_torches` draws whatever phase it is given. The test's model has the same period (`FLAME_SHIFT`).

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_step.py --step 1 --root variants/01-first-room/01a-faster-flames --evidence variants/01-first-room/01a-faster-flames/evidence --set "step_model.FLAME_SHIFT = 2"`): every frame compared with the model of the game changed in the same way (`step_model.FLAME_SHIFT = 2`). Result: PASS, 514 frames; shown: the four flames every 4 frames. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/01-first-room`.

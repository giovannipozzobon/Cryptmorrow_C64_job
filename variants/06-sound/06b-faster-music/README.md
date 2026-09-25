# Cryptmorrow, step 06 - variant 06b: Faster music

The theme and the pieces of the end at 150 beats a minute instead of 125.

This folder is step 06 (`chain/06-sound` in the project) with one change.

## Where

`game/assets/score.py`, `SPEED`: frames per sixteenth note; the asset builder writes it into `music.asm` as `MUSIC_SPEED`.

## Before (`game/assets/score.py`)

```python
SPEED = 6            # frames per step: 50 / 6 * 60 / 4 = 125 BPM (PAL)
```

## After

```python
SPEED = 5            # frames per step: 50 / 5 * 60 / 4 = 150 BPM (PAL)
```

## What you will see

The same notes, quicker; the piece of GAME OVER ends sooner and then every note is released.

## Allowed values and limits

Above `GATE_TICK`, 4: the gate is released on frame 4 of the last step of a note, and with 4 frames a step or fewer that frame never comes, so repeated notes no longer attack; lower `GATE_TICK` with it for very fast music. 12 is slow. Envelopes and vibrato do not change.

## What else depends on it

Only the music: the game counts its own frames.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_step.py --step 6 --root variants/06-sound/06b-faster-music --evidence variants/06-sound/06b-faster-music/evidence --script tests/routes/variant_06b.py --no-shows`): every frame compared with the model of the game changed in the same way (no change to the model). Result: PASS, 1455 frames; shown: theme and piece of GAME OVER, then silence. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/06-sound`.

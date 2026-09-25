# Cryptmorrow, step 03 - variant 03a: Autumn moss

The atrium in other colours: the moss turns orange and yellow, with the same pixels.

This folder is step 03 (`chain/03-dungeon` in the project) with one change.

## Where

`game/assets/tiles.py`, `ZONE_PALETTES`: each zone maps the catalogue's colours to its own; the atrium, `atrio` in the code, kept them all.

## Before (`game/assets/tiles.py`)

```python
    "atrio": {},                                # moss green, unchanged
```

## After

```python
    "atrio": {GREEN: ORANGE, LIGHT_GREEN: YELLOW},  # autumn moss
```

## What you will see

The seven rooms of the atrium with orange and yellow moss; `set_zone` copies the atrium's tables as before, only their bytes have changed.

## Allowed values and limits

Any of the 16 colours, per colour of the catalogue. Colours not listed stay. Keep the floor and the walls apart, or the explorer will not stand out.

## What else depends on it

Only `zones.color` changes; the asset builder writes it again (`run-game.ps1` does).

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_step.py --step 3 --root variants/03-dungeon/03a-autumn-moss --evidence variants/03-dungeon/03a-autumn-moss/evidence`): every frame compared with the model of the game changed in the same way (no change to the model). Result: PASS, 3039 frames; shown: the rooms as the reference with the new tables. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/03-dungeon`.

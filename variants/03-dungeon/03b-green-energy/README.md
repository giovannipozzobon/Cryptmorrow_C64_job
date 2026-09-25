# Cryptmorrow, step 03 - variant 03b: A green energy bar

The cells of energy left are light green instead of light red.

This folder is step 03 (`chain/03-dungeon` in the project) with one change.

## Where

`game/src/hud.asm`: the colour of the bar in `hud_frame` (printed once) and in `hud_update` (every change).

## Before (`game/src/hud.asm`)

```asm
        .byte BAR_COLUMN, HUD_ROW, LIGHT_RED
```

## After

```asm
        .byte BAR_COLUMN, HUD_ROW, LIGHT_GREEN
```

### Before (`game/src/hud.asm`)

```asm
        lda #LIGHT_RED << 4
```

### After

```asm
        lda #LIGHT_GREEN << 4
```

## What you will see

Eight light green cells after ENERGY.

## Allowed values and limits

One colour in two places: `hud_update` repaints the bar in the same call as `hud_frame`, so changing only `hud_frame` changes nothing, and changing only `hud_update` changes the whole bar at once. Keep it far from dark grey, the colour of the cells lost.

## What else depends on it

Nothing else. (A constant for the colour would keep the two places together: a challenge for the reader.)

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_step.py --step 3 --root variants/03-dungeon/03b-green-energy --evidence variants/03-dungeon/03b-green-energy/evidence --set "reference.FULL = 13"`): every frame compared with the model of the game changed in the same way (`reference.FULL = 13`). Result: PASS, 3039 frames; shown: the HUD as the reference, bar in light green. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/03-dungeon`.

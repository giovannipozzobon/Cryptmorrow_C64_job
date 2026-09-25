# Cryptmorrow, step 01 - variant 01b: Two more torches

The Moss Gate is data: two more torch tiles in its map and the room has six burning torches.

This folder is step 01 (`chain/01-first-room` in the project) with one change.

## Where

`game/assets/rooms/moss_gate.txt`, the second row of the map: `T` is a wall torch with its flame on the left, `t` on the right.

## Before (`game/assets/rooms/moss_gate.txt`)

```text
#####T###GG###t#####
```

## After

```text
###T#T###GG###t#t###
```

## What you will see

Six torches along the north wall and on the sides, all burning; `draw_room` finds them while it draws and puts them in its list, the main loop animates the list.

## Allowed values and limits

A torch needs floor below it. At most six torches a room (`MAX_TORCHES` in `room.asm`): the asset builder refuses a seventh; in the engine it would keep the flame painted in its tile and never move. The asset builder checks the map and the number of metatiles (128 at most; this map needs no new one).

## What else depends on it

The same room is the start of the game in every later step; nothing else changes.

## Try it

`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds this folder and starts it in VICE.

## How it was verified

Assembled with 64tass and run in VICE by the project's test (`python tests/verify_step.py --step 1 --root variants/01-first-room/01b-more-torches --evidence variants/01-first-room/01b-more-torches/evidence`): every frame compared with the model of the game changed in the same way (no change to the model). Result: PASS, 514 frames; shown: six torches listed at the start. Report in `evidence/`.

## Restore

Put back the lines of *Before*, or start again from `chain/01-first-room`.

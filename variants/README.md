# Cryptmorrow - guided variants and "where it breaks"

Each folder is a step of the chain (`chain/NN-name` in the project) with one change: a guided variant to try, or a mistake made on purpose. Its README says where, before and after, what you will see, the limits, how it was verified and how to restore. `tools/run-game.ps1 -Mode Play` in a folder builds it and starts it in VICE.

| Step | Folder | Kind | What it shows | Verified |
|---|---|---|---|---|
| 01 | `01-first-room/01a-faster-flames` | variant | The torches flicker twice as fast: a new flame every 4 frames instead of every 8. | yes |
| 01 | `01-first-room/01b-more-torches` | variant | The Moss Gate is data: two more torch tiles in its map and the room has six burning torches. | yes |
| 02 | `02-explorer/02a-faster-explorer` | variant | The explorer walks two pixels a frame instead of one. | yes |
| 02 | `02-explorer/02b-quicker-steps` | variant | The walking frames alternate every 4 frames instead of every 8. | yes |
| 03 | `03-dungeon/03a-autumn-moss` | variant | The atrium in other colours: the moss turns orange and yellow, with the same pixels. | yes |
| 03 | `03-dungeon/03b-green-energy` | variant | The cells of energy left are light green instead of light red. | yes |
| 04 | `04-objects-doors/04a-generous-potion` | variant | A potion gives back four cells of energy instead of two. | yes |
| 04 | `04-objects-doors/04b-richer-treasures` | variant | A treasure is worth 500 points instead of 250. | yes |
| 05 | `05-combat/05a-gentler-damage` | variant | A touch takes one cell of energy instead of two. | yes |
| 05 | `05-combat/05b-lazy-bats` | variant | A bat wakes only when the explorer comes within 60 pixels across and 45 up or down, instead of 120 and 90. | yes |
| 06 | `06-sound/06a-effects-first` | variant | The program starts in SOUND FX mode instead of MUSIC. | yes |
| 06 | `06-sound/06b-faster-music` | variant | The theme and the pieces of the end at 150 beats a minute instead of 125. | yes |
| 07 | `07-title-and-ends/07a-another-name` | variant | The big letters of the title spell BONE CRYPT. | yes |
| 07 | `07-title-and-ends/07b-shorter-wait` | variant | Fire counts on the end screen after one second instead of two. | yes |
| 01 | `01-first-room/01x-hires` | where it breaks | `$08` instead of `$18` in $D016: the VIC shows the multicolour bitmap as a high-resolution one. | yes |
| 02 | `02-explorer/02x-missing-jump` | where it breaks | Without `jmp try_move` after the left direction the code falls into the right one: left walks right. | yes |
| 03 | `03-dungeon/03x-high-byte` | where it breaks | `exit_east` sets the low byte of X and forgets the high one: X is a 16-bit number on a 320-pixel screen. | yes |
| 04 | `04-objects-doors/04x-key-kept` | where it breaks | `ora` instead of `eor` when a door opens: the key stays. | yes |
| 05 | `05-combat/05x-no-floor` | where it breaks | Without `lda #0` the subtraction wraps: one cell minus two is 255. | yes |
| 06 | `06-sound/06x-stuck-note` | where it breaks | Without `inc fx_pos` every sound effect stays on its first frame, the one with the gate off: the effects fall silent. | yes |
| 07 | `07-title-and-ends/07x-held-stick` | where it breaks | `show_title` forgets the stick already pushed: the menu moves by itself. | yes |
| 08 | `08-complete/08x-first-block` | where it breaks | `bne` instead of `bcs` in unpack: the loop stops before the first block. | yes |

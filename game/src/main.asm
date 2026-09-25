;|; CRYPTMORROW 01 - the first room, PAL C64. {1-1}
;|; The Moss Gate drawn by the tile engine in the {1-1}
;|; multicolour bitmap: metatiles, walls, the name of {1-1}
;|; the room and its burning torches. {1-1}
;|; CRYPTMORROW 02 - the explorer, PAL C64. {2-2}
;|; The Moss Gate with the explorer: joystick in port 2, {2-2}
;|; four directions, two walking frames each, walls and {2-2}
;|; pillars that stop it. {2-2}
;|; CRYPTMORROW 03 - the dungeon, PAL C64. {3-3}
;|; Sixteen rooms in four zones, joined by openings, each {3-3}
;|; in the colours of its zone; the HUD with energy, {3-3}
;|; keys, seals and score. {3-3}
;|; CRYPTMORROW 04 - objects and doors, PAL C64. {4-4}
;|; Keys, treasures, potions and seals; three locked {4-4}
;|; doors and the portal: out through it, VICTORY. {4-4}
;|; CRYPTMORROW 05 - combat, PAL C64. {5-5}
;|; The sword, skeletons and bats, energy and damage: {5-5}
;|; GAME OVER when the energy is gone. {5-5}
;|; CRYPTMORROW 06 - sound, PAL C64. {6-6}
;|; The SID theme, the pieces of the end and eight sound {6-6}
;|; effects, played by a raster interrupt; START_MODE {6-6}
;|; chooses MUSIC, SOUND FX or SILENT. {6-6}
;|; CRYPTMORROW 07 - title and end screens, PAL C64. {7-7}
; CRYPTMORROW 08 - the complete game, PAL C64. {8}
; A title with its menu (MUSIC, SOUND FX, SILENT) and {7}
; PRESS FIRE; sixteen rooms in four zones; three keys, {7}
; three doors, three seals and the portal; skeletons and {7}
; bats; a sword; energy and damage; end screens for {7}
; GAME OVER and VICTORY with the score. The SID theme, {7}
; the pieces of the end and the sound effects play in a {7}
; raster interrupt. {7}
; The data are packed behind the code and unpacked at {8}
; the start. {8}
; Assemble this file: it includes the others.
        .cpu "6502"
        .include "memory.asm"
        .include "../assets/generated/dungeon.asm"
;|START_MODE  = MODE_MUSIC  ; or MODE_FX, MODE_SILENT {6-6}

        * = $0801
        .word basic_end         ; BASIC line: 10 SYS 2061
        .word 10
        .byte $9e
        .text "2061"
        .byte 0
basic_end:
        .word 0

entry:
        sei                     ; no KERNAL interrupts {8}
        jsr unpack              ; the data to their places {8}
; The program proper. unpack runs once: the data blocks {8}
; overwrite part of their sources. The test starts again {8}
; from here. {8}
start:                          ; {8}
        sei
        cld
        ldx #$ff                ; fresh stack
        txs
        lda #$2f
        sta $00
        lda #$36                ; RAM at $a000, I/O, KERNAL
        sta $01
        lda #$7f                ; no CIA interrupts
        sta $dc0d
        sta $dd0d
        lda $dc0d
        lda $dd0d
        lda #0
        sta $d01a               ; no VIC interrupts
        sta $d015
        sta $d020
        sta $d021
        sta $d418               ; {6}
        sta frame_count
        sta frame_count+1
        sta torch_phase
        sta joy_state           ; {2}
        sta fire_held           ; {5}
        lda #$ff                ; no colour tables yet
        sta colour_zone
        lda #$0f
        sta $d019
        lda #$0b                ; display off while drawing
        sta $d011

        lda $dd02
        ora #3
        sta $dd02
        lda $dd00
        and #$fc
        ora #2                  ; VIC bank $4000-$7fff
        sta $dd00
        lda #$18                ; screen $4400, bitmap $6000
        sta $d018
        lda #$18                ; multicolour, 40 columns
        sta $d016
        lda #$ff                ; CIA1 port A: inputs, so {2}
        sta $dc00               ; joystick 2 reads directly {2}
        lda #0                  ; {2}
        sta $dc02               ; {2}

        lda #MODE_MUSIC         ; the menu starts on MUSIC {7}
;|        lda #START_MODE {6-6}
        sta audio_mode          ; {6}
        jsr start_audio         ; interrupts on from here {6}
        jsr show_title          ; {7}
;|        jsr clear_screen        ; a game in the start room {1-6}
;|        jsr init_game {1-6}
;|        jsr print_hud {3-6}
;|        jsr init_hero {2-6}
;|        jsr enter_room          ; drawn, then shown {1-6}

main_loop:
        jsr wait_frame
frame_tick:
        inc frame_count
        bne count_ready
        inc frame_count+1
count_ready:
        jsr read_joystick       ; {2}
        jsr run_state           ; title, game or end {7}
;|        lda game_ended          ; after the end the {4-6}
;|        bne frame_end           ; room stands still {4-6}
;|        jsr play_frame {2-6}
frame_end:
        lda frame_count
        and #7
        bne frame_done
        lda frame_count         ; phase = frame / 8 mod 4
        lsr a
        lsr a
        lsr a
        and #3
        sta torch_phase
        jsr animate_torches
frame_done:
        jmp main_loop

;{2}
; --- play_frame ----------------------------------------
;|; One frame of the game. {2-6}
; One frame of the game, from STATE_PLAY. {7}
play_frame:
        jsr check_fire          ; may start a blow {5}
        jsr update_hero
        jsr check_exits         ; may draw another room {3}
        jsr check_door          ; {4}
        jsr check_objects       ; {4}
        jsr update_enemies      ; {5}
        jsr check_blade         ; {5}
        jsr check_contact       ; may end the game {5}
        jsr animate_hero
        jsr place_hero
        jsr show_combat         ; {5}
        lda hud_dirty           ; {4}
        beq hud_ready           ; {4}
        jsr hud_update          ; {4}
hud_ready:                      ; {4}
        rts

;{}
; --- wait_frame ----------------------------------------
; Waits for the PAL lower border, then its next edge,
; using the raster's ninth bit in D011.
wait_frame:
wait_lower:
        bit $d011
        bpl wait_lower
wait_upper:
        bit $d011
        bmi wait_upper
        rts

        .include "hero.asm"     ; {2}
        .include "room.asm"
        .include "text.asm"
        .include "hud.asm"      ; {3}
        .include "world.asm"
        .include "objects.asm"  ; {4}
        .include "combat.asm"   ; {4}
        .include "screens.asm"  ; {7}
        .include "player.asm"   ; {6}
        .include "unpack.asm"   ; {8}

frame_count: .word 0
torch_phase: .byte 0
code_end:
        .cerror code_end > SPRITE_DATA, "code too long" ; {2}
;|        .cerror code_end > $4000, "code too long" {1-1}

        .include "data.asm"

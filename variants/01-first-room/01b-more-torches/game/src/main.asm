; CRYPTMORROW 01 - the first room, PAL C64.
; The Moss Gate drawn by the tile engine in the
; multicolour bitmap: metatiles, walls, the name of
; the room and its burning torches.
; Assemble this file: it includes the others.
        .cpu "6502"
        .include "memory.asm"
        .include "../assets/generated/dungeon.asm"

        * = $0801
        .word basic_end         ; BASIC line: 10 SYS 2061
        .word 10
        .byte $9e
        .text "2061"
        .byte 0
basic_end:
        .word 0

entry:
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
        sta frame_count
        sta frame_count+1
        sta torch_phase
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

        jsr clear_screen        ; a game in the start room
        jsr init_game
        jsr enter_room          ; drawn, then shown

main_loop:
        jsr wait_frame
frame_tick:
        inc frame_count
        bne count_ready
        inc frame_count+1
count_ready:
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

        .include "room.asm"
        .include "text.asm"
        .include "world.asm"

frame_count: .word 0
torch_phase: .byte 0
code_end:
        .cerror code_end > $4000, "code too long"

        .include "data.asm"

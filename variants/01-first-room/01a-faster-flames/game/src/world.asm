; CRYPTMORROW - the rooms: each in its own page from
; ROOM_DATA, drawn in the colours of its zone. Also
; the state of a game.

; --- init_game -----------------------------------------
; The state of a new game: the start room.
init_game:
        lda #START_ROOM
        sta room_slot
        rts

; --- enter_room ----------------------------------------
; Draws room room_slot with the display off, then shows
; it from the top of a frame, so no half picture.
enter_room:
        lda #$0b                ; display off
        sta $d011
room_blank:
        jsr room_address
        jsr set_zone            ; colours of the zone
        jsr draw_room
room_drawn:
        jsr animate_torches     ; flames in step at once
        jsr wait_frame
        lda #$3b                ; display on
        sta $d011
room_shown:
        rts

; --- room_address --------------------------------------
; room_ptr = page_ptr = ROOM_DATA + room_slot * 256.
; draw_room uses up room_ptr; page_ptr stays.
room_address:
        lda #0
        sta room_ptr
        sta page_ptr
        lda room_slot
        clc
        adc #>ROOM_DATA
        sta room_ptr+1
        sta page_ptr+1
        rts

; --- set_zone ------------------------------------------
; The colour tables of the catalog (TILE_SCR_L to
; TILE_COL_R, 1 KB) for the zone of room page_ptr: a
; copy from ZONE_COLOURS, only when the zone changes.
; The bitmaps of the tiles are the same in every zone.
        .cerror TILE_COL_R != TILE_SCR_L + $300, "tables"
set_zone:
        ldy #ROOM_ZONE
        lda (page_ptr),y
        cmp colour_zone
        beq zone_ready          ; already there
        sta colour_zone
        asl a
        asl a                   ; 4 pages a zone
        clc
        adc #>ZONE_COLOURS
        sta zone_src+1
        lda #>TILE_SCR_L
        sta zone_dst+1
        ldy #0
        sty zone_src
        sty zone_dst
        ldx #4                  ; four tables
zone_copy:
        lda (zone_src),y
        sta (zone_dst),y
        iny
        bne zone_copy
        inc zone_src+1
        inc zone_dst+1
        dex
        bne zone_copy
zone_ready:
        rts

colour_zone: .byte $ff  ; zone of the tables in use

; --- Game state ----------------------------------------
room_slot:  .byte 0     ; row * GRID_WIDTH + column

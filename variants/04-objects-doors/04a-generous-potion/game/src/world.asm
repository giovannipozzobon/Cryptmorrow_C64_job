; CRYPTMORROW - the dungeon: a grid of 4 x 4 rooms, each
; in its own page from ROOM_DATA. Walking through an
; opening draws the next room, with its open door and
; its objects. Also the game state.

GRID_WIDTH   = 4        ; rooms in a row of the grid
ENTRY_MARGIN = 8        ; pixels inside the new room

; A room is left when the hitbox enters the outermost
; ring of cells of the playfield. Walls fill that ring
; except in the openings, so only there can it happen.
; Y <= NORTH_EDGE: hitbox top in cell row 3.
; Y >= SOUTH_EDGE: hitbox bottom in cell row 22.
; X <= WEST_EDGE:  hitbox left in cell column 0.
; X >= EAST_EDGE:  hitbox right in cell column 39.
NORTH_EDGE = FIRST_ROW * 8 + 7 - BOX_TOP
SOUTH_EDGE = (FIRST_ROW + CELL_ROWS - 1) * 8 - BOX_BOTTOM
WEST_EDGE  = 7 - BOX_LEFT
EAST_EDGE  = 39 * 8 - BOX_RIGHT

        .cerror EAST_EDGE < 256, "check_exits: X high byte"
        .cerror HERO_SPEED > WEST_EDGE + 1, "X could wrap"

; --- init_game -----------------------------------------
; The state of a new game: nothing taken, no door open.
init_game:
        lda #START_ROOM
        sta room_slot
        lda #ENERGY_MAX
        sta energy
        lda #0
        sta key_set
        sta seals
        sta doors_open
        sta game_ended
        sta score
        sta score+1
        sta score+2
        ldx #TAKEN_BYTES - 1
clear_taken:
        sta taken,x
        dex
        bpl clear_taken
        rts

; --- check_exits ---------------------------------------
; Called after update_hero: at an edge, the explorer
; moves to the opposite edge of the next room.
check_exits:
        lda hero_y
        cmp #NORTH_EDGE + 1
        bcc exit_north          ; Y <= NORTH_EDGE
        cmp #SOUTH_EDGE
        bcs exit_south          ; Y >= SOUTH_EDGE
        lda hero_x+1
        bne east_half           ; X >= 256
        lda hero_x
        cmp #WEST_EDGE + 1
        bcc exit_west           ; X <= WEST_EDGE
        rts
east_half:
        lda hero_x
        cmp #<EAST_EDGE
        bcs exit_east           ; X >= EAST_EDGE
        rts

exit_north:
        lda room_slot
        cmp #START_ROOM
        bne north_room
        jmp victory             ; out through the portal
north_room:
        lda #SOUTH_EDGE - ENTRY_MARGIN
        sta hero_y
        lda #<-GRID_WIDTH       ; a row up: -4 = $fc
        jmp change_room
exit_south:
        lda #NORTH_EDGE + ENTRY_MARGIN
        sta hero_y
        lda #GRID_WIDTH         ; a row down: +4
        jmp change_room
exit_west:
        lda #<(EAST_EDGE - ENTRY_MARGIN)
        sta hero_x
        lda #>(EAST_EDGE - ENTRY_MARGIN)
        sta hero_x+1
        lda #<-1                ; a room left: $ff
        jmp change_room
exit_east:
        lda #WEST_EDGE + ENTRY_MARGIN
        sta hero_x
        lda #0
        sta hero_x+1
        lda #1                  ; a room right

; --- change_room ---------------------------------------
; A = step in the grid. The asset builder has checked
; that every opening leads to a room.
change_room:
        clc
        adc room_slot
        sta room_slot
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
        jsr show_door           ; open doors stay open
room_drawn:
        jsr animate_torches     ; flames in step at once
        jsr show_objects
        jsr place_hero
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
TAKEN_BYTES = 4         ; one bit per object: 32 objects
        .cerror OBJECT_COUNT > TAKEN_BYTES * 8, "objects"
room_slot:  .byte 0     ; row * GRID_WIDTH + column
energy:     .byte 0     ; 0 to ENERGY_MAX
key_set:    .byte 0     ; keys carried: bit 0 A, 1 B, 2 C
seals:      .byte 0     ; seals found, 0 to 3
doors_open: .byte 0     ; bits 0-2 doors A-C, 3 portal
taken:      .fill TAKEN_BYTES   ; objects picked up
score:      .byte 0, 0, 0   ; BCD, highest digits first
hud_dirty:  .byte 0     ; not 0: hud_update must run

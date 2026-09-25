; CRYPTMORROW - the tile engine: clearing the screen,
; drawing a room from its metatile map, redrawing one
; metatile, the torches.

MAP_WIDTH   = 20        ; metatiles per map row
FIRST_ROW   = 3         ; cell row where the map starts
CELL_ROWS   = 20        ; 10 map rows x 2 cell rows
MAX_TORCHES = 6
TYPE_MASK   = %01110000
TORCH_LEFT  = 1 << 4    ; flame in the top-left cell
TORCH_RIGHT = 2 << 4    ; flame in the top-right cell
TYPE_DOOR   = 4 << 4    ; gate or locked door
WALL_CELL   = 1         ; walkability: solid
DOOR_CELL   = 2         ; walkability: solid, a door
NAME_BITMAP = BITMAP + 24 * 320
NAME_SCREEN = SCREEN + 24 * 40

; --- fill_pages ----------------------------------------
; Stores A in X whole pages from fill_ptr onwards.
fill_pages:
        ldy #0
fill_byte:
        sta (fill_ptr),y
        iny
        bne fill_byte
        inc fill_ptr+1          ; next page
        dex
        bne fill_byte
        rts

; --- clear_screen --------------------------------------
; Black bitmap and colours; every cell solid until a
; room is drawn over it. All four areas start on a
; page boundary, so only the high byte changes.
clear_screen:
        lda #0
        sta fill_ptr
        lda #>BITMAP
        sta fill_ptr+1
        ldx #32                 ; $6000-$7fff
        lda #0
        jsr fill_pages
        lda #>SCREEN
        sta fill_ptr+1
        ldx #4                  ; $4400-$47ff
        lda #0
        jsr fill_pages
        lda #>COLOR_RAM
        sta fill_ptr+1
        ldx #4                  ; $d800-$dbff
        lda #0
        jsr fill_pages
        lda #>SOLID_MAP
        sta fill_ptr+1
        ldx #4                  ; $9800-$9bff
        lda #1
        jmp fill_pages

; --- draw_room -----------------------------------------
; Draws the 20 x 10 map at room_ptr on cell rows 3-22:
; bitmap, screen RAM, Color RAM and walkability map.
; Each map row is read twice: first for the top cells
; of its metatiles, then for the bottom cells. Then
; prints the room name, stored at ROOM_NAME in the same
; page. Call with the display blanked; room_ptr must
; point at the start of a page and is used up.
draw_room:
        lda #0
        sta torch_count
        sta half                ; top cells first
        lda #<(BITMAP + FIRST_ROW * 320)
        sta bmp_ptr
        lda #>(BITMAP + FIRST_ROW * 320)
        sta bmp_ptr+1
        lda #<(SCREEN + FIRST_ROW * 40)
        sta scr_ptr
        lda #>(SCREEN + FIRST_ROW * 40)
        sta scr_ptr+1
        lda #<(COLOR_RAM + FIRST_ROW * 40)
        sta col_ptr
        lda #>(COLOR_RAM + FIRST_ROW * 40)
        sta col_ptr+1
        lda #<(SOLID_MAP + FIRST_ROW * 40)
        sta sol_ptr
        lda #>(SOLID_MAP + FIRST_ROW * 40)
        sta sol_ptr+1
        lda #CELL_ROWS
        sta rows_left

draw_cell_row:
        lda #0
        sta map_col
        sta cell_col

draw_tile:
        ldy map_col
        lda (room_ptr),y        ; metatile id 0-127
        jsr draw_half
        clc                     ; next metatile: 16 bitmap
        lda bmp_ptr             ; bytes further on
        adc #16
        sta bmp_ptr
        bcc same_page
        inc bmp_ptr+1
same_page:
        inc map_col
        lda map_col
        cmp #MAP_WIDTH
        bne draw_tile

; 20 x 16 = 320 bytes: bmp_ptr already points at the
; next cell row. The other pointers move 40 bytes.
        ldx #scr_ptr
        jsr down_one_row
        ldx #col_ptr
        jsr down_one_row
        ldx #sol_ptr
        jsr down_one_row
        lda half
        eor #$80
        sta half
        bne next_cell_row       ; same map row, bottom
        clc                     ; both halves done:
        lda room_ptr            ; next map row
        adc #MAP_WIDTH
        sta room_ptr
        bcc next_cell_row
        inc room_ptr+1
next_cell_row:
        dec rows_left
        beq map_complete
        jmp draw_cell_row
map_complete:
        lda #ROOM_NAME          ; 200 < 256: room_ptr is
        sta text_ptr            ; still in the same page
        lda room_ptr+1
        sta text_ptr+1
        jsr clear_name_row
        jmp print_text

; --- draw_half -----------------------------------------
; Draws half of metatile A: its two top cells if half
; is $00, its two bottom cells if half is $80. Bitmap
; at bmp_ptr; screen RAM, Color RAM and walkability at
; column cell_col of the rows at scr_ptr, col_ptr and
; sol_ptr. Adds 2 to cell_col. A torch tile adds its
; flame cell to the torch list.
draw_half:
        sta tile_id
        tay
        lda TILE_ATTR,y
        sta attr_bits
        tya
        ora half                ; +128 for bottom cells
        tax                     ; X: colour table index

; Bitmap source: TILE_BITMAP + id * 32, plus 16 for the
; bottom cells. id * 32 = id / 8 pages + (id * 32) and 255.
        lda tile_id
        lsr a
        lsr a
        lsr a
        clc
        adc #>TILE_BITMAP
        sta src_ptr+1
        lda tile_id
        asl a
        asl a
        asl a
        asl a
        asl a
        bit half
        bpl source_ready
        ora #16                 ; second half of the tile
source_ready:
        sta src_ptr

; Two cells side by side are 16 consecutive bytes. The
; copy is written out 16 times (.for repeats the three
; lines): no loop counter to test, 3 cycles less a byte.
        .for offset = 15, offset >= 0, offset -= 1
        ldy #offset
        lda (src_ptr),y
        sta (bmp_ptr),y
        .next

; Torch tiles: remember where their flame cell is.
        bit half
        bmi torch_checked       ; flames are top cells
        lda attr_bits
        and #TYPE_MASK
        beq torch_checked       ; most tiles
        cmp #TORCH_LEFT
        beq flame_in_left_cell
        cmp #TORCH_RIGHT
        bne torch_checked
        lda #8                  ; right cell: 8 bytes on
        jmp add_torch
flame_in_left_cell:
        lda #0
add_torch:
        ldy torch_count
        cpy #MAX_TORCHES
        bcs torch_checked       ; list full
        clc
        adc bmp_ptr
        sta torch_lo,y
        lda bmp_ptr+1
        adc #0
        sta torch_hi,y
        inc torch_count
torch_checked:

; Walkability of a solid cell: 2 for a door, so the
; explorer can tell a door from a wall; 1 otherwise.
        ldy #WALL_CELL
        lda attr_bits
        and #TYPE_MASK
        cmp #TYPE_DOOR
        bne cell_value_ready
        ldy #DOOR_CELL
cell_value_ready:
        sty solid_value

; Solid bits: 0 TL, 1 TR, 2 BL, 3 BR.
        lda attr_bits
        bit half
        bpl solid_ready
        lsr a                   ; bottom cells: bits 2-3
        lsr a
solid_ready:
        sta solid_bits

; Colours and walkability of the left and right cell.
        ldy cell_col
        lda TILE_SCR_L,x
        sta (scr_ptr),y
        lda TILE_COL_L,x
        sta (col_ptr),y
        lda #0                  ; walkable...
        lsr solid_bits          ; ...unless this bit is 1
        bcc left_cell_ready
        lda solid_value
left_cell_ready:
        sta (sol_ptr),y
        iny
        lda TILE_SCR_R,x
        sta (scr_ptr),y
        lda TILE_COL_R,x
        sta (col_ptr),y
        lda #0
        lsr solid_bits
        bcc right_cell_ready
        lda solid_value
right_cell_ready:
        sta (sol_ptr),y
        iny
        sty cell_col
        rts

; --- draw_metatile -------------------------------------
; Draws one metatile of the room over what is on the
; screen: A = id, X = map column, Y = map row. Used for
; doors (a torch tile would enter the list twice).
draw_metatile:
        sta tile_id
        txa
        asl a                   ; two cells per metatile
        sta cell_col
        tya
        asl a                   ; cell row = FIRST_ROW
        clc                     ;   + 2 * map row
        adc #FIRST_ROW
        tay

; Screen RAM, Color RAM and the walkability map start
; on a page boundary: their rows share the low byte.
        lda screen_rows_lo,y
        sta scr_ptr
        sta col_ptr
        sta sol_ptr
        lda screen_rows_hi,y
        sta scr_ptr+1
        clc
        adc #>(COLOR_RAM - SCREEN)
        sta col_ptr+1
        lda screen_rows_hi,y
        clc
        adc #>(SOLID_MAP - SCREEN)
        sta sol_ptr+1

; Bitmap: row start + column * 16 (up to 304).
        lda #0
        sta bmp_ptr+1
        lda cell_col            ; column * 2
        asl a
        asl a
        asl a                   ; only this one can carry
        rol bmp_ptr+1
        clc
        adc bitmap_rows_lo,y
        sta bmp_ptr
        lda bmp_ptr+1
        adc bitmap_rows_hi,y
        sta bmp_ptr+1

        lda #0                  ; top cells
        sta half
        lda tile_id
        jsr draw_half
        dec cell_col            ; same column,
        dec cell_col            ; one cell row down
        clc
        lda bmp_ptr
        adc #<320
        sta bmp_ptr
        lda bmp_ptr+1
        adc #>320
        sta bmp_ptr+1
        ldx #scr_ptr
        jsr down_one_row
        ldx #col_ptr
        jsr down_one_row
        ldx #sol_ptr
        jsr down_one_row
        lda #$80                ; bottom cells
        sta half
        lda tile_id
        jmp draw_half

; X = zero-page address of a pointer; add 40 to it.
down_one_row:
        clc
        lda 0,x
        adc #40
        sta 0,x
        bcc row_moved
        inc 1,x
row_moved:
        rts

; Bitmap and colours of cell row 24.
clear_name_row:
        lda #0
        ldx #0
clear_name_page:
        sta NAME_BITMAP,x       ; first 256 bytes
        inx
        bne clear_name_page
        ldx #63
clear_name_tail:
        sta NAME_BITMAP+256,x   ; last 64 bytes
        dex
        bpl clear_name_tail
        ldx #39
clear_name_colours:
        sta NAME_SCREEN,x
        dex
        bpl clear_name_colours
        rts

; --- animate_torches -----------------------------------
; Copies flame frame torch_phase into every flame cell
; recorded by draw_room.
animate_torches:
        lda torch_phase
        asl a                   ; 8 bytes per frame
        asl a
        asl a
        clc
        adc #<FLAMES
        sta flame_src
        lda #>FLAMES
        adc #0
        sta flame_src+1
        ldx torch_count
        beq torches_done
next_torch:
        dex
        lda torch_lo,x
        sta flame_dst
        lda torch_hi,x
        sta flame_dst+1
        ldy #7
copy_flame:
        lda (flame_src),y
        sta (flame_dst),y
        dey
        bpl copy_flame
        txa
        bne next_torch
torches_done:
        rts

torch_count: .byte 0
torch_lo:    .fill MAX_TORCHES
torch_hi:    .fill MAX_TORCHES

; CRYPTMORROW - memory map and zero page.
; Every address the program uses is named here.

; --- VIC-II bank 1: $4000-$7fff -----------------------
SPRITE_DATA = $4000     ; hero frames: pointers 0-7
OBJECT_SPRITES = $4200  ; objects: pointers 8-11
SCREEN      = $4400     ; colours 01/10 of each cell
SPRITE_PTRS = SCREEN + $3f8
BITMAP      = $6000     ; 8000 bytes, 40 x 25 cells
COLOR_RAM   = $d800     ; colour 11 of each cell
COMBAT_SPRITES = $4800  ; enemies, dust, blade: 32-40
BIG_FONT    = $4c00     ; 26 big letters, 120 bytes each
BIG_STYLES  = $5840     ; colours of big words, 16 a style

; --- Metatile catalog, built by game/assets -----------
; A metatile is 2 x 2 cells. The four colour tables
; hold the top cells at index id and the bottom cells
; at index id + 128.
TILE_BITMAP = $8000     ; 32 bytes a tile: TL TR BL BR
TILE_SCR_L  = $9000     ; screen byte, left cells
TILE_SCR_R  = $9100     ; screen byte, right cells
TILE_COL_L  = $9200     ; Color RAM, left cells
TILE_COL_R  = $9300     ; Color RAM, right cells
TILE_ATTR   = $9400     ; solid bits 0-3, type 4-6
FLAMES      = $9480     ; four 8-byte flame frames
FONT        = $9500     ; 8 bytes per glyph
SOLID_MAP   = $9800     ; 40 x 25 flags, 1 = solid
DOOR_TILES  = $9c00     ; 4 x 32: open tiles of doors
TITLE_PAGE  = $9d00     ; pages of the three screens,
OVER_PAGE   = $9e00     ; like room pages: map, zone,
WON_PAGE    = $9f00     ; text of the bottom row
ROOM_DATA   = $a000     ; 16 rooms, a page each
ZONE_COLOURS = $b000    ; 4 x 1 KB: colour tables
MUSIC_DATA  = $c000     ; music tables and patterns

; --- A room page: ROOM_DATA + room * 256 --------------
ROOM_MAP     = 0        ; 200 metatile ids, 20 x 10
ROOM_OBJECTS = 200      ; 2 x: kind, column, row, number
ROOM_DOOR    = 208      ; door: 1-3 keys A-C, 4 the
                        ; portal, 0 none
ROOM_ZONE    = 209      ; 0 atrio, 1-3 zones A-C
ROOM_ENEMIES = 216      ; 3 x: kind, column, row, patrol
ROOM_NAME    = 228      ; string for print_text

; --- Zero page: explorer ------------------------------
joy_state   = $02       ; read_joystick: JOY_* bits
hero_x      = $03       ; 16-bit screen X of sprite
hero_y      = $05       ; screen Y of sprite
hero_dir    = $06       ; DIR_*
hero_moving = $07       ; 1 if a step happened
walk_frame  = $08       ; 0/1
walk_timer  = $09       ; frames since last flip
probe_x     = $0a       ; 16-bit X tested by is_solid
probe_y     = $0c       ; Y tested by is_solid
cell_ptr    = $0d       ; is_solid: map row pointer
step_count  = $0f       ; try_move: steps left

; --- Zero page: room drawing --------------------------
room_ptr    = $10       ; current row of the map
bmp_ptr     = $12       ; bitmap of the current cells
scr_ptr     = $14       ; screen RAM, current row
col_ptr     = $16       ; Color RAM, current row
sol_ptr     = $18       ; walkability, current row
src_ptr     = $1a       ; tile bitmap being copied
half        = $1c       ; $00 top cells, $80 bottom
map_col     = $1d       ; 0-19
cell_col    = $1e       ; 0-38, two per metatile
rows_left   = $1f       ; cell rows still to draw
tile_id     = $20       ; metatile being drawn
attr_bits   = $21       ; its TILE_ATTR byte
solid_bits  = $22       ; solid bits of this half
fill_ptr    = $23       ; fill_pages destination

; --- Zero page: text and torches ----------------------
text_ptr    = $25       ; string being printed
text_bmp    = $27       ; bitmap of the next glyph
text_scr    = $29       ; screen RAM of that cell
glyph_ptr   = $2b       ; glyph in FONT
text_col    = $2d       ; column of the string
text_colour = $2e       ; colour << 4
text_pos    = $2f       ; offset of next character
flame_src   = $30       ; flame frame being shown
flame_dst   = $32       ; flame cell in the bitmap

; --- Zero page: music player --------------------------
; Used inside the interrupt only: nothing else writes
; these addresses.
pat_ptr     = $34       ; pattern being read
ord_ptr     = $36       ; order list being read
freq_lo     = $38       ; frequency of this frame
freq_hi     = $39

; --- Zero page: rooms ---------------------------------
page_ptr    = $3a       ; page of the current room
solid_value = $3c       ; draw_half: 1 wall, 2 door
hero_block  = $3d       ; what stopped the explorer

; --- Zero page: zone colours --------------------------
zone_src    = $3e       ; set_zone: colour tables
zone_dst    = $40       ; set_zone: TILE_SCR_L...

; --- Zero page: big letters ---------------------------
big_colour  = $42       ; print_big: Color RAM pointer

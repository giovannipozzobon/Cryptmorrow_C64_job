; CRYPTMORROW - the explorer: joystick, movement,
; collisions with the walkability map, animation.
; update_hero keeps what stopped the explorer in
; hero_block: a wall or a door. place_hero sets only
; the ninth X bit of its own sprite.

HERO_START_X = 148      ; screen X of the sprite corner
HERO_START_Y = 111      ; screen Y of the sprite corner
HERO_SPEED   = 1        ; pixels per frame
WALK_RATE    = 8        ; frames between walk frames
HERO_POINTER = (SPRITE_DATA - $4000) / 64

; Hitbox at the explorer's feet, in sprite pixels
; (the sprite is 24 x 21).
BOX_LEFT   = 6
BOX_RIGHT  = 17
BOX_TOP    = 13
BOX_BOTTOM = 18
BOX_MID    = 11

DIR_DOWN  = 0
DIR_UP    = 1
DIR_LEFT  = 2
DIR_RIGHT = 3

JOY_UP    = %00000001
JOY_DOWN  = %00000010
JOY_LEFT  = %00000100
JOY_RIGHT = %00001000
JOY_FIRE  = %00010000

; --- read_joystick -------------------------------------
; Port 2 switches read 0 when pressed: invert them.
read_joystick:
        lda $dc00
        eor #$ff
        and #$1f                ; up/down/left/right/fire
        sta joy_state
joy_ready:                      ; the test injects input
        rts

; --- init_hero -----------------------------------------
init_hero:
        lda #<HERO_START_X
        sta hero_x
        lda #>HERO_START_X
        sta hero_x+1
        lda #HERO_START_Y
        sta hero_y
        lda #DIR_DOWN
        sta hero_dir
        lda #0
        sta hero_moving
        sta walk_frame
        sta walk_timer
        sta joy_state
        sta $d017               ; no expansion
        sta $d01d
        sta $d01b               ; sprite over the bitmap
        lda #9                  ; code 01: brown
        sta $d025
        lda #10                 ; code 11: skin
        sta $d026
        lda #5                  ; code 10: green tunic
        sta $d027
        lda #1
        sta $d01c               ; sprite 0 multicolour
        sta $d015               ; sprite 0 visible
        jsr animate_hero
        jmp place_hero

; --- update_hero ---------------------------------------
; Horizontal input wins over vertical: no diagonals.
update_hero:
        lda #0
        sta hero_moving
        sta hero_block
        lda joy_state
        and #JOY_LEFT | JOY_RIGHT
        beq vertical            ; no horizontal input
        and #JOY_LEFT
        beq go_right
        lda #DIR_LEFT
        sta hero_dir
        jmp try_move
go_right:
        lda #DIR_RIGHT
        sta hero_dir
        jmp try_move
vertical:
        lda joy_state
        and #JOY_UP | JOY_DOWN
        beq update_done         ; stick centred
        and #JOY_UP
        beq go_down
        lda #DIR_UP
        sta hero_dir
        jmp try_move
go_down:
        lda #DIR_DOWN
        sta hero_dir
try_move:
        lda #HERO_SPEED
        sta step_count
step_loop:
        jsr step_blocked        ; one pixel ahead
        sta hero_block          ; 0 floor, 1 wall, 2 door
        bne update_done         ; solid: stop
        jsr step_forward
        lda #1
        sta hero_moving
        dec step_count
        bne step_loop
update_done:
        rts

; --- step_blocked --------------------------------------
; A != 0 when the cells one pixel ahead of the
; hitbox, in hero_dir, are solid: A is the value of the
; first solid cell found (1 wall, 2 door).
step_blocked:
        lda hero_dir
        cmp #DIR_LEFT
        beq blocked_left
        cmp #DIR_RIGHT
        beq blocked_right
        cmp #DIR_UP
        beq blocked_up
blocked_down:
        lda hero_y
        clc
        adc #BOX_BOTTOM + 1
        sta probe_y
        jmp blocked_row
blocked_up:
        lda hero_y
        clc
        adc #BOX_TOP - 1
        sta probe_y
blocked_row:                    ; left, middle, right
        lda #BOX_LEFT
        jsr probe_column
        jsr is_solid
        bne blocked_done
        lda #BOX_MID
        jsr probe_column
        jsr is_solid
        bne blocked_done
        lda #BOX_RIGHT
        jsr probe_column
        jmp is_solid
blocked_left:
        lda #BOX_LEFT - 1
        jsr probe_column
        jmp blocked_column
blocked_right:
        lda #BOX_RIGHT + 1
        jsr probe_column
blocked_column:                 ; top and bottom
        lda hero_y
        clc
        adc #BOX_TOP
        sta probe_y
        jsr is_solid
        bne blocked_done
        lda hero_y
        clc
        adc #BOX_BOTTOM
        sta probe_y
        jmp is_solid
blocked_done:
        rts

; probe_x = hero_x + A (A = offset in the sprite)
probe_column:
        clc
        adc hero_x
        sta probe_x
        lda hero_x+1
        adc #0
        sta probe_x+1
        rts

step_forward:
        lda hero_dir
        cmp #DIR_LEFT
        beq forward_left
        cmp #DIR_RIGHT
        beq forward_right
        cmp #DIR_UP
        beq forward_up
        inc hero_y
        rts
forward_up:
        dec hero_y
        rts
forward_left:
        lda hero_x
        bne left_low
        dec hero_x+1
left_low:
        dec hero_x
        rts
forward_right:
        inc hero_x
        bne forward_done
        inc hero_x+1
forward_done:
        rts

; --- is_solid ------------------------------------------
; A = SOLID_MAP flag of the cell at (probe_x, probe_y).
; Points outside the 320 x 200 screen are solid.
is_solid:
        lda probe_x+1
        beq solid_x_ok
        cmp #1
        bne solid_outside
        lda probe_x
        cmp #64                 ; X >= 320
        bcs solid_outside
solid_x_ok:
        lda probe_y
        cmp #200
        bcs solid_outside
        lsr a                   ; row = Y / 8
        lsr a
        lsr a
        asl a                   ; two bytes per entry
        tax
        lda row_offsets,x
        sta cell_ptr
        lda row_offsets+1,x
        sta cell_ptr+1
        lda probe_x+1           ; column = X / 8
        lsr a                   ; ninth bit into carry
        lda probe_x
        ror a
        lsr a
        lsr a
        tay
        lda (cell_ptr),y
        rts
solid_outside:
        lda #1
        rts

; --- animate_hero --------------------------------------
animate_hero:
        lda hero_moving
        bne walking
        lda #0                  ; standing: rest frame
        sta walk_frame
        sta walk_timer
        beq set_pointer
walking:
        inc walk_timer
        lda walk_timer
        cmp #WALK_RATE
        bne set_pointer
        lda #0
        sta walk_timer
        lda walk_frame
        eor #1
        sta walk_frame
set_pointer:
        lda hero_dir            ; dir * 2 + walk_frame
        asl a
        ora walk_frame
        clc
        adc #HERO_POINTER
        sta SPRITE_PTRS
        rts

; --- place_hero ----------------------------------------
place_hero:
        lda $d010               ; ninth X bit of sprite 0
        and #%11111110          ; off; the other sprites
        sta $d010               ; keep theirs
        lda hero_x              ; VIC X = screen X + 24
        clc
        adc #24
        sta $d000
        lda hero_x+1
        adc #0
        beq x_below_256
        lda $d010
        ora #1                  ; ninth bit on
        sta $d010
x_below_256:
        lda hero_y              ; VIC Y = screen Y + 50
        clc
        adc #50
        sta $d001
        rts

; SOLID_MAP + row * 40 for the 25 cell rows
row_offsets:
        .word SOLID_MAP + range(25) * 40

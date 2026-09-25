; CRYPTMORROW - combat: the sword, skeletons and bats,
; damage and the end of a game, lost or won. The blade
; is sprite 1, the enemies sprites 2-4. Enemies come
; back each time a room is entered.

MAX_ENEMIES   = 3       ; enemy slots in a room page
BLADE_SPRITE  = 1
ENEMY_SPRITE  = 2       ; sprites 2, 3, 4
SKELETON      = 1       ; enemy kinds in a room page
BAT           = 2
FAST_FLAG     = 2       ; flags: bit 0 up-down, 1 fast
ENDED_LOST    = 1       ; game_ended: GAME OVER
ENDED_WON     = 2       ; game_ended: VICTORY
SLASH_FRAMES  = 20      ; a blow lasts 20 frames:
BLADE_FRAMES  = 8       ; the blade is out for 8
BLADE_UNTIL   = SLASH_FRAMES - BLADE_FRAMES
SAFE_FRAMES   = 30      ; frames safe after a hit
DAMAGE        = 2       ; cells of energy a touch
FLASH_FRAMES  = 8       ; a hit enemy flashes, stops
DUST_FRAMES   = 12      ; a defeated enemy: dust
REACH         = 12      ; closer than this: a touch
CHASE_X       = 120     ; a bat chases the explorer
CHASE_Y       = 90      ; inside this distance
RING_LEFT     = 8       ; skeletons stay out of the
RING_RIGHT    = 312     ; outermost ring of cells,
RING_TOP      = 32      ; where the openings are
RING_BOTTOM   = 176
COMBAT_POINTER = (COMBAT_SPRITES - $4000) / 64
SKELETON_FRAME = COMBAT_POINTER         ; 2 frames
BAT_FRAME      = COMBAT_POINTER + 2     ; 2 frames
DUST_FRAME     = COMBAT_POINTER + 4
BLADE_FRAME    = COMBAT_POINTER + 5     ; + direction
FLASH_COLOUR   = LIGHT_RED
BLADE_COLOUR   = WHITE

; --- check_fire ----------------------------------------
; Fire starts a blow when the last one is over and the
; button was up the frame before: no automatic repeat.
; While the blade is out the explorer stands still, so
; the stick is ignored.
check_fire:
        lda slash_timer
        beq fire_ready
        dec slash_timer
fire_ready:
        lda joy_state
        and #JOY_FIRE
        cmp fire_held
        sta fire_held
        beq blade_out           ; no change
        tax
        beq blade_out           ; released
        lda slash_timer
        bne blade_out           ; the last blow goes on
        lda #SLASH_FRAMES       ; a new blow
        sta slash_timer
        lda hero_dir
        sta blade_dir
        lda #0                  ; nobody hit by it yet
        ldx #MAX_ENEMIES - 1
clear_hits:
        sta en_hit,x
        dex
        bpl clear_hits
blade_out:
        lda slash_timer
        cmp #BLADE_UNTIL + 1
        bcc fire_done
        lda #0
        sta joy_state
fire_done:
        rts

; --- spawn_enemies -------------------------------------
; The enemies of the room page, at their places: X =
; column * 16 - 4, Y = row * 16 + 20 (sprite corner).
spawn_enemies:
        ldx #MAX_ENEMIES - 1
spawn_slot:
        txa
        asl a
        asl a                   ; 4 bytes a slot
        clc
        adc #ROOM_ENEMIES
        tay
        lda (page_ptr),y        ; kind, 0: empty slot
        sta en_kind,x
        iny
        lda #0
        sta en_x_hi,x
        lda (page_ptr),y        ; column
        asl a
        asl a
        asl a
        asl a                   ; only this one can carry
        rol en_x_hi,x
        sec
        sbc #4
        sta en_x_lo,x
        bcs spawn_row
        dec en_x_hi,x
spawn_row:
        iny
        lda (page_ptr),y        ; row
        asl a
        asl a
        asl a
        asl a
        clc
        adc #20
        sta en_y,x
        iny
        lda (page_ptr),y        ; flags
        lsr a                   ; bit 0: up and down
        lda #DIR_RIGHT          ; (lda keeps the carry)
        bcc patrol_ready
        lda #DIR_DOWN
patrol_ready:
        sta en_dir,x
        lda (page_ptr),y
        and #FAST_FLAG
        sta en_fast,x
        ldy en_kind,x
        lda enemy_hp,y
        sta en_hp,x
        lda #0
        sta en_flash,x
        sta en_dust,x
        sta en_hit,x
        dex
        bpl spawn_slot
        rts

; --- update_enemies ------------------------------------
update_enemies:
        ldx #MAX_ENEMIES - 1
enemy_turn:
        lda en_kind,x
        beq enemy_done          ; empty slot, or gone
        lda en_dust,x
        beq enemy_alive
        dec en_dust,x           ; dust for a moment,
        bne enemy_done
        lda #0                  ; then gone
        sta en_kind,x
        beq enemy_done
enemy_alive:
        lda en_flash,x
        beq enemy_moves
        dec en_flash,x          ; just hit: stands still
        jmp enemy_done
enemy_moves:
        lda en_kind,x
        cmp #SKELETON
        bne bat_moves
        jsr skeleton_step
        jmp enemy_done
bat_moves:
        jsr bat_step
enemy_done:
        dex
        bpl enemy_turn
        rts

; --- skeleton_step -------------------------------------
; A skeleton walks one pixel every other frame along its
; patrol (every frame if fast) and turns back at
; anything solid.
skeleton_step:
        lda en_fast,x
        bne step_now            ; fast: no rest
        lda frame_count
        lsr a
        bcs step_done           ; odd frame: rests
step_now:
        jsr enemy_blocked
        beq step_ahead
        lda en_dir,x            ; turn round: down-up,
        eor #1                  ; left-right
        sta en_dir,x
        rts
step_ahead:
        lda en_dir,x
        cmp #DIR_LEFT
        beq enemy_left
        cmp #DIR_RIGHT
        beq enemy_right
        cmp #DIR_UP
        beq enemy_up
        inc en_y,x
        rts
enemy_up:
        dec en_y,x
        rts
enemy_left:
        lda en_x_lo,x
        bne enemy_left_low
        dec en_x_hi,x
enemy_left_low:
        dec en_x_lo,x
        rts
enemy_right:
        inc en_x_lo,x
        bne step_done
        inc en_x_hi,x
step_done:
        rts

; --- bat_step ------------------------------------------
; A bat hangs still until the explorer comes near, then
; flies after it: across on even frames, up or down on
; odd frames, over walls and pillars.
bat_step:
        jsr aim_at_hero
        jsr measure
        lda far_x
        cmp #CHASE_X
        bcs bat_waits
        lda far_y
        cmp #CHASE_Y
        bcs bat_waits
        lda frame_count
        lsr a
        bcs bat_vertical        ; odd frame
        lda far_x
        beq bat_waits           ; same column already
        bit west
        bmi enemy_left
        bpl enemy_right
bat_vertical:
        lda far_y
        beq bat_waits
        bit north
        bmi enemy_up
        inc en_y,x
bat_waits:
        rts

; --- enemy_blocked -------------------------------------
; A != 0 if the feet of enemy X cannot move one pixel in
; en_dir: the explorer's hitbox and walkability map,
; with the ring of openings counted as wall.
enemy_blocked:
        stx enemy_slot
        lda en_dir,x
        cmp #DIR_LEFT
        bcs across              ; left or right
        cmp #DIR_UP
        beq feet_up
        lda en_y,x              ; down: below the feet
        clc
        adc #BOX_BOTTOM + 1
        jmp feet_row
feet_up:
        lda en_y,x              ; up: above the feet
        clc
        adc #BOX_TOP - 1
feet_row:
        sta probe_y
        lda #BOX_LEFT
        jsr enemy_column
        jsr probe_cell
        bne blocked_found
        lda #BOX_RIGHT
        jsr enemy_column
        jmp probe_cell
across:
        beq feet_left
        lda #BOX_RIGHT + 1      ; right of the feet
        jmp feet_column
feet_left:
        lda #BOX_LEFT - 1       ; left of the feet
feet_column:
        jsr enemy_column
        lda en_y,x
        clc
        adc #BOX_TOP
        sta probe_y
        jsr probe_cell
        bne blocked_found
        lda en_y,x
        clc
        adc #BOX_BOTTOM
        sta probe_y
        jmp probe_cell
blocked_found:
        rts

; probe_x = X of enemy X + A
enemy_column:
        clc
        adc en_x_lo,x
        sta probe_x
        lda en_x_hi,x
        adc #0
        sta probe_x+1
        rts

; A = the cell at (probe_x, probe_y) for an enemy, the
; flags set by A; X = enemy_slot again.
probe_cell:
        lda probe_y
        cmp #RING_TOP
        bcc ring_wall
        cmp #RING_BOTTOM
        bcs ring_wall
        lda probe_x+1
        bne probe_east          ; X >= 256
        lda probe_x
        cmp #RING_LEFT
        bcc ring_wall
        bcs probe_map
probe_east:
        lda probe_x
        cmp #<RING_RIGHT        ; 312 - 256
        bcs ring_wall
probe_map:
        jsr is_solid            ; uses X and Y
        ldx enemy_slot
        cmp #0
        rts
ring_wall:
        ldx enemy_slot
        lda #1
        rts

; --- aim_at_hero, measure ------------------------------
; measure: distance from enemy X to the point (pt_x,
; pt_y): far_x and far_y (255 if larger), and its sign:
; west = $ff if the point is left of the enemy, north =
; $ff if above.
aim_at_hero:
        lda hero_x
        sta pt_x
        lda hero_x+1
        sta pt_x+1
        lda hero_y
        sta pt_y
        rts

measure:
        lda #0
        sta west
        sta north
        sec
        lda pt_x
        sbc en_x_lo,x
        sta far_x
        lda pt_x+1
        sbc en_x_hi,x
        beq x_measured          ; 0-255 to the east
        cmp #$ff
        bne x_far               ; 256 or more
        dec west                ; to the west
        lda #0
        sec
        sbc far_x               ; minus the difference
        beq x_far               ; -256
        sta far_x
        jmp x_measured
x_far:
        lda #255
        sta far_x
x_measured:
        sec
        lda pt_y
        sbc en_y,x
        bcs y_measured          ; the point is lower
        dec north
        eor #$ff                ; carry is clear: minus
        adc #1                  ; the difference
y_measured:
        sta far_y
        rts

; --- check_blade ---------------------------------------
; While the blade is out, every enemy near its point is
; hit, once per blow; then the same for a point half
; way back, so that an enemy on top of the explorer can
; be hit too. A skeleton takes two hits.
check_blade:
        lda slash_timer
        cmp #BLADE_UNTIL + 1
        bcc blade_done
        lda blade_dir           ; the point of the blow
        jsr blade_point
        lda blade_dir           ; the point half way
        ora #4                  ; (tables 4-7)
blade_point:
        tay
        lda hero_x
        clc
        adc strike_x,y
        sta pt_x
        lda hero_x+1
        adc strike_x_high,y
        sta pt_x+1
        lda hero_y
        clc
        adc strike_y,y
        sta pt_y
        ldx #MAX_ENEMIES - 1
blade_test:
        lda en_kind,x
        beq blade_next
        lda en_dust,x
        ora en_hit,x
        bne blade_next          ; dust, or hit already
        jsr measure
        lda far_x
        cmp #REACH
        bcs blade_next
        lda far_y
        cmp #REACH
        bcs blade_next
        lda #1
        sta en_hit,x
        dec en_hp,x
        bne enemy_hurt
        lda #DUST_FRAMES        ; defeated
        sta en_dust,x
        ldy en_kind,x
        lda enemy_points_low-1,y
        sta gain_low
        lda enemy_points_middle-1,y
        sta gain_middle
        jsr add_score
        jmp blade_next
enemy_hurt:
        lda #FLASH_FRAMES
        sta en_flash,x
blade_next:
        dex
        bpl blade_test
blade_done:
        rts

; --- check_contact -------------------------------------
; An enemy touching the explorer takes DAMAGE cells of
; energy (never below zero); then the explorer cannot be
; hurt for a while and blinks. With no energy left the
; game is over.
check_contact:
        lda invulnerable
        beq contact_test
        dec invulnerable
        rts
contact_test:
        jsr aim_at_hero
        ldx #MAX_ENEMIES - 1
contact_loop:
        lda en_kind,x
        beq contact_next
        lda en_dust,x
        bne contact_next
        jsr measure
        lda far_x
        cmp #REACH
        bcs contact_next
        lda far_y
        cmp #REACH
        bcs contact_next
        lda energy              ; hurt
        sec
        sbc #DAMAGE
        bcs energy_left
        nop                     ; not below zero
energy_left:
        sta energy
        lda #SAFE_FRAMES
        sta invulnerable
        lda #1
        sta hud_dirty
        lda energy
        bne contact_done
        jmp game_over
contact_next:
        dex
        bpl contact_loop
contact_done:
        rts

; --- game_over, victory --------------------------------
; The end of a game: the room stops, GAME OVER (no energy
; left) or VICTORY (out through the portal) takes the
; place of its name.
game_over:
        lda #ENDED_LOST
        ldx #<over_text
        ldy #>over_text
        bne game_ends           ; always
victory:
        lda #ENDED_WON
        ldx #<won_text
        ldy #>won_text
game_ends:
        sta game_ended
        stx end_text
        sty end_text+1
        lda #0
        sta invulnerable        ; the explorer in view
        sta slash_timer         ; no blade
        jsr clear_name_row
        lda end_text
        ldy end_text+1
        jmp print_at

; --- show_combat ---------------------------------------
; The explorer blinks while it cannot be hurt; sprite 1
; shows the blade while it is out, sprites 2-4 the
; enemies.
show_combat:
        lda invulnerable
        and #4
        bne hero_hidden
        lda $d015
        ora #1
        bne hero_ready          ; always
hero_hidden:
        lda $d015
        and #%11111110
hero_ready:
        sta $d015
        lda $d01c               ; enemies multicolour,
        and #%11111101          ; the blade high-res
        ora #%00011100
        sta $d01c
        lda #BLADE_COLOUR
        sta $d027+BLADE_SPRITE

        lda slash_timer
        cmp #BLADE_UNTIL + 1
        bcc blade_hidden
        ldy blade_dir
        tya
        clc
        adc #BLADE_FRAME
        sta SPRITE_PTRS+BLADE_SPRITE
        lda hero_x              ; VIC X: explorer + blade_x
        clc
        adc blade_x,y
        sta $d000+2*BLADE_SPRITE
        lda hero_x+1
        adc #0
        beq blade_x_low
        lda $d010
        ora #1 << BLADE_SPRITE
        bne blade_ninth
blade_x_low:
        lda $d010
        and #%11111101
blade_ninth:
        sta $d010
        lda hero_y
        clc
        adc blade_y,y
        sta $d001+2*BLADE_SPRITE
        lda $d015
        ora #1 << BLADE_SPRITE
        bne blade_ready         ; always
blade_hidden:
        lda $d015
        and #%11111101
blade_ready:
        sta $d015

        ldx #MAX_ENEMIES - 1
show_enemy:
        lda en_kind,x
        bne enemy_frame
        jmp hide_enemy
enemy_frame:
        lda en_dust,x
        beq enemy_animated
        lda #DUST_FRAME
        bne enemy_pointer       ; always
enemy_animated:
        lda frame_count         ; skeleton: new frame
        lsr a                   ; every 8, bat every 4
        lsr a
        ldy en_kind,x
        cpy #BAT
        beq frame_bit
        lsr a
frame_bit:
        and #1
        clc
        adc enemy_frames-1,y
enemy_pointer:
        sta SPRITE_PTRS+ENEMY_SPRITE,x
        ldy en_kind,x
        lda enemy_colours-1,y
        ldy en_flash,x
        beq enemy_colour
        lda #FLASH_COLOUR
enemy_colour:
        sta $d027+ENEMY_SPRITE,x
        txa
        asl a                   ; two VIC registers
        tay                     ; per sprite
        lda en_x_lo,x           ; VIC X = X + 24
        clc
        adc #24
        sta $d000+2*ENEMY_SPRITE,y
        lda en_x_hi,x
        adc #0
        beq enemy_x_low
        lda $d010
        ora enemy_bits,x
        bne enemy_ninth         ; always
enemy_x_low:
        lda enemy_bits,x
        eor #$ff
        and $d010
enemy_ninth:
        sta $d010
        lda en_y,x              ; VIC Y = Y + 50
        clc
        adc #50
        sta $d001+2*ENEMY_SPRITE,y
        lda $d015
        ora enemy_bits,x
        bne enemy_shown         ; always
hide_enemy:
        lda enemy_bits,x
        eor #$ff
        and $d015
enemy_shown:
        sta $d015
        dex
        bmi enemies_shown
        jmp show_enemy          ; too far for a branch
enemies_shown:
        rts

; --- Tables --------------------------------------------
; By direction (down, up, left, right): the point of a
; blow, from the explorer's corner; where the blade
; sprite goes (VIC coordinates, from the explorer's).
; Points 0-3 are ahead, 4-7 half way back.
strike_x:       .byte 3, 3, <-20, 20, 3, 3, <-10, 10
strike_x_high:  .byte 0, 0, $ff, 0, 0, 0, $ff, 0
strike_y:       .byte 16, <-20, <-1, <-1
                .byte 8, <-10, <-1, <-1
blade_x:        .byte 24 + 4, 24 + 4, 24 - 18, 24 + 18
blade_y:        .byte 50 + 12, 50 - 16, 50 - 1, 50 - 1
; By enemy kind (skeleton, bat)
enemy_hp:       .byte 0, 3, 1   ; kind 0: an empty slot
enemy_frames:   .byte SKELETON_FRAME, BAT_FRAME
enemy_colours:  .byte LIGHT_GREY, PURPLE
enemy_points_low:    .byte $00, $50     ; 100, 50
enemy_points_middle: .byte $01, $00
enemy_bits:     .byte 4, 8, 16  ; sprites 2, 3, 4

        .enc "glyphs"
over_text:
        .byte 15, 24, LIGHT_RED
        .text "GAME OVER"
        .byte TEXT_END
won_text:
        .byte 16, 24, YELLOW
        .text "VICTORY"
        .byte TEXT_END
        .enc "none"

; --- Combat state --------------------------------------
slash_timer:  .byte 0   ; 20 at a blow, down to 0
blade_dir:    .byte 0   ; direction of the blow
fire_held:    .byte 0   ; JOY_FIRE if held last frame
invulnerable: .byte 0   ; frames left without damage
game_ended:   .byte 0   ; ENDED_LOST or ENDED_WON
en_kind:      .fill MAX_ENEMIES ; 0 none, 1 skeleton, 2 bat
en_x_lo:      .fill MAX_ENEMIES ; sprite corner, like the
en_x_hi:      .fill MAX_ENEMIES ; explorer's hero_x/y
en_y:         .fill MAX_ENEMIES
en_dir:       .fill MAX_ENEMIES ; skeleton: DIR_ value
en_hp:        .fill MAX_ENEMIES ; hits still needed
en_flash:     .fill MAX_ENEMIES ; frames of hit flash
en_dust:      .fill MAX_ENEMIES ; frames of dust left
en_hit:       .fill MAX_ENEMIES ; 1: hit by this blow
en_fast:      .fill MAX_ENEMIES ; FAST_FLAG: every frame
enemy_slot:   .byte 0
pt_x:         .word 0   ; a point, for measure
pt_y:         .byte 0
far_x:        .byte 0
far_y:        .byte 0
west:         .byte 0
north:        .byte 0
end_text:     .word 0   ; game_ends: the string

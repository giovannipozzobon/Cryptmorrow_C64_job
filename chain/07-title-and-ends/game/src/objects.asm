; CRYPTMORROW - objects, locked doors and the portal.
; Up to two objects per room, shown by sprites 5 and 6;
; a door opens with its key and stays open; the portal
; of the start room opens with the three seals. What was
; taken or opened is kept in bits, so room data never
; changes.

MAX_OBJECTS    = 2      ; object slots in a room page
FIRST_SPRITE   = 5      ; sprites 5 and 6
KIND_KEY       = 1      ; 1-3: keys A, B, C
KIND_SEAL      = 4
KIND_TREASURE  = 5
KIND_POTION    = 6
POTION_ENERGY  = 2      ; cells of the bar per potion
PORTAL         = 4      ; door number of the portal
MAX_SEALS      = 3      ; seals that open the portal
LIST_END       = $ff    ; ends a list of DOOR_TILES
DOOR_LIST      = 32     ; bytes per door in DOOR_TILES
OBJECT_POINTER = (OBJECT_SPRITES - $4000) / 64
HIT_X = (BOX_LEFT + BOX_RIGHT) / 2      ; middle of the
HIT_Y = (BOX_TOP + BOX_BOTTOM) / 2      ; hitbox: 11, 15

; --- check_door ----------------------------------------
; After update_hero: if a door stopped the explorer and
; it carries its key, the key is used up and the door
; opens for the rest of the game. The portal needs no
; key but all the seals, and keeps them.
check_door:
        lda hero_block
        cmp #DOOR_CELL
        bne door_done
        ldy #ROOM_DOOR
        lda (page_ptr),y        ; door 1-4, 0: none
        beq door_done
        tax
        cpx #PORTAL
        beq portal_door
        lda key_bits-1,x
        and key_set
        beq door_done           ; no key: stays shut
        eor key_set             ; the key is used up
        sta key_set
        lda #1
        sta hud_dirty
        bne door_opens          ; always
portal_door:
        lda seals
        cmp #MAX_SEALS
        bne door_done           ; not all the seals yet
door_opens:
        lda doors_open
        ora key_bits-1,x
        sta doors_open
        lda #FX_DOOR
        jsr sound_effect
        jmp show_door
door_done:
        rts

; --- show_door -----------------------------------------
; Draws the open door over the closed one, if the door
; of this room has been opened: the list of door N in
; DOOR_TILES (column, row, open tile; LIST_END).
show_door:
        ldy #ROOM_DOOR
        lda (page_ptr),y
        beq no_door
        tax
        lda key_bits-1,x
        and doors_open
        beq no_door
        dex                     ; list at (N - 1) * 32
        txa
        asl a
        asl a
        asl a
        asl a
        asl a
        sta door_index
door_tile:
        ldx door_index
        lda DOOR_TILES,x
        cmp #LIST_END
        beq no_door
        sta door_col
        lda DOOR_TILES+1,x
        sta door_row
        lda DOOR_TILES+2,x      ; the open tile
        pha
        txa
        clc
        adc #3                  ; next entry
        sta door_index
        pla
        ldx door_col
        ldy door_row
        jsr draw_metatile
        jmp door_tile
no_door:
        rts

; --- read_object ---------------------------------------
; Copies slot obj_slot of the room page: kind, column,
; row and number of the object.
read_object:
        lda obj_slot
        asl a
        asl a                   ; 4 bytes a slot
        clc
        adc #ROOM_OBJECTS
        tay
        lda (page_ptr),y
        sta obj_kind            ; 0: empty slot
        iny
        lda (page_ptr),y
        sta obj_col
        iny
        lda (page_ptr),y
        sta obj_row
        iny
        lda (page_ptr),y
        sta obj_number
        rts

; --- taken_bit -----------------------------------------
; X = byte of `taken` and A = bit mask for obj_number.
taken_bit:
        lda obj_number
        and #7
        tay
        lda obj_number
        lsr a
        lsr a
        lsr a
        tax
        lda bit_masks,y
        rts

; --- show_objects --------------------------------------
; Sprites 5 and 6 show the objects of the room that are
; still there, centred on their metatile.
show_objects:
        lda $d01c               ; multicolour, like the
        ora #%01100000          ; explorer
        sta $d01c
        lda #0
        sta obj_slot
show_slot:
        jsr read_object
        lda obj_kind
        beq hide_slot           ; empty slot
        jsr taken_bit
        and taken,x
        bne hide_slot           ; already taken
        ldx obj_slot
        ldy obj_kind
        lda object_frames-1,y
        sta SPRITE_PTRS+FIRST_SPRITE,x
        lda object_colours-1,y
        sta $d027+FIRST_SPRITE,x

; VIC X = column * 16 - 4 + 24; VIC Y = row * 16 + 22
; + 50. Column 19 gives 324: X needs a ninth bit.
        lda #0
        sta obj_x_high
        lda obj_col
        asl a
        asl a
        asl a
        asl a                   ; only this one can carry
        rol obj_x_high
        clc
        adc #20
        sta obj_x
        bcc x_ready
        inc obj_x_high
x_ready:
        lda obj_slot
        asl a                   ; two VIC registers
        tay                     ; per sprite
        lda obj_x
        sta $d000+2*FIRST_SPRITE,y
        lda obj_row
        asl a
        asl a
        asl a
        asl a
        clc
        adc #72
        sta $d001+2*FIRST_SPRITE,y
        lda sprite_bits,x
        eor #$ff
        and $d010               ; ninth bit off...
        ldy obj_x_high
        beq ninth_ready
        ora sprite_bits,x       ; ...or on
ninth_ready:
        sta $d010
        lda $d015
        ora sprite_bits,x       ; visible
        sta $d015
        jmp next_slot
hide_slot:
        ldx obj_slot
        lda sprite_bits,x
        eor #$ff
        and $d015               ; hidden
        sta $d015
next_slot:
        inc obj_slot
        lda obj_slot
        cmp #MAX_OBJECTS
        beq objects_shown
        jmp show_slot           ; too far for a branch
objects_shown:
        rts

; --- check_objects -------------------------------------
; The explorer picks up an object when the middle of
; its hitbox is inside the object's metatile.
; Column = (X + HIT_X) / 16, row = (Y + HIT_Y - 24) / 16.
check_objects:
        lda hero_x+1
        sta hero_col            ; high byte, then shifted
        lda hero_x
        clc
        adc #HIT_X
        bcc column_sum
        inc hero_col
column_sum:
        ldx #4                  ; 16-bit value / 16
divide_column:
        lsr hero_col
        ror a
        dex
        bne divide_column
        sta hero_col
        lda hero_y
        sec
        sbc #24 - HIT_Y         ; Y is at least 11
        lsr a
        lsr a
        lsr a
        lsr a
        sta hero_row

        lda #0
        sta obj_slot
pick_slot:
        jsr read_object
        lda obj_kind
        beq pick_next
        lda obj_col
        cmp hero_col
        bne pick_next
        lda obj_row
        cmp hero_row
        bne pick_next
        jsr taken_bit
        and taken,x
        bne pick_next           ; gone already
        jsr use_object          ; carry set: taken
        bcc pick_next
        jsr taken_bit
        ora taken,x
        sta taken,x
        ldx obj_slot
        lda sprite_bits,x
        eor #$ff
        and $d015
        sta $d015
        lda #FX_PICKUP
        jsr sound_effect
        lda #1
        sta hud_dirty
pick_next:
        inc obj_slot
        lda obj_slot
        cmp #MAX_OBJECTS
        bne pick_slot
        rts

; --- use_object ----------------------------------------
; The effect of object obj_kind. Carry set if it is
; taken, clear if it stays on the floor.
use_object:
        lda obj_kind
        cmp #KIND_SEAL
        bcc take_key            ; 1-3
        beq take_seal
        cmp #KIND_TREASURE
        beq add_points
        lda energy              ; potion: only if the
        cmp #ENERGY_MAX         ; energy is not full
        bcs leave_object
        adc #POTION_ENERGY      ; carry is clear here
        cmp #ENERGY_MAX + 1
        bcc energy_ready
        lda #ENERGY_MAX
energy_ready:
        sta energy
        sec
        rts
leave_object:
        clc
        rts
take_key:
        tax
        lda key_bits-1,x
        ora key_set
        sta key_set
        sec
        rts
take_seal:
        inc seals
add_points:                     ; seal or treasure
        ldx obj_kind
        lda points_low-KIND_SEAL,x
        sta gain_low
        lda points_middle-KIND_SEAL,x
        sta gain_middle
        jsr add_score
        sec
        rts

; --- add_score -----------------------------------------
; score += gain_middle, gain_low (BCD, four digits). The
; music interrupt must never run in decimal mode:
; interrupts stay off while the D flag is set.
add_score:
        sei
        sed
        clc
        lda score+2
        adc gain_low
        sta score+2
        lda score+1
        adc gain_middle
        sta score+1
        lda score
        adc #0
        sta score
        cld
        cli
        lda #1
        sta hud_dirty
        rts

; --- Tables --------------------------------------------
key_bits:       .byte 1, 2, 4, 8        ; doors A-C, portal
bit_masks:      .byte 1, 2, 4, 8, 16, 32, 64, 128
sprite_bits:    .byte 1 << FIRST_SPRITE, 2 << FIRST_SPRITE
; By kind 1-6: key A, key B, key C, seal, treasure, potion
object_frames:  .byte OBJECT_POINTER, OBJECT_POINTER
                .byte OBJECT_POINTER, OBJECT_POINTER + 1
                .byte OBJECT_POINTER + 2, OBJECT_POINTER + 3
object_colours: .byte YELLOW, YELLOW, YELLOW, LIGHT_GREEN
                .byte YELLOW, WHITE
points_low:     .byte $00, $50  ; seal 1000, treasure 250
points_middle:  .byte $10, $02

; --- Variables -------------------------------------------
obj_slot:   .byte 0
obj_kind:   .byte 0
obj_col:    .byte 0
obj_row:    .byte 0
obj_number: .byte 0
obj_x:      .byte 0
obj_x_high: .byte 0
hero_col:   .byte 0
hero_row:   .byte 0
door_col:   .byte 0     ; show_door: tile being drawn
door_row:   .byte 0
door_index: .byte 0     ; show_door: offset in the list
gain_low:   .byte 0     ; points for add_score, BCD
gain_middle: .byte 0

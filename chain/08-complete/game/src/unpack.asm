; CRYPTMORROW - unpack.
; The PRG holds the data blocks one after the other
; behind the code (data.asm), so that it has no holes
; and loads faster from disk. At the start, unpack puts
; each block at its address: the last block first, and
; each one from its last byte back to its first.

; --- unpack --------------------------------------------
; Copies the BLOCK_COUNT blocks of the table to their
; addresses. Uses src_ptr, fill_ptr and copy_len.
unpack:
        ldx #(BLOCK_COUNT - 1) * 6
unpack_block:
        lda blocks,x            ; source in the PRG
        sta src_ptr
        lda blocks+1,x
        sta src_ptr+1
        lda blocks+2,x          ; address
        sta fill_ptr
        lda blocks+3,x
        sta fill_ptr+1
        lda blocks+4,x          ; length
        sta copy_len
        lda blocks+5,x
        sta copy_len+1
        jsr copy_back
        txa                     ; the block before
        sec
        sbc #6
        tax
        bcs unpack_block        ; until below the first
        rts

; --- copy_back -----------------------------------------
; Copies copy_len bytes from src_ptr to fill_ptr, the
; last byte first: right even when the two overlap and
; the destination is higher. Keeps X.
copy_back:
        lda src_ptr+1           ; point both at the last
        clc                     ; page, maybe not full
        adc copy_len+1
        sta src_ptr+1
        lda fill_ptr+1
        clc
        adc copy_len+1
        sta fill_ptr+1
        ldy copy_len            ; bytes on that page
        beq whole_pages
copy_byte:
        dey
        lda (src_ptr),y
        sta (fill_ptr),y
        tya
        bne copy_byte
whole_pages:
        lda copy_len+1          ; full pages below?
        beq copied
        dec copy_len+1
        dec src_ptr+1
        dec fill_ptr+1
        jmp copy_byte           ; Y = 0: 256 bytes
copied:
        rts

; --- The table of the blocks ---------------------------
; Source in the PRG, address, length; in the order of
; the PRG, which is also the order of the addresses.
blocks:
        .word b_hero, SPRITE_DATA, b_objects - b_hero
        .word b_objects, OBJECT_SPRITES
        .word b_combat - b_objects
        .word b_combat, COMBAT_SPRITES, b_big - b_combat
        .word b_big, BIG_FONT, b_styles - b_big
        .word b_styles, BIG_STYLES, b_tiles - b_styles
        .word b_tiles, TILE_BITMAP, b_attr - b_tiles
        .word b_attr, TILE_ATTR, b_flames - b_attr
        .word b_flames, FLAMES, b_font - b_flames
        .word b_font, FONT, b_doors - b_font
        .word b_doors, DOOR_TILES, b_pages - b_doors
        .word b_pages, TITLE_PAGE, b_rooms - b_pages
        .word b_rooms, ROOM_DATA, b_zones - b_rooms
        .word b_zones, ZONE_COLOURS, b_music - b_zones
        .word b_music, MUSIC_DATA, packed_end - b_music
blocks_end:
BLOCK_COUNT = (blocks_end - blocks) / 6

; unpack is safe if no block lies above its address.
; Sources and addresses both go up, and no block runs
; into the next address: checking the first is enough.
        .cerror b_hero > SPRITE_DATA, "packed data too high"

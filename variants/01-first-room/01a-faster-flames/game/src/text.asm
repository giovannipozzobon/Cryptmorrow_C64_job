; CRYPTMORROW - text: one glyph per cell of the bitmap.
; A string is: column, row, colour, glyph codes, $ff.
; The codes follow game/assets/font.py: space 0,
; A-Z 1-26, 0-9 27-36, - : . / 37-40, rule 41,
; HUD icons 42-44: energy block, key, seal; cursor 45.

TEXT_END = $ff

; --- print_text ----------------------------------------
; Draws the string at text_ptr. Glyph pixels use code 01,
; so each cell takes its colour from the screen RAM
; high nibble; Color RAM is not touched.
print_text:
        ldy #0
        lda (text_ptr),y        ; column 0-39
        sta text_col
        iny
        lda (text_ptr),y        ; cell row 0-24
        tax
        iny
        lda (text_ptr),y        ; colour 0-15
        asl a                   ; into the high nibble
        asl a
        asl a
        asl a
        sta text_colour

; Screen RAM: SCREEN + row * 40 + column.
        lda text_col
        clc
        adc screen_rows_lo,x
        sta text_scr
        lda screen_rows_hi,x
        adc #0
        sta text_scr+1

; Bitmap: BITMAP + row * 320 + column * 8.
        lda #0
        sta text_bmp+1
        lda text_col
        asl a
        asl a
        asl a                   ; only this one can carry
        rol text_bmp+1
        clc
        adc bitmap_rows_lo,x
        sta text_bmp
        lda text_bmp+1
        adc bitmap_rows_hi,x
        sta text_bmp+1

        lda #3                  ; first glyph code
        sta text_pos
print_char:
        ldy text_pos
        lda (text_ptr),y
        cmp #TEXT_END
        beq print_done
        ldx #0                  ; glyph = FONT + code * 8
        stx glyph_ptr+1
        asl a
        rol glyph_ptr+1
        asl a
        rol glyph_ptr+1
        asl a
        rol glyph_ptr+1
        clc
        adc #<FONT
        sta glyph_ptr
        lda glyph_ptr+1
        adc #>FONT
        sta glyph_ptr+1
        ldy #7
copy_glyph:
        lda (glyph_ptr),y
        sta (text_bmp),y
        dey
        bpl copy_glyph
        ldy #0
        lda text_colour
        sta (text_scr),y
        clc                     ; next cell: 8 bytes on
        lda text_bmp
        adc #8
        sta text_bmp
        bcc glyph_page
        inc text_bmp+1
glyph_page:
        inc text_scr            ; and one screen byte
        bne glyph_done
        inc text_scr+1
glyph_done:
        inc text_pos
        bne print_char          ; strings are short
print_done:
        rts

screen_rows_lo: .byte <(SCREEN + range(25) * 40)
screen_rows_hi: .byte >(SCREEN + range(25) * 40)
bitmap_rows_lo: .byte <(BITMAP + range(25) * 320)
bitmap_rows_hi: .byte >(BITMAP + range(25) * 320)

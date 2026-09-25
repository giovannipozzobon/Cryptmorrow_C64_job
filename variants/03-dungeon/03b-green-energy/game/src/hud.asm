; CRYPTMORROW - the HUD: energy, keys, seals and score
; on cell row 1, a rule under them and one over the
; room name. print_hud draws everything once; later
; hud_update rewrites only the values, when something
; has set hud_dirty.

HUD_ROW      = 1
ENERGY_MAX   = 8        ; cells of the energy bar
BAR_COLUMN   = 8
KEYS_COLUMN  = 19       ; digit after the key icon
SEALS_COLUMN = 23       ; digit after the seal icon
SCORE_COLUMN = 34       ; first of six digits
GLYPH_ZERO   = 27       ; glyph code of the digit 0
BAR_SCREEN   = SCREEN + HUD_ROW * 40 + BAR_COLUMN
RULE_LENGTH  = 36

; --- print_hud -----------------------------------------
print_hud:
        lda #<hud_frame
        ldy #>hud_frame
        jsr print_list
; --- hud_update ----------------------------------------
; The glyphs of the energy bar never change: a full
; cell is light red, a lost one dark grey. Only the
; colour byte in screen RAM is rewritten.
hud_update:
        lda #0
        sta hud_dirty
        ldx #0                  ; cell of the bar
bar_cell:
        lda #DARK_GREY << 4
        cpx energy
        bcs bar_colour          ; cell >= energy: lost
        lda #LIGHT_GREEN << 4
bar_colour:
        sta BAR_SCREEN,x
        inx
        cpx #ENERGY_MAX
        bne bar_cell

        lda #KEYS_COLUMN
        sta digit_text          ; column of the digit
        ldx #0                  ; keys carried: count the
        lda key_set             ; bits of key_set
count_keys:
        beq keys_counted
        lsr a
        bcc count_keys
        inx
        bcs count_keys          ; always: carry is set
keys_counted:
        txa
        jsr print_digit
        lda #SEALS_COLUMN
        sta digit_text
        lda seals
        jsr print_digit

        lda #SCORE_COLUMN
        sta digit_text
; --- print_score ---------------------------------------
; The six digits of score from column digit_text, on the
; row in digit_text+1: three bytes, two BCD digits each.
print_score:
        lda #0
        sta score_byte
score_digits:
        ldx score_byte
        lda score,x
        lsr a                   ; high digit
        lsr a
        lsr a
        lsr a
        jsr print_digit
        ldx score_byte
        lda score,x
        and #$0f                ; low digit
        jsr print_digit
        inc score_byte
        lda score_byte
        cmp #3
        bne score_digits
        rts

; --- print_digit ---------------------------------------
; Prints digit A (0-9) on the row in digit_text+1 (the
; HUD row, except for the end screen) at the column in
; digit_text, then moves that column one to the right.
; print_text uses X and Y: callers keep their counters
; in memory.
print_digit:
        clc
        adc #GLYPH_ZERO
        sta digit_text+3        ; the only glyph
        lda #<digit_text
        ldy #>digit_text
        jsr print_at
        inc digit_text
        rts

digit_text:
        .byte 0, HUD_ROW, WHITE, 0, TEXT_END
score_byte:
        .byte 0

; --- The fixed part: labels, icons, rules -------------
        .enc "glyphs"
hud_frame:
        .byte 1, HUD_ROW, LIGHT_GREY
        .text "ENERGY"
        .byte TEXT_END
        .byte BAR_COLUMN, HUD_ROW, LIGHT_GREEN
        .text "*" x ENERGY_MAX
        .byte TEXT_END
        .byte KEYS_COLUMN - 1, HUD_ROW, YELLOW
        .text "+"
        .byte TEXT_END
        .byte SEALS_COLUMN - 1, HUD_ROW, LIGHT_GREEN
        .text "@"
        .byte TEXT_END
        .byte SEALS_COLUMN + 1, HUD_ROW, GREY
        .text "/3"
        .byte TEXT_END
        .byte SCORE_COLUMN - 6, HUD_ROW, LIGHT_GREY
        .text "SCORE"
        .byte TEXT_END
        .byte 2, HUD_ROW + 1, GREEN
        .text "~" x RULE_LENGTH
        .byte TEXT_END
        .byte 2, 23, GREEN      ; over the room name
        .text "~" x RULE_LENGTH
        .byte TEXT_END
        .byte TEXT_END          ; end of the list
        .enc "none"

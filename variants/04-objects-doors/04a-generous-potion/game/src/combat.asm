; CRYPTMORROW - the end of a game: VICTORY takes the
; place of the room's name and the game stops. The
; next step adds the combat to this file.

ENDED_WON     = 2       ; game_ended: VICTORY
; --- victory -------------------------------------------
; The end of a game: the room stops, VICTORY (out
; through the portal) takes the place of its name.
victory:
        lda #ENDED_WON
        ldx #<won_text
        ldy #>won_text
game_ends:
        sta game_ended
        stx end_text
        sty end_text+1
        jsr clear_name_row
        lda end_text
        ldy end_text+1
        jmp print_at

        .enc "glyphs"
won_text:
        .byte 16, 24, YELLOW
        .text "VICTORY"
        .byte TEXT_END
        .enc "none"

; --- The end of a game ---------------------------------
game_ended:   .byte 0   ; ENDED_LOST or ENDED_WON
end_text:     .word 0   ; game_ends: the string

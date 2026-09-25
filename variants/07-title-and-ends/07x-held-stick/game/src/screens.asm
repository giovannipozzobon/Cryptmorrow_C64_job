; CRYPTMORROW - the states of the program: the
; title with its menu, the game, the end of a game in
; the room, the end screen; big letters for the words.
; Each screen is a page like a room's (title, GAME OVER,
; VICTORY), drawn by draw_room, with words printed on
; its black places.

STATE_TITLE   = 0       ; game_state: what main_loop runs
STATE_PLAY    = 1
STATE_ENDING  = 2       ; the room stands still a moment
STATE_END     = 3       ; the end screen
ENDING_FRAMES = 50      ; one second in the room
END_DELAY     = 100     ; two seconds before Fire counts
MENU_ROW      = 18      ; MUSIC, SOUND FX, SILENT
MENU_COLUMN   = 15      ; where the cursor goes
CURSOR        = 45      ; glyph code of the cursor
PROMPT_ROW    = 22      ; PRESS FIRE
PROMPT_COLUMN = 15
PROMPT_LENGTH = 10
STATS_ROW     = 18      ; SCORE, SEALS, ROOMS
STATS_COLUMN  = 14
VALUE_COLUMN  = 21
ROOM_COUNT    = 16
TITLE_HERO_Y  = 98      ; the explorer before the gate
SKELETON_X    = 70      ; the title's enemies, screen
SKELETON_Y    = 98      ; coordinates like the explorer
BAT_X         = 226
BAT_Y         = 74
STYLE_LOGO    = 0       ; big word colours in BIG_STYLES
STYLE_LOST    = 1
STYLE_WON     = 2

; --- run_state -----------------------------------------
; Jumps to the routine of game_state; it returns to the
; main loop. The table holds each address minus one,
; because rts adds one to the address it takes.
run_state:
        lda game_state
        asl a                   ; two bytes an address
        tax
        lda state_code+1,x
        pha
        lda state_code,x
        pha
        rts

state_code:
        .word title_frame-1, play_frame-1
        .word ending_frame-1, end_frame-1

; --- show_title ----------------------------------------
; Draws the title screen and starts the chosen audio
; mode again (the theme from its beginning).
show_title:
        jsr screen_off
        lda #STATE_TITLE
        sta game_state
        lda #0
        sta fire_armed
        lda #0                  ; a stick already pushed
        and #JOY_UP | JOY_DOWN  ; does not move the cursor
        sta stick_held
        lda audio_mode
        jsr set_audio
        lda #>TITLE_PAGE
        jsr draw_screen
title_drawn:
        lda #<logo_text
        ldy #>logo_text
        jsr print_big
        jsr show_menu
        lda #<prompt_text
        ldy #>prompt_text
        jsr print_at
        jsr title_sprites
        jmp screen_on

; --- title_frame ---------------------------------------
title_frame:
        jsr move_cursor
        jsr animate_title
        jsr fire_released
        bcc title_waits
        jmp start_game
title_waits:
        rts

; --- move_cursor ---------------------------------------
; Up and down move the cursor through the three modes,
; one line each time the stick leaves the centre. The
; mode changes at once, so that it can be heard: FX plays
; an effect as a sample.
move_cursor:
        lda joy_state
        and #JOY_UP | JOY_DOWN
        cmp stick_held
        sta stick_held
        beq cursor_done         ; no change
        tax
        beq cursor_done         ; back to the centre
        and #JOY_UP             ; up wins over down
        beq cursor_down
        ldx audio_mode
        beq cursor_done         ; on the first line
        dex
        jmp cursor_moved
cursor_down:
        ldx audio_mode
        cpx #MODE_SILENT
        beq cursor_done         ; on the last line
        inx
cursor_moved:
        txa
        jsr set_audio
        jsr show_menu
        lda audio_mode
        cmp #MODE_FX
        bne cursor_done
        lda #FX_PICKUP
        jmp sound_effect
cursor_done:
        rts

; --- show_menu -----------------------------------------
; The three lines of the menu: the chosen one yellow with
; the cursor, the others grey.
show_menu:
        ldx #2
menu_line:
        stx menu_index
        lda menu_lo,x
        sta text_ptr
        lda menu_hi,x
        sta text_ptr+1
        lda #GREY
        ldy #0                  ; a space
        cpx audio_mode
        bne line_ready
        lda #YELLOW
        ldy #CURSOR
line_ready:
        sta menu_colour
        tya
        ldy #3                  ; first glyph: the cursor
        sta (text_ptr),y
        dey
        lda menu_colour
        sta (text_ptr),y        ; colour of the line
        jsr print_text
        ldx menu_index
        dex
        bpl menu_line
        rts

; --- title_sprites, animate_title ----------------------
; The explorer stands before the gate, a skeleton and a
; bat on either side: the skeleton steps on the spot,
; the bat flutters up and down.
title_sprites:
        jsr init_hero           ; sprite 0, shared colours
        lda #TITLE_HERO_Y
        sta hero_y
        lda #0
        sta $d010               ; every X below 256
        jsr place_hero
        lda #%00001101          ; explorer and enemies
        sta $d01c               ; multicolour
        sta $d015
        lda #LIGHT_GREY
        sta $d027+2
        lda #PURPLE
        sta $d027+3
        lda #SKELETON_X + 24
        sta $d004
        lda #SKELETON_Y + 50
        sta $d005
        lda #BAT_X + 24
        sta $d006
animate_title:
        lda frame_count         ; skeleton: a new frame
        lsr a                   ; every 8
        lsr a
        lsr a
        and #1
        clc
        adc #SKELETON_FRAME
        sta SPRITE_PTRS+2
        lda frame_count         ; bat: every 4
        lsr a
        lsr a
        tax
        and #1
        clc
        adc #BAT_FRAME
        sta SPRITE_PTRS+3
        txa
        and #7
        tax
        lda bat_bob,x
        clc
        adc #BAT_Y + 50
        sta $d007
; PRESS FIRE glows: its colour changes every 4 frames.
pulse_prompt:
        lda frame_count
        lsr a
        lsr a
        and #7
        tax
        lda prompt_colours,x
        ldx #PROMPT_LENGTH - 1
prompt_colour:
        sta SCREEN + PROMPT_ROW * 40 + PROMPT_COLUMN,x
        dex
        bpl prompt_colour
        rts

; --- fire_released -------------------------------------
; Carry set when Fire is let go after a press seen here
; (fire_armed): release, press, release, as in volume 1.
fire_released:
        lda joy_state
        and #JOY_FIRE
        cmp fire_held
        sta fire_held
        beq not_released        ; no change
        tax
        bne fire_pressed
        lda fire_armed          ; let go: after a press?
        beq not_released
        sec
        rts
fire_pressed:
        lda #1
        sta fire_armed
not_released:
        clc
        rts

; --- start_game ----------------------------------------
; From the title: a new game in the chosen audio mode.
start_game:
        jsr screen_off
        lda audio_mode
        jsr set_audio           ; the theme from its start
        jsr clear_screen
        jsr init_game
        jsr print_hud
        lda #STATE_PLAY
        sta game_state
        jsr init_hero
        jmp enter_room          ; the start room, shown

; --- ending_frame --------------------------------------
; GAME OVER or VICTORY stands in the room for a second,
; then comes the end screen.
ending_frame:
        dec end_timer
        bne ending_waits
        jmp show_end
ending_waits:
        rts

; --- show_end ------------------------------------------
; The end screen of game_ended: its page and big word,
; the score, the seals and the rooms explored. PRESS FIRE
; comes after END_DELAY frames.
show_end:
        jsr screen_off
        lda #STATE_END
        sta game_state
        lda #END_DELAY
        sta end_timer
        lda #0
        sta fire_armed
        lda game_ended
        cmp #ENDED_WON
        beq won_screen
        lda #>OVER_PAGE
        jsr draw_screen
        lda #<lost_word
        ldy #>lost_word
        jmp end_word
won_screen:
        lda #>WON_PAGE
        jsr draw_screen
        lda #<won_word
        ldy #>won_word
end_word:
        jsr print_big
        jsr print_stats
        jmp screen_on

; --- end_frame -----------------------------------------
; Fire is followed but does not count during END_DELAY;
; then PRESS FIRE appears, glows, and Fire leads back to
; the title.
end_frame:
        lda end_timer
        beq end_ready
        jsr fire_released       ; only to follow the button
        lda #0
        sta fire_armed          ; presses do not count yet
        dec end_timer
        bne end_done
        lda #<prompt_text
        ldy #>prompt_text
        jmp print_at            ; PRESS FIRE appears
end_ready:
        jsr pulse_prompt
        jsr fire_released
        bcc end_done
        jmp show_title
end_done:
        rts

; --- print_stats ---------------------------------------
; SCORE, SEALS and ROOMS with their values. print_digit
; writes on the row in digit_text+1: the HUD row after.
print_stats:
        lda #<stats_text
        ldy #>stats_text
        jsr print_list
        lda #STATS_ROW
        sta digit_text+1
        lda #VALUE_COLUMN
        sta digit_text
        jsr print_score
        inc digit_text+1        ; next row: the seals
        lda #VALUE_COLUMN
        sta digit_text
        lda seals
        jsr print_digit
        inc digit_text+1        ; next row: the rooms
        lda #VALUE_COLUMN
        sta digit_text
        ldx #0                  ; count the bits of
        lda rooms_seen          ; rooms_seen
        jsr count_bits
        lda rooms_seen+1
        jsr count_bits
        txa
        ldy #0                  ; tens
tens_loop:
        cmp #10
        bcc tens_done
        sbc #10                 ; carry is set
        iny
        bne tens_loop           ; always
tens_done:
        sta ones_digit
        tya
        jsr print_digit
        lda ones_digit
        jsr print_digit
        lda #HUD_ROW
        sta digit_text+1
        rts

; X += the number of 1 bits in A.
count_bits:
        beq bits_counted
        lsr a
        bcc count_bits
        inx
        bcs count_bits          ; always: carry is set
bits_counted:
        rts

; --- draw_screen ---------------------------------------
; A = high byte of a screen page: a black screen, then
; the page drawn like a room, in the colours of its zone.
draw_screen:
        pha
        jsr clear_screen
        pla
        sta room_ptr+1
        sta page_ptr+1
        lda #0
        sta room_ptr
        sta page_ptr
        jsr set_zone
        jmp draw_room

; --- screen_off, screen_on -----------------------------
screen_off:
        lda #$0b                ; display off
        sta $d011
        lda #0
        sta $d015               ; no sprites
        rts

screen_on:
        jsr animate_torches     ; flames in step at once
        jsr wait_frame
        lda #$3b                ; display on
        sta $d011
screen_shown:
        rts

; --- print_big -----------------------------------------
; A/Y = a string of big letters: column, row, style,
; glyph codes (1-26 A-Z, 0 a space), TEXT_END. Each
; letter is 3 x 5 cells from BIG_FONT; the style gives
; each of the five cell rows its screen RAM byte and its
; Color RAM colour.
print_big:
        sta text_ptr
        sty text_ptr+1
        ldy #0
        lda (text_ptr),y
        sta big_column
        iny
        lda (text_ptr),y
        sta big_row
        iny
        lda (text_ptr),y        ; style * 16
        asl a
        asl a
        asl a
        asl a
        sta big_style
        lda #3
        sta text_pos
big_letter:
        ldy text_pos
        lda (text_ptr),y
        cmp #TEXT_END
        beq big_done
        tax
        beq big_next            ; a space: nothing drawn
        lda big_lo-1,x
        sta glyph_ptr
        lda big_hi-1,x
        sta glyph_ptr+1
        jsr big_glyph
big_next:
        lda big_column          ; three cells on
        clc
        adc #3
        sta big_column
        inc text_pos
        bne big_letter          ; always
big_done:
        rts

; One letter at big_column, big_row, from glyph_ptr.
big_glyph:
        lda #0
        sta big_line
glyph_row:
        lda big_row
        clc
        adc big_line
        tax                     ; cell row on the screen
        lda #0                  ; bitmap: row start
        sta text_bmp+1          ; + column * 8
        lda big_column
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
        lda big_column          ; screen RAM and Color RAM
        clc
        adc screen_rows_lo,x
        sta text_scr
        sta big_colour
        lda screen_rows_hi,x
        adc #0
        sta text_scr+1
        clc
        adc #>(COLOR_RAM - SCREEN)
        sta big_colour+1
        ldy #23                 ; three cells side by side
copy_big:                       ; are 24 bitmap bytes
        lda (glyph_ptr),y
        sta (text_bmp),y
        dey
        bpl copy_big
        lda big_style           ; colours of this row
        clc
        adc big_line
        tax
        ldy #2
colour_big:
        lda BIG_STYLES,x        ; screen RAM byte
        sta (text_scr),y
        lda BIG_STYLES+5,x      ; Color RAM colour
        sta (big_colour),y
        dey
        bpl colour_big
        lda glyph_ptr           ; next row of the letter
        clc
        adc #24
        sta glyph_ptr
        bcc glyph_moved
        inc glyph_ptr+1
glyph_moved:
        inc big_line
        lda big_line
        cmp #5
        bne glyph_row
        rts

big_lo: .byte <(BIG_FONT + range(26) * 120)
big_hi: .byte >(BIG_FONT + range(26) * 120)

; --- Tables and strings --------------------------------
bat_bob:        .byte 0, 1, 2, 3, 3, 2, 1, 0
prompt_colours: .byte DARK_GREY << 4, GREY << 4
                .byte LIGHT_GREY << 4, WHITE << 4
                .byte WHITE << 4, LIGHT_GREY << 4
                .byte GREY << 4, DARK_GREY << 4
menu_lo:        .byte <menu_music, <menu_fx, <menu_silent
menu_hi:        .byte >menu_music, >menu_fx, >menu_silent

        .enc "glyphs"
logo_text:
        .byte 4, 1, STYLE_LOGO
        .text "CRYPTMORROW"
        .byte TEXT_END
lost_word:
        .byte 7, 1, STYLE_LOST
        .text "GAME OVER"
        .byte TEXT_END
won_word:
        .byte 10, 1, STYLE_WON
        .text "VICTORY"
        .byte TEXT_END
menu_music:                     ; the first glyph is the
        .byte MENU_COLUMN, MENU_ROW, GREY       ; cursor
        .text "  MUSIC"
        .byte TEXT_END
menu_fx:
        .byte MENU_COLUMN, MENU_ROW + 1, GREY
        .text "  SOUND FX"
        .byte TEXT_END
menu_silent:
        .byte MENU_COLUMN, MENU_ROW + 2, GREY
        .text "  SILENT"
        .byte TEXT_END
prompt_text:
        .byte PROMPT_COLUMN, PROMPT_ROW, WHITE
        .text "PRESS FIRE"
        .byte TEXT_END
stats_text:
        .byte STATS_COLUMN, STATS_ROW, LIGHT_GREY
        .text "SCORE"
        .byte TEXT_END
        .byte STATS_COLUMN, STATS_ROW + 1, LIGHT_GREY
        .text "SEALS"
        .byte TEXT_END
        .byte STATS_COLUMN, STATS_ROW + 2, LIGHT_GREY
        .text "ROOMS"
        .byte TEXT_END
        .byte VALUE_COLUMN + 1, STATS_ROW + 1, WHITE
        .text "/3"
        .byte TEXT_END
        .byte VALUE_COLUMN + 2, STATS_ROW + 2, WHITE
        .text "/16"
        .byte TEXT_END
        .byte TEXT_END          ; end of the list
        .enc "none"

; --- State ---------------------------------------------
game_state:  .byte 0    ; STATE_ value
end_timer:   .byte 0    ; frames of ENDING or END_DELAY
fire_armed:  .byte 0    ; 1: Fire pressed in this state
stick_held:  .byte 0    ; up/down bits of the last frame
menu_index:  .byte 0
menu_colour: .byte 0
ones_digit:  .byte 0
big_column:  .byte 0    ; print_big: next letter
big_row:     .byte 0
big_style:   .byte 0    ; style * 16
big_line:    .byte 0    ; row of the letter, 0-4

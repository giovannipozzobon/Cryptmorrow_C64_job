; CRYPTMORROW - sound: three SID voices, updated once per
; frame by a raster interrupt. In MUSIC mode they play a
; song, in FX mode voice 1 plays the sound effects, in
; SILENT mode nothing. The data comes from
; game/assets/score.py and sfx.py, compiled to music.asm.
;
; pattern bytes  $00-$5d note, $60 rest,
;                $80-$bf length (value - $7f steps),
;                $c0-$df instrument, $ff end
; order bytes    $00-$7f pattern, $80-$bf transpose
;                (value - $a0), $ff n: go to entry n
; wave tables    control + argument per frame: argument
;                $00-$7f semitones above the note,
;                $80 + n fixed note n; $ff n jump, $fe hold
; effects        fx_ctrl and fx_note: control byte (gate
;                included) and note of each frame; FX_END

SID         = $d400
NOTE_REST   = $60
CMD_LENGTH  = $80
CMD_INSTR   = $c0
PAT_END     = $ff
ORDER_LOOP  = $ff
TRANS_ZERO  = $a0
WAVE_LOOP   = $ff
WAVE_END    = $fe
IRQ_LINE    = 250       ; raster line of the interrupt
KERNAL_EXIT = $ea81     ; KERNAL: restore Y, X, A; RTI
MODE_MUSIC  = 0         ; the values of audio_mode
MODE_FX     = 1
MODE_SILENT = 2
VOLUME      = $0f       ; $d418: volume 15, no filter

; --- start_audio ---------------------------------------
; Prepares audio_mode, then hooks audio_irq to raster line
; IRQ_LINE through the KERNAL vector at $0314.
start_audio:
        lda audio_mode
        jsr set_audio
        lda #<audio_irq
        sta $0314
        lda #>audio_irq
        sta $0315
        lda #IRQ_LINE
        sta $d012
        lda $d011
        and #$7f                ; raster bit 8 = 0
        sta $d011
        lda #1
        sta $d01a               ; raster interrupt on
        sta $d019               ; clear an old request
        cli
        rts

; The KERNAL saved A, X and Y before jumping here.
audio_irq:
        lda #1
        sta $d019               ; acknowledge the raster
        jsr audio_frame
irq_done:
        jmp KERNAL_EXIT

; --- set_audio -----------------------------------------
; A = MODE_MUSIC, MODE_FX or MODE_SILENT: the theme from
; its beginning, or three silent voices (volume 0 in
; SILENT mode). No effect is left waiting. The interrupt
; is held off meanwhile.
set_audio:
        sei
        sta audio_mode
        lda #0
        sta fx_next
        sta fx_pos
        sta fx_prio
        lda audio_mode
        bne no_music            ; MODE_MUSIC is 0
        lda #SONG_THEME
        jsr music_init
        cli
        rts
no_music:
        jsr sid_silence
        lda audio_mode
        cmp #MODE_SILENT
        bne audio_ready
        lda #0
        sta sid_shadow+24       ; volume 0
audio_ready:
        cli
        rts

; --- sid_silence ---------------------------------------
; Every SID register and its shadow to 0, volume 15.
sid_silence:
        ldx #24
        lda #0
clear_sid:
        sta sid_shadow,x
        sta SID,x
        dex
        bpl clear_sid
        lda #VOLUME
        sta sid_shadow+24
        rts

; --- music_init ----------------------------------------
; A = song (SONG_THEME, SONG_WON, SONG_LOST): the player
; starts it from the beginning. Call with the interrupt
; held off.
music_init:
        sta music_song
        jsr sid_silence
        lda #0
        sta music_tick
        sta music_frames
        sta music_frames+1
        ldx #VOICE_BYTES - 1    ; every voice variable
clear_voices:                   ; starts at zero
        sta v_order,x
        dex
        bpl clear_voices
        lda music_song          ; three order lists a song
        asl a
        adc music_song          ; carry is clear: song * 3
        tay
        ldx #0
song_voice:
        lda song_order_lo,y
        sta v_ordlo,x
        lda song_order_hi,y
        sta v_ordhi,x
        iny
        inx
        cpx #3
        bne song_voice
        ldx #2
init_voice:
        lda #1
        sta v_len,x
        jsr next_pattern        ; first pattern of voice X
        dex
        bpl init_voice
        rts

; --- audio_frame ---------------------------------------
; 1. send the registers computed last frame, so the SID
;    changes at the same raster position every frame;
; 2. compute the next frame of the music or the effect.
audio_frame:
        ldx #24                 ; from $d418 down: AD and
flush_sid:                      ; SR before the control
        lda sid_shadow,x
        sta SID,x
        dex
        bpl flush_sid
        inc irq_frames          ; every interrupt counts
        bne irq_counted
        inc irq_frames+1
irq_counted:
        lda audio_mode
        beq music_play          ; MODE_MUSIC
        cmp #MODE_FX
        beq fx_play
        rts                     ; MODE_SILENT

; --- music_play ----------------------------------------
; Compute the next frame of each voice, then advance the
; frame inside the step.
music_play:
        ldx #2
play_voice:
        jsr voice_frame
        dex
        bpl play_voice
        inc music_tick
        lda music_tick
        cmp #MUSIC_SPEED
        bne tick_ready
        lda #0
        sta music_tick
tick_ready:
        inc music_frames
        bne play_done
        inc music_frames+1
play_done:
        rts

; --- fx_play -------------------------------------------
; Starts the effect asked for by sound_effect, if any,
; then sends the next frame of the effect to voice 1.
fx_play:
        ldx fx_next
        beq fx_step             ; nothing new
        lda #0
        sta fx_next
        sta sid_shadow+2        ; pulse width, low byte
        lda fx_first-1,x
        sta fx_pos
        lda fx_ad-1,x
        sta sid_shadow+5
        lda fx_sr-1,x
        sta sid_shadow+6
        lda fx_pulse-1,x
        sta sid_shadow+3
fx_step:
        ldy fx_pos
        beq fx_done             ; no effect playing
        lda fx_ctrl,y
        cmp #FX_END
        beq fx_over
        sta sid_shadow+4        ; waveform and gate
        ldx fx_note,y
        lda note_lo,x
        sta sid_shadow
        lda note_hi,x
        sta sid_shadow+1
        inc fx_pos
fx_done:
        rts
fx_over:
        lda #0                  ; the note is released:
        sta fx_pos              ; any effect may come
        sta fx_prio
        rts

; --- sound_effect --------------------------------------
; A = FX_ number. In FX mode, asks the interrupt to start
; that effect, unless a more important one is playing or
; was asked for in this frame. X and Y are kept.
sound_effect:
        stx fx_keep_x
        ldx audio_mode
        cpx #MODE_FX
        bne effect_done
        tax
        lda fx_priority-1,x
        sei                     ; fx_prio is shared with
        cmp fx_prio             ; the interrupt
        bcc effect_refused      ; less important
        sta fx_prio
        stx fx_next
effect_refused:
        cli
effect_done:
        ldx fx_keep_x
        rts

; --- end_sound -----------------------------------------
; A = ENDED_LOST or ENDED_WON: the short piece of the end
; in MUSIC mode, the effect in FX mode.
end_sound:
        ldx audio_mode
        bne end_effect
        cmp #ENDED_WON
        beq won_song
        lda #SONG_LOST
        bne end_song            ; always
won_song:
        lda #SONG_WON
end_song:
        sei
        jsr music_init
        cli
        rts
end_effect:
        cmp #ENDED_WON
        beq won_effect
        lda #FX_LOST
        jmp sound_effect
won_effect:
        lda #FX_WON
        jmp sound_effect

; --- voice_frame (X = voice 0-2) -----------------------
voice_frame:
        lda music_tick
        bne mid_step
        lda v_steps,x           ; first frame of a step
        bne step_counted
        jsr next_event          ; event over: read more
step_counted:
        dec v_steps,x
        jmp update_sound
mid_step:
        cmp #MUSIC_GATE_TICK
        bne update_sound
        lda v_steps,x
        bne update_sound        ; not the last step
        lda #0                  ; release the note so the
        sta v_gate,x            ; next one attacks again

; Wave table: waveform and note of this frame.
update_sound:
        ldy v_wave,x
wave_read:
        lda wave_ctrl,y
        cmp #WAVE_END
        beq wave_hold           ; keep the last entry
        cmp #WAVE_LOOP
        bne wave_step
        lda wave_arg,y          ; jump inside the table
        tay
        jmp wave_read
wave_step:
        sta v_ctrl,x
        lda wave_arg,y
        bmi wave_fixed
        clc                     ; semitones above the note
        adc v_note,x
        jmp wave_note
wave_fixed:
        and #$7f                ; fixed note (drums)
wave_note:
        sta v_wnote,x
        iny
wave_hold:
        tya
        sta v_wave,x

; Frequency of the note, plus the vibrato offset.
        ldy v_wnote,x
        lda note_lo,y
        sta freq_lo
        lda note_hi,y
        sta freq_hi
        ldy v_instr,x
        lda ins_vibdepth,y
        beq vibrato_done
        lda v_age,x
        cmp ins_vibdelay,y
        bcc vibrato_done        ; not yet
        lda v_vibph,x           ; phases 2-5 go down,
        and #7                  ; the others go up: a
        inc v_vibph,x           ; triangle 8 frames long
        tay
        lda vib_down,y
        pha
        ldy v_instr,x
        pla
        bne vibrato_down
        clc
        lda v_viblo,x
        adc ins_vibdepth,y
        sta v_viblo,x
        lda v_vibhi,x
        adc #0
        sta v_vibhi,x
        jmp vibrato_add
vibrato_down:
        sec
        lda v_viblo,x
        sbc ins_vibdepth,y
        sta v_viblo,x
        lda v_vibhi,x
        sbc #0
        sta v_vibhi,x
vibrato_add:
        clc
        lda freq_lo
        adc v_viblo,x
        sta freq_lo
        lda freq_hi
        adc v_vibhi,x
        sta freq_hi
vibrato_done:
        lda v_age,x
        cmp #$ff
        beq age_done
        inc v_age,x
age_done:

; Pulse width sweep, turning at $0e00 and $0200.
        ldy #0
        lda v_pwspd,x
        beq pulse_done
        bpl pulse_add
        dey                     ; negative: high byte $ff
pulse_add:
        clc
        adc v_pwlo,x
        sta v_pwlo,x
        tya
        adc v_pwhi,x
        sta v_pwhi,x
        cmp #$0e
        bcs pulse_turn
        cmp #$02
        bcs pulse_done
pulse_turn:
        lda v_pwspd,x           ; two's complement:
        eor #$ff                ; opposite direction
        clc
        adc #1
        sta v_pwspd,x
pulse_done:

; Into the shadow registers of this voice.
        ldy sid_offset,x
        lda freq_lo
        sta sid_shadow,y
        lda freq_hi
        sta sid_shadow+1,y
        lda v_pwlo,x
        sta sid_shadow+2,y
        lda v_pwhi,x
        sta sid_shadow+3,y
        lda v_ctrl,x
        and #$fe
        ora v_gate,x
        sta sid_shadow+4,y
        rts

; --- next_event (X = voice) ----------------------------
; Reads commands until a note or a rest.
next_event:
        lda v_patlo,x
        sta pat_ptr
        lda v_pathi,x
        sta pat_ptr+1
read_event:
        ldy #0
        lda (pat_ptr),y
        inc pat_ptr
        bne event_read
        inc pat_ptr+1
event_read:
        cmp #PAT_END
        beq pattern_end
        cmp #CMD_INSTR
        bcs set_instrument
        cmp #CMD_LENGTH
        bcs set_length
        cmp #NOTE_REST
        beq rest
        clc                     ; a note: transpose it
        adc v_trans,x
        jsr start_note
        jmp event_done
rest:
        lda #0
        sta v_gate,x
event_done:
        lda v_len,x
        sta v_steps,x
        lda pat_ptr
        sta v_patlo,x
        lda pat_ptr+1
        sta v_pathi,x
        rts
set_length:
        sec
        sbc #CMD_LENGTH - 1
        sta v_len,x
        jmp read_event
set_instrument:
        and #$1f
        sta v_instr,x
        jmp read_event
pattern_end:
        jsr next_pattern
        jmp next_event

; --- next_pattern (X = voice) --------------------------
; Follows the order list: transpositions, loop, then the
; next pattern's address into v_patlo/v_pathi.
next_pattern:
        lda v_ordlo,x
        sta ord_ptr
        lda v_ordhi,x
        sta ord_ptr+1
order_read:
        ldy v_order,x
        lda (ord_ptr),y
        cmp #ORDER_LOOP
        bne order_entry
        iny
        lda (ord_ptr),y         ; position to continue from
        sta v_order,x
        jmp order_read
order_entry:
        inc v_order,x
        cmp #CMD_LENGTH
        bcc order_pattern
        sec
        sbc #TRANS_ZERO
        sta v_trans,x
        jmp order_read
order_pattern:
        tay
        lda pat_lo,y
        sta v_patlo,x
        lda pat_hi,y
        sta v_pathi,x
        rts

; --- start_note (A = note, X = voice) ------------------
start_note:
        sta v_note,x
        ldy v_instr,x
        lda ins_wave,y
        sta v_wave,x
        lda ins_pwlo,y
        sta v_pwlo,x
        lda ins_pwhi,y
        sta v_pwhi,x
        lda ins_pwspd,y
        sta v_pwspd,x
        lda #0
        sta v_age,x
        sta v_vibph,x
        sta v_viblo,x
        sta v_vibhi,x
        lda ins_ad,y
        pha
        lda ins_sr,y
        ldy sid_offset,x
        sta sid_shadow+6,y
        pla
        sta sid_shadow+5,y
        lda #1
        sta v_gate,x
        rts

sid_offset: .byte 0, 7, 14
vib_down:   .byte 0, 0, 1, 1, 1, 1, 0, 0

; --- Sound state ---------------------------------------
audio_mode:   .byte 0   ; MODE_MUSIC, MODE_FX, MODE_SILENT
irq_frames:   .word 0   ; interrupts since the start
fx_next:      .byte 0   ; effect to start, 0 none
fx_pos:       .byte 0   ; next frame in fx_ctrl, 0 none
fx_prio:      .byte 0   ; priority of the effect, 0 none
fx_keep_x:    .byte 0
music_song:   .byte 0   ; song being played
music_tick:   .byte 0   ; frame inside the step
music_frames: .word 0   ; frames played since init
sid_shadow:   .fill 25  ; next values of $d400-$d418
v_order:  .fill 3       ; position in the order list
v_ordlo:  .fill 3       ; the voice's order list
v_ordhi:  .fill 3
v_patlo:  .fill 3       ; next pattern byte
v_pathi:  .fill 3
v_steps:  .fill 3       ; steps left in this event
v_len:    .fill 3       ; length of notes, in steps
v_note:   .fill 3       ; note played, transposed
v_trans:  .fill 3       ; transposition of the voice
v_instr:  .fill 3       ; instrument
v_wave:   .fill 3       ; wave table position
v_ctrl:   .fill 3       ; waveform of this frame
v_wnote:  .fill 3       ; note of this frame
v_gate:   .fill 3       ; 1 while the note sounds
v_pwlo:   .fill 3       ; pulse width
v_pwhi:   .fill 3
v_pwspd:  .fill 3       ; pulse sweep speed, signed
v_age:    .fill 3       ; frames since the note began
v_vibph:  .fill 3       ; vibrato phase
v_viblo:  .fill 3       ; vibrato offset, signed
v_vibhi:  .fill 3
VOICE_BYTES = * - v_order

"""Python model of the sound in game/src/player.asm: the three
audio modes, the songs and the sound effects.

The game asks for sounds (set_audio, sound_effect, end_sound); the
raster interrupt then plays one frame of the music or of the effect
(audio_frame). The model receives the same requests, in the same order
relative to the interrupts, and keeps the same state: the test compares
it with the C64 after every frame.
"""
from player_model import PlayerModel

MODE_MUSIC, MODE_FX, MODE_SILENT = 0, 1, 2
FX_END = 0xFF
ENDED_LOST, ENDED_WON = 1, 2


class AudioModel:
    def __init__(self, memory, labels, mode=MODE_MUSIC):
        self.m, self.L = memory, labels
        self.player = PlayerModel(memory, labels)
        self.shadow = self.player.shadow      # one set of registers
        self.song = {name: labels[f"SONG_{name}"] for name in
                     ("THEME", "WON", "LOST")}
        self.effect_number = {name: labels[f"FX_{name}"] for name in
                              ("SLASH", "HIT", "DUST", "PICKUP", "DOOR",
                               "HURT", "LOST", "WON")}
        self.irq_frames = 0
        self.started = {}               # effect number: times started
        self.refused = self.replaced = 0
        self.songs = []                 # songs started, in order
        self.set_mode(mode)

    def byte(self, label, index=0):
        return self.m[(self.L[label] + index) & 0xFFFF]

    # --- requests of the game --------------------------------------
    def set_mode(self, mode):
        """set_audio: the theme from its start, or silence."""
        self.mode = mode
        self.fx_next = self.fx_pos = self.fx_prio = 0
        if mode == MODE_MUSIC:
            self.player.init(self.song["THEME"])
            self.songs.append(self.song["THEME"])
        else:
            self.player.silence()
            if mode == MODE_SILENT:
                self.shadow[24] = 0

    def effect(self, number):
        """sound_effect: only in FX mode, only if at least as
        important as the effect playing or asked for."""
        if self.mode != MODE_FX:
            return False
        priority = self.byte("fx_priority", number - 1)
        if priority < self.fx_prio:
            self.refused += 1
            return False
        if self.fx_prio:
            self.replaced += 1          # over one playing or asked for
        self.fx_prio, self.fx_next = priority, number
        return True

    def end_sound(self, how):
        """end_sound: the piece of the end, or its effect."""
        if self.mode == MODE_MUSIC:
            song = self.song["WON" if how == ENDED_WON else "LOST"]
            self.player.init(song)
            self.songs.append(song)
        else:
            self.effect(self.effect_number["WON" if how == ENDED_WON
                                           else "LOST"])

    def request(self, item):
        """One entry of Game.step's "sounds" list."""
        kind, value = item
        if kind == "mode":
            self.set_mode(value)
        elif kind == "effect":
            self.effect(self.effect_number[value])
        elif kind == "end":
            self.end_sound(value)
        else:
            raise ValueError(item)

    # --- the interrupt ---------------------------------------------
    def irq(self):
        """audio_frame, after the registers are sent."""
        self.irq_frames = (self.irq_frames + 1) & 0xFFFF
        if self.mode == MODE_MUSIC:
            self.player.play()
        elif self.mode == MODE_FX:
            self.fx_play()

    def fx_play(self):
        number = self.fx_next
        if number:
            self.started[number] = self.started.get(number, 0) + 1
            self.fx_next = 0
            self.shadow[2] = 0
            self.fx_pos = self.byte("fx_first", number - 1)
            self.shadow[5] = self.byte("fx_ad", number - 1)
            self.shadow[6] = self.byte("fx_sr", number - 1)
            self.shadow[3] = self.byte("fx_pulse", number - 1)
        if not self.fx_pos:
            return
        control = self.byte("fx_ctrl", self.fx_pos)
        if control == FX_END:
            self.fx_pos = self.fx_prio = 0
            return
        self.shadow[4] = control
        note = self.byte("fx_note", self.fx_pos)
        self.shadow[0] = self.byte("note_lo", note)
        self.shadow[1] = self.byte("note_hi", note)
        self.fx_pos += 1

    def state(self):
        """What the test reads back from the C64."""
        return {"mode": self.mode, "fx_next": self.fx_next,
                "fx_pos": self.fx_pos, "fx_prio": self.fx_prio,
                "song": self.player.song,
                "music_frames": self.player.frames & 0xFFFF,
                "music_tick": self.player.tick,
                "shadow": list(self.shadow)}

"""Python model of the music player in game/src/player.asm.

It reads the same bytes the C64 reads (a 64 KB snapshot of the
program's memory) and applies the same rules frame by frame, so the
test can compare the 25 shadow SID registers after every interrupt.
A song is chosen at init (the theme, or one of the pieces of
the end of a game), and the order lists come from its entries in
song_order_lo/hi.
"""
VOLUME = 0x0F


class PlayerModel:
    def __init__(self, memory, labels, song=0):
        self.m = memory                   # bytes-like, 65536 long
        self.L = labels
        self.speed = labels["MUSIC_SPEED"]
        self.gate_tick = labels["MUSIC_GATE_TICK"]
        self.shadow = [0] * 25
        self.init(song)

    def byte(self, label, index=0):
        return self.m[(self.L[label] + index) & 0xFFFF]

    def silence(self):
        """sid_silence: every shadow register 0, volume 15."""
        self.shadow[:] = [0] * 25
        self.shadow[24] = VOLUME

    def init(self, song=0):
        """music_init: song from the beginning."""
        self.song = song
        self.silence()
        self.tick = 0
        self.frames = 0
        names = ("order ordlo ordhi patlo pathi steps len note trans "
                 "instr wave ctrl wnote gate pwlo pwhi pwspd age vibph "
                 "viblo vibhi")
        self.v = {name: [0, 0, 0] for name in names.split()}
        for x in range(3):
            self.v["ordlo"][x] = self.byte("song_order_lo", song * 3 + x)
            self.v["ordhi"][x] = self.byte("song_order_hi", song * 3 + x)
        for x in (2, 1, 0):
            self.v["len"][x] = 1
            self.next_pattern(x)

    def play(self):
        for x in (2, 1, 0):
            self.voice_frame(x)
        self.tick = (self.tick + 1) % self.speed
        self.frames = (self.frames + 1) & 0xFFFF

    def voice_frame(self, x):
        v = self.v
        if self.tick == 0:
            if v["steps"][x] == 0:
                self.next_event(x)
            v["steps"][x] = (v["steps"][x] - 1) & 0xFF
        elif self.tick == self.gate_tick and v["steps"][x] == 0:
            v["gate"][x] = 0
        self.update_sound(x)

    def update_sound(self, x):
        v = self.v
        y = v["wave"][x]
        while True:
            control = self.byte("wave_ctrl", y)
            if control == 0xFE:                       # hold
                break
            if control == 0xFF:                       # jump
                y = self.byte("wave_arg", y)
                continue
            v["ctrl"][x] = control
            argument = self.byte("wave_arg", y)
            if argument & 0x80:
                v["wnote"][x] = argument & 0x7F
            else:
                v["wnote"][x] = (argument + v["note"][x]) & 0xFF
            y = (y + 1) & 0xFF
            break
        v["wave"][x] = y
        note = v["wnote"][x]
        freq = self.byte("note_lo", note) | self.byte("note_hi", note) << 8
        instrument = v["instr"][x]
        depth = self.byte("ins_vibdepth", instrument)
        if depth and v["age"][x] >= self.byte("ins_vibdelay", instrument):
            phase = v["vibph"][x] & 7
            v["vibph"][x] = (v["vibph"][x] + 1) & 0xFF
            offset = v["viblo"][x] | v["vibhi"][x] << 8
            if self.byte("vib_down", phase):
                offset = (offset - depth) & 0xFFFF
            else:
                offset = (offset + depth) & 0xFFFF
            v["viblo"][x], v["vibhi"][x] = offset & 0xFF, offset >> 8
            freq = (freq + offset) & 0xFFFF
        if v["age"][x] != 0xFF:
            v["age"][x] += 1
        speed = v["pwspd"][x]
        if speed:
            width = v["pwlo"][x] | v["pwhi"][x] << 8
            width = (width + (speed - 256 if speed & 0x80 else speed)) \
                & 0xFFFF
            v["pwlo"][x], v["pwhi"][x] = width & 0xFF, width >> 8
            if v["pwhi"][x] >= 0x0E or v["pwhi"][x] < 0x02:
                v["pwspd"][x] = (-speed) & 0xFF
        base = self.byte("sid_offset", x)
        self.shadow[base] = freq & 0xFF
        self.shadow[base + 1] = freq >> 8
        self.shadow[base + 2] = v["pwlo"][x]
        self.shadow[base + 3] = v["pwhi"][x]
        self.shadow[base + 4] = (v["ctrl"][x] & 0xFE) | v["gate"][x]

    def next_event(self, x):
        v = self.v
        while True:
            pointer = v["patlo"][x] | v["pathi"][x] << 8
            value = self.m[pointer]
            pointer = (pointer + 1) & 0xFFFF
            v["patlo"][x], v["pathi"][x] = pointer & 0xFF, pointer >> 8
            if value == 0xFF:
                self.next_pattern(x)
                continue
            if value >= 0xC0:
                v["instr"][x] = value & 0x1F
                continue
            if value >= 0x80:
                v["len"][x] = (value - 0x7F) & 0xFF
                continue
            if value == 0x60:
                v["gate"][x] = 0
            else:
                self.start_note(x, (value + v["trans"][x]) & 0xFF)
            v["steps"][x] = v["len"][x]
            return

    def next_pattern(self, x):
        v = self.v
        orders = v["ordlo"][x] | v["ordhi"][x] << 8
        while True:
            y = v["order"][x]
            value = self.m[(orders + y) & 0xFFFF]
            if value == 0xFF:
                v["order"][x] = self.m[(orders + ((y + 1) & 0xFF)) & 0xFFFF]
                continue
            v["order"][x] = (y + 1) & 0xFF
            if value >= 0x80:
                v["trans"][x] = (value - 0xA0) & 0xFF
                continue
            v["patlo"][x] = self.byte("pat_lo", value)
            v["pathi"][x] = self.byte("pat_hi", value)
            return

    def start_note(self, x, note):
        v = self.v
        v["note"][x] = note
        i = v["instr"][x]
        v["wave"][x] = self.byte("ins_wave", i)
        v["pwlo"][x] = self.byte("ins_pwlo", i)
        v["pwhi"][x] = self.byte("ins_pwhi", i)
        v["pwspd"][x] = self.byte("ins_pwspd", i)
        for name in ("age", "vibph", "viblo", "vibhi"):
            v[name][x] = 0
        base = self.byte("sid_offset", x)
        self.shadow[base + 6] = self.byte("ins_sr", i)
        self.shadow[base + 5] = self.byte("ins_ad", i)
        v["gate"][x] = 1

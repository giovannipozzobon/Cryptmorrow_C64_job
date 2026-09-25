"""Cryptmorrow theme: an original piece for the three SID voices.

Everything here was written for this game: the melody, the chords,
the bass lines and the drums. The theme is in C# minor and 4/4, at
125 beats a minute (SPEED below), with a dark, bass-heavy sound over
a driving eighth-note beat. The pieces of the end and the sound
effects (sfx.py) were written for the game too. Nothing was
sampled or copied from other music.

Key: C# minor. One step is a sixteenth note; SPEED frames per step.
Notes: C, C#, D, D#, E, F, F#, G, G#, A, A#, B plus octave (C#4 = middle
octave). Tokens in a pattern: "@name" instrument, "C#4/6" note lasting
6 steps, "r/4" rest. Order lists: pattern names and "t+5" / "t-4"
transpositions (semitones, applied to the notes of that voice); "stop"
ends a song that does not loop (see SONGS).
"""

SPEED = 5            # frames per step: 50 / 5 * 60 / 4 = 150 BPM (PAL)
GATE_TICK = 4        # frame of the last step when the gate is released

# Wave tables: one entry per frame. "40 +3": pulse waveform, note three
# semitones above the played note. "81 C6": noise, fixed note C6.
# Waveforms: 10 triangle, 20 sawtooth, 40 pulse, 80 noise (gate is
# added by the player). "loop n" jumps to entry n, "end" holds.
WAVES = {
    "pulse": ["40 +0", "end"],
    "arp_minor": ["40 +0", "40 +3", "40 +7", "40 +12", "loop 0"],
    "arp_major": ["40 +0", "40 +4", "40 +7", "40 +12", "loop 0"],
    "kick": ["80 C6", "40 E3", "40 C3", "40 A2", "40 F2", "40 D2", "end"],
    "snare": ["80 A6", "40 D4", "80 F6", "80 E6", "80 D6", "end"],
    "hat": ["80 A7", "end"],
}

# ad/sr: SID envelope bytes. pw: start pulse width (0-4095).
# pwspeed: added every frame, bouncing between 512 and 3584.
# vib: (delay in frames, depth in frequency units per frame).
INSTRUMENTS = {
    "bass": dict(ad=0x09, sr=0xA6, pw=0x0400, pwspeed=6,
                 wave="pulse", vib=(0, 0)),
    "lead": dict(ad=0x29, sr=0xA9, pw=0x0600, pwspeed=18,
                 wave="pulse", vib=(12, 18)),
    "arpmin": dict(ad=0x58, sr=0xA9, pw=0x0300, pwspeed=40,
                   wave="arp_minor", vib=(0, 0)),
    "arpmaj": dict(ad=0x58, sr=0xA9, pw=0x0300, pwspeed=40,
                   wave="arp_major", vib=(0, 0)),
    "kick": dict(ad=0x08, sr=0x00, pw=0x0800, pwspeed=0,
                 wave="kick", vib=(0, 0)),
    "snare": dict(ad=0x08, sr=0x00, pw=0x0800, pwspeed=0,
                  wave="snare", vib=(0, 0)),
    "hat": dict(ad=0x02, sr=0x00, pw=0x0800, pwspeed=0,
                wave="hat", vib=(0, 0)),
}

PATTERNS = {
    # bass: root and octave in eighth notes, written on C#;
    # the order lists transpose it to each chord
    "bass_bar": "@bass C#2/2 C#2/2 C#3/2 C#2/2 C#2/2 C#3/2 C#2/2 C#3/2",
    "bass_half": "@bass C#2/2 C#3/2 C#2/2 C#3/2",
    "bass_fill": "@bass C#2/2 C#2/2 C#3/2 C#2/2 C#3/1 C#3/1 C#2/2 "
                 "G#2/2 C#3/2",

    # lead, part A: C#m | A | F#m | G# | C#m | A | F#m G# | C#m
    "lead_a": "@lead G#4/6 F#4/2 E4/4 G#4/2 E4/2 "
              "C#4/8 E4/4 A4/4 "
              "A4/6 G#4/2 F#4/4 A4/2 C#5/2 "
              "C5/8 G#4/4 D#5/4 "
              "C#5/6 B4/2 G#4/4 E4/2 G#4/2 "
              "A4/4 G#4/2 F#4/2 E4/4 C#4/4 "
              "F#4/4 A4/4 G#4/4 C5/4 "
              "C#5/12 r/4",

    # lead, part B: E | B | C#m | A | E | B | F#m | G#
    "lead_b": "@lead B4/4 G#4/2 B4/2 E5/8 "
              "D#5/6 C#5/2 B4/4 F#4/4 "
              "E5/6 D#5/2 C#5/4 G#4/4 "
              "A4/8 B4/4 C#5/4 "
              "B4/2 E5/2 G#5/4 F#5/4 E5/4 "
              "D#5/8 F#5/4 D#5/4 "
              "C#5/4 A4/4 F#4/4 A4/4 "
              "G#4/8 C5/4 D#5/4",

    # eerie arpeggios for the intro and the break
    "arp_intro": "@arpmin C#4/16 C#4/16 @arpmaj A3/16 G#3/16",
    "arp_break": "@arpmin C#4/16 @arpmaj A3/16 @arpmin F#3/16 "
                 "@arpmaj G#3/16",

    # drums: one voice, kick on 1, 3 and 4, snare on 2 and the 'and' of 4
    "hats": "@hat C4/2 C4/2 C4/2 C4/2 C4/2 C4/2 C4/2 C4/2",
    "beat": "@kick C4/2 @hat C4/2 @snare C4/2 @hat C4/2 "
            "@kick C4/2 @hat C4/2 @kick C4/2 @snare C4/2",
    "fill": "@kick C4/2 @hat C4/2 @snare C4/2 @hat C4/2 "
            "@snare C4/1 C4/1 C4/2 C4/1 C4/1 @kick C4/2",
    "half": "@kick C4/8 @snare C4/8",

    # end of a game: two bars each, then silence
    "won_bass": "@bass E2/4 E3/4 B2/4 E3/4 E2/2 G#2/2 B2/2 E3/2 E2/8",
    "won_lead": "@lead B4/2 E5/2 G#5/2 B5/2 G#5/2 B5/2 E6/4 "
                "D#6/2 E6/2 F#6/2 D#6/2 E6/8",
    "won_arp": "@arpmaj E4/12 B3/4 E4/16",
    "lost_bass": "@bass C#2/8 A1/8 G#1/8 C#2/4 r/4",
    "lost_lead": "@lead G#4/4 F#4/4 E4/4 D#4/4 C#4/12 r/4",
    "lost_arp": "@arpmin C#4/8 @arpmaj A3/8 G#3/8 @arpmin C#4/8",
    "silence": "r/64",
}

# 32 bars: intro 4, A 8, B 8, A 8, break 4; then the song loops.
BASS_A = ["t+0", "bass_bar", "t-4", "bass_bar", "t+5", "bass_bar",
          "t-5", "bass_bar", "t+0", "bass_bar", "t-4", "bass_bar",
          "t+5", "bass_half", "t-5", "bass_half", "t+0", "bass_fill"]
BASS_B = ["t+3", "bass_bar", "t-2", "bass_bar", "t+0", "bass_bar",
          "t-4", "bass_bar", "t+3", "bass_bar", "t-2", "bass_bar",
          "t+5", "bass_bar", "t-5", "bass_fill"]
ORDERS = [
    # voice 1: bass
    ["t+0", "bass_bar", "bass_bar", "t-4", "bass_bar", "t-5", "bass_bar"]
    + BASS_A + BASS_B + BASS_A
    + ["t+0", "bass_bar", "t-4", "bass_bar", "t+5", "bass_bar",
       "t-5", "bass_fill"],
    # voice 2: arpeggios and lead
    ["arp_intro", "lead_a", "lead_b", "lead_a", "arp_break"],
    # voice 3: drums
    ["hats", "hats", "beat", "fill"] + (["beat"] * 7 + ["fill"]) * 3
    + ["half", "half", "half", "fill"],
]
BARS = 32

# Songs: the theme loops for ever; the two short pieces of the
# end of a game are played once, then "stop" keeps each voice silent.
# Song numbers follow this order: SONG_THEME 0, SONG_WON 1, SONG_LOST 2.
SONGS = {
    "theme": dict(orders=ORDERS, bars=BARS),
    "won": dict(orders=[["won_bass", "stop"], ["won_lead", "stop"],
                        ["won_arp", "stop"]], bars=2),
    "lost": dict(orders=[["lost_bass", "stop"], ["lost_lead", "stop"],
                         ["lost_arp", "stop"]], bars=2),
}

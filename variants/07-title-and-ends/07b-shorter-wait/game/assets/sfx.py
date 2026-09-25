"""Cryptmorrow sound effects: original, one SID voice.

In FX mode the music is silent and voice 1 plays one effect at a time.
An effect is a list of frames (1/50 s each): a waveform and a note, as
in score.py. The builder adds a first frame with the gate off, so that
the envelope starts again even over another effect, and a last frame
that releases the note. A more important effect (higher priority)
replaces a less important one; an effect asked for while a more
important one plays is not heard.

Waveforms: 10 triangle, 20 sawtooth, 40 pulse, 80 noise. ad/sr: SID
envelope bytes. pulse: high byte of the pulse width (0-15).
"""

# Order = effect numbers 1-8 of game/src (FX_SLASH ... FX_WON).
EFFECTS = {
    # the sword cuts the air: a short hiss falling in pitch
    "slash": dict(priority=1, ad=0x00, sr=0xA2, pulse=8,
                  frames="80 A7, 80 F7, 80 D7, 80 A6, 80 F6, 80 D6"),
    # a blow that only hurts a skeleton: a metallic clink
    "hit": dict(priority=2, ad=0x00, sr=0xA4, pulse=4,
                frames="40 C6, 40 G5, 40 C5"),
    # a defeated enemy falls to dust: noise sinking for 1/5 s
    "dust": dict(priority=3, ad=0x00, sr=0xF6, pulse=8,
                 frames="80 C6, 80 A5, 80 F5, 80 D5, 80 C5, 80 A4, "
                        "80 F4, 80 D4, 80 C4, 80 A3"),
    # a key, a seal, a treasure or a potion: a rising arpeggio
    "pickup": dict(priority=3, ad=0x00, sr=0xA5, pulse=8,
                   frames="10 C5, 10 C5, 10 E5, 10 E5, 10 G5, 10 G5, "
                          "10 C6, 10 C6, 10 E6, 10 E6, 10 G6, 10 G6, "
                          "10 C7, 10 C7"),
    # a door or the portal opens: a grinding saw, then a thud
    "door": dict(priority=4, ad=0x00, sr=0xC6, pulse=8,
                 frames="20 C2, 20 C2, 20 C2, 20 C#2, 20 C#2, 20 C#2, "
                        "20 D2, 20 D2, 20 D2, 20 C#2, 20 C#2, 20 C#2, "
                        "80 C4, 80 C3"),
    # the explorer is hurt: a square wave falling fast
    "hurt": dict(priority=5, ad=0x00, sr=0xB4, pulse=6,
                 frames="40 A4, 40 A4, 40 G4, 40 G4, 40 E4, 40 E4, "
                        "40 C4, 40 C4, 40 A3, 40 A3, 40 G3, 40 G3, "
                        "40 E3, 40 E3"),
    # no energy left: a slow chromatic fall, about a second
    "lost": dict(priority=6, ad=0x08, sr=0xC8, pulse=8,
                 frames=", ".join(f"10 {note}" for note in
                                  ("G4 F#4 F4 E4 D#4 D4 C#4 C4 B3 A#3 "
                                   "A3 G#3").split() for _ in range(4))),
    # out through the portal: a fanfare in E major
    "won": dict(priority=6, ad=0x08, sr=0xC8, pulse=8,
                frames=", ".join(["40 E5"] * 4 + ["40 G#5"] * 4 +
                                 ["40 B5"] * 4 + ["40 E6"] * 16)),
}

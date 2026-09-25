"""Compile score.py and sfx.py into music.asm, the data read by
player.asm.

Byte formats (documented again in game/src/player.asm):
  pattern   $00-$5d note (C0 = 0 ... A7 = 93), $60 rest,
            $80-$bf length = value - $80 + 1 steps,
            $c0-$df instrument = value - $c0, $ff end of pattern
  order     $00-$7f pattern number, $80-$bf transpose = value - $a0,
            $ff n: continue from position n ("stop" becomes the
            silent pattern and a jump to itself)
  wave      control byte (waveform) + argument:
            $00-$7f semitones above the note, $80 + n fixed note n;
            $ff n: jump to entry n; $fe: hold the last entry
  effect    one control byte (waveform and gate) and one note per
            frame, in fx_ctrl and fx_note; $ff in fx_ctrl ends it
"""
from pathlib import Path

import score
import sfx

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A",
              "A#", "B"]
HIGHEST_NOTE = 93              # A7: higher notes overflow the register
PAL_CLOCK = 985248
REST, LENGTH, INSTRUMENT, END = 0x60, 0x80, 0xC0, 0xFF
TRANSPOSE_ZERO, ORDER_LOOP = 0xA0, 0xFF
WAVE_LOOP, WAVE_END, WAVE_FIXED = 0xFF, 0xFE, 0x80
FX_END = 0xFF


def note_number(name):
    """'C#4' -> 49. Octaves 0-7, C0 = 0."""
    pitch, octave = name[:-1], int(name[-1])
    if pitch not in NOTE_NAMES:
        raise ValueError(f"unknown note {name}")
    number = octave * 12 + NOTE_NAMES.index(pitch)
    if not 0 <= number <= HIGHEST_NOTE:
        raise ValueError(f"note {name} out of range")
    return number


def sid_frequency(number):
    """16-bit SID frequency value of a note on a PAL C64."""
    hertz = 440.0 * 2 ** ((number - 57) / 12)
    value = round(hertz * 16777216 / PAL_CLOCK)
    assert value <= 0xFFFF
    return value


def compile_waves():
    data, starts = [], {}
    for name, entries in score.WAVES.items():
        starts[name] = len(data)
        for entry in entries:
            if entry == "end":
                data.append((WAVE_END, 0))
            elif entry.startswith("loop"):
                data.append((WAVE_LOOP, starts[name] + int(entry.split()[1])))
            else:
                control, argument = entry.split()
                if argument[0] in "+-":
                    offset = int(argument)
                    if not 0 <= offset < 0x80:
                        raise ValueError(f"{name}: offset {offset}")
                    data.append((int(control, 16), offset))
                else:
                    data.append((int(control, 16),
                                 WAVE_FIXED + note_number(argument)))
    if len(data) > 255:
        raise ValueError("wave tables longer than 255 entries")
    return data, starts


def compile_pattern(name, text, instruments):
    data, length, steps = [], None, 0
    for token in text.split():
        if token.startswith("@"):
            data.append(INSTRUMENT + instruments.index(token[1:]))
            continue
        pitch, count = token.split("/")
        count = int(count)
        if not 1 <= count <= 64:
            raise ValueError(f"{name}: length {count}")
        if count != length:
            data.append(LENGTH + count - 1)
            length = count
        data.append(REST if pitch == "r" else note_number(pitch))
        steps += count
    return data + [END], steps


def compile_orders(song, patterns, steps):
    """Order lists of one song: [voice 1, voice 2, voice 3], and its
    length in steps. A looping song goes back to its first entry; a
    song ending in "stop" goes on with the silent pattern for ever."""
    names = list(patterns)
    orders, lengths = [], []
    for items in score.SONGS[song]["orders"]:
        data, total = [], 0
        for item in items:
            if item == "stop":
                data += [names.index("silence"), ORDER_LOOP, len(data)]
                break
            if item.startswith("t"):
                data.append(TRANSPOSE_ZERO + int(item[1:]))
            else:
                data.append(names.index(item))
                total += steps[item]
        else:
            data += [ORDER_LOOP, 0]
        orders.append(data)
        lengths.append(total)
    if len(set(lengths)) != 1:
        raise ValueError(f"{song}: voices of different length: {lengths}")
    if lengths[0] != score.SONGS[song]["bars"] * 16:
        raise ValueError(f"{song}: {lengths[0]} steps, not "
                         f"{score.SONGS[song]['bars']} bars")
    return orders, lengths[0]


def compile_effects():
    """Frames of every effect in one table, entry 0 unused (fx_pos 0
    means no effect): a first frame with the gate off, the frames
    with the gate on, a frame that releases the note, FX_END."""
    control, notes, first = [0], [0], []
    for name, effect in sfx.EFFECTS.items():
        frames = [item.split() for item in effect["frames"].split(",")]
        waves = [(int(wave, 16), note_number(note)) for wave, note in frames]
        first.append(len(control))
        control.append(waves[0][0])
        notes.append(waves[0][1])
        for wave, note in waves:
            control.append(wave | 1)
            notes.append(note)
        control += [waves[-1][0], FX_END]
        notes += [waves[-1][1], 0]
    if len(control) > 256:
        raise ValueError("effects longer than 256 frames in all")
    return control, notes, first


def byte_lines(label, values):
    lines = [f"{label}:"] if label else []
    for start in range(0, len(values), 8):
        chunk = ", ".join(f"${v:02x}" for v in values[start:start + 8])
        lines.append(f"        .byte {chunk}")
    return lines


def build(out_dir):
    waves, starts = compile_waves()
    names = list(score.INSTRUMENTS)
    patterns, steps = {}, {}
    for name, text in score.PATTERNS.items():
        patterns[name], steps[name] = compile_pattern(name, text, names)
    songs = {song: compile_orders(song, patterns, steps)
             for song in score.SONGS}
    control, notes, first = compile_effects()
    ins = score.INSTRUMENTS
    lines = ["; Generated by game/assets/music.py from score.py and",
             "; sfx.py. Do not edit: change those and rebuild.",
             f"MUSIC_SPEED = {score.SPEED}",
             f"MUSIC_GATE_TICK = {score.GATE_TICK}"]
    lines += [f"SONG_{song.upper()} = {n}"
              for n, song in enumerate(score.SONGS)]
    lines += [f"FX_{name.upper()} = {n + 1}"
              for n, name in enumerate(sfx.EFFECTS)]
    lines += [f"FX_END = ${FX_END:02x}", ""]
    freqs = [sid_frequency(n) for n in range(HIGHEST_NOTE + 1)]
    lines += byte_lines("note_lo", [f & 255 for f in freqs])
    lines += byte_lines("note_hi", [f >> 8 for f in freqs])
    table = [("ins_ad", [ins[n]["ad"] for n in names]),
             ("ins_sr", [ins[n]["sr"] for n in names]),
             ("ins_pwlo", [ins[n]["pw"] & 255 for n in names]),
             ("ins_pwhi", [ins[n]["pw"] >> 8 for n in names]),
             ("ins_pwspd", [ins[n]["pwspeed"] & 255 for n in names]),
             ("ins_wave", [starts[ins[n]["wave"]] for n in names]),
             ("ins_vibdelay", [ins[n]["vib"][0] for n in names]),
             ("ins_vibdepth", [ins[n]["vib"][1] for n in names])]
    for label, values in table:
        lines += byte_lines(label, values)
    lines += byte_lines("wave_ctrl", [c for c, _ in waves])
    lines += byte_lines("wave_arg", [a for _, a in waves])
    lines.append("pat_lo:")
    lines += [f"        .byte <pat_{n}" for n in patterns]
    lines.append("pat_hi:")
    lines += [f"        .byte >pat_{n}" for n in patterns]
    lines.append("song_order_lo:           ; three voices a song")
    lines += [f"        .byte <order_{song}_{v + 1}"
              for song in songs for v in range(3)]
    lines.append("song_order_hi:")
    lines += [f"        .byte >order_{song}_{v + 1}"
              for song in songs for v in range(3)]
    for song, (orders, _) in songs.items():
        for voice, data in enumerate(orders):
            lines += byte_lines(f"order_{song}_{voice + 1}", data)
    for name, data in patterns.items():
        lines += byte_lines(f"pat_{name}", data)
    effects = list(sfx.EFFECTS.values())
    lines.append("; effects 1-8: first frame, envelope, pulse width,")
    lines.append("; priority; then the frames of all of them")
    for label, values in (
            ("fx_first", first),
            ("fx_ad", [e["ad"] for e in effects]),
            ("fx_sr", [e["sr"] for e in effects]),
            ("fx_pulse", [e["pulse"] for e in effects]),
            ("fx_priority", [e["priority"] for e in effects]),
            ("fx_ctrl", control), ("fx_note", notes)):
        lines += byte_lines(label, values)
    text = "\n".join(lines) + "\n"
    (Path(out_dir) / "music.asm").write_text(text, encoding="utf-8",
                                            newline="\n")
    theme_steps = songs["theme"][1]
    frames = theme_steps * score.SPEED
    return {"song_steps": theme_steps, "loop_frames": frames,
            "loop_seconds": round(frames * 19656 / PAL_CLOCK, 2),
            "bpm": round(PAL_CLOCK / 19656 * 60 / (score.SPEED * 4), 1),
            "songs": {song: {"steps": length,
                             "frames": length * score.SPEED,
                             "loops": song == "theme"}
                      for song, (_, length) in songs.items()},
            "effects": {name: {"number": n + 1,
                               "priority": e["priority"],
                               "frames": control.index(FX_END, first[n])
                               - first[n]}
                        for n, (name, e) in enumerate(sfx.EFFECTS.items())},
            "effect_bytes": len(control) * 2 + 5 * len(first),
            "instruments": names, "patterns": list(patterns),
            "wave_entries": len(waves),
            "data_bytes": sum(len(p) for p in patterns.values())
            + sum(len(o) for orders, _ in songs.values() for o in orders)
            + 2 * len(waves) + 8 * len(names) + 2 * len(freqs)
            + 2 * len(patterns) + 6 * len(songs)}

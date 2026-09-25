"""What reaches the SID when the first blow of the sword asks for an
effect in SOUND FX mode (chapter 11: step 06 and variant 06x).

Usage: python tools/sid_writes.py
           [--vice PATH] [--root DIR ...]

VICE runs with its 'dump' sound device, which writes every SID register
write to a text file: cycles since the last write, register, value.
The machine boots without autostart; through the text monitor the PRG
of DIR is loaded as LOAD leaves it and started from `entry`. At the
first `set_audio` (called by start_audio) the register A is set to 1,
MODE_FX, as START_MODE = MODE_FX would do (variant 06a). The program
then runs from `joy_ready` to `joy_ready`, frame after frame; in frame
FIRE the joystick byte `joy_state` gets Fire (16), as the tests inject
input, and from that frame fx_pos and fx_prio are read at `joy_ready`.
The writes are grouped in bursts of 25 (audio_frame sends the shadow
registers every interrupt, from $d418 down to $d400; sid_silence writes
25 zeros); the value written into register 4, the control of voice 1,
is listed burst by burst. Prints JSON. Standard library only.
"""
import argparse
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tools"))
sys.path.insert(0, str(PROJECT / "tests"))
from measure_routine import TextMonitor  # noqa: E402
from vicemon import DEFAULT_VICE, free_port, load_labels  # noqa: E402

FIRE, AFTER = 30, 120
ROOTS = ["chain/06-sound", "variants/06-sound/06x-stuck-note"]


def runs(values):
    """[a, a, b] -> ['a x2', 'b x1']"""
    out = []
    for value in values:
        if out and out[-1][0] == value:
            out[-1][1] += 1
        else:
            out.append([value, 1])
    return [f"{v} x{n}" for v, n in out]


def record(vice_path, root, scratch):
    folder = PROJECT / root
    prg = folder / "game/build/cryptmorrow.prg"
    labels = load_labels(folder / "game/build/cryptmorrow.lbl")
    dump = Path(scratch) / (folder.name + ".dump")
    port = free_port()
    log = open(Path(scratch) / (folder.name + ".log"), "w")
    vice = subprocess.Popen(
        [str(vice_path), "-default", "-pal", "-sound", "-sounddev",
         "dump", "-soundarg", str(dump), "-warp", "+VICIIvcache",
         "-remotemonitor", "-remotemonitoraddress",
         f"127.0.0.1:{port}"], stdout=log, stderr=subprocess.STDOUT)
    seen = []
    try:
        deadline = time.monotonic() + 30
        while True:
            try:
                socket.create_connection(("127.0.0.1", port), 1).close()
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise RuntimeError("VICE's monitor did not answer")
                time.sleep(0.2)
        time.sleep(3)                           # BASIC is ready
        text = TextMonitor(port)
        text.send(f'l "{prg.as_posix()}" 0')    # as LOAD leaves it
        text.send(f"r pc = {labels['entry']:04x}")
        text.send(f"break {labels['set_audio']:04x}")
        text.send("g", wait=60)
        text.send("r a = 01")                   # MODE_FX
        text.send("del")
        text.send(f"break {labels['joy_ready']:04x}")
        for frame in range(FIRE + AFTER):
            text.send("g", wait=30)
            if frame == FIRE:
                text.send(f"> {labels['joy_state']:04x} 10")
            if frame >= FIRE:
                row = []
                for name in ("fx_pos", "fx_prio"):
                    address = labels[name]
                    shown = text.send(f"m {address:04x} {address:04x}")
                    row.append(int(re.search(
                        rf">C:{address:04x}\s+([0-9a-f]{{2}})",
                        shown).group(1), 16))
                seen.append(f"fx_pos {row[0]}, fx_prio {row[1]}")
        text.send("del")
        text.link.sendall(b"quit\n")            # VICE closes the dump
        time.sleep(2)
        text.close()
    finally:
        try:
            vice.wait(timeout=15)
        except subprocess.TimeoutExpired:
            vice.terminate()
            vice.wait(timeout=10)
        log.close()
    writes = [tuple(int(v) for v in line.split())
              for line in dump.read_text().splitlines() if line.strip()]
    bursts, current = [], []
    for _, register, value in writes:
        if register == 24 and current:
            bursts.append(current)
            current = []
        current.append((register, value))
    bursts.append(current)
    whole = [b for b in bursts if [r for r, _ in b] == list(range(24, -1,
                                                                   -1))]
    control = [f"${dict(b)[4]:02x}" for b in whole]
    return {"root": root, "writes": len(writes),
            "bursts_of_25": len(whole),
            "voice_1_control": runs(control),
            "at_joy_ready_from_fire": runs(seen)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vice", default=str(DEFAULT_VICE))
    parser.add_argument("--root", action="append", default=None)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as scratch:
        result = [record(args.vice, root, scratch)
                  for root in (args.root or ROOTS)]
    print(json.dumps({"fire_frame": FIRE, "frames_after": AFTER,
                      "runs": result}, indent=1))


if __name__ == "__main__":
    main()

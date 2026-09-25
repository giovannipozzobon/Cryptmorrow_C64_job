"""Measure how many cycles a stretch of the program takes, in VICE.

Usage: python tools/measure_routine.py --root DIR --start LABEL
           --end LABEL [--vice PATH] [--poke NAME[+N]=VALUE ...]
           [--peek NAME[+N] ...] [--skip N]

The PRG of DIR (game/build/cryptmorrow.prg) is started by VICE, loaded
again by the monitor (as LOAD leaves it) and restarted from `entry`, as
tools/shoot.py does. The program runs to the first execution of the
start label; there the stopwatch of VICE's text monitor is reset;
the program runs on to the first execution of the end label, and the
stopwatch is read, all through one link to the text monitor (closing
a link lets the machine run on). The reading counts only if the
monitor shows the machine standing at the end label.

With --poke NAME[+N]=VALUE (repeatable), the monitor writes VALUE into
the byte at label NAME plus N when the start label is reached, before
the stopwatch starts: a state the program would reach later (an enemy
in the room), set up by hand and declared with the measure. With
--peek NAME[+N] (repeatable) the byte is read at the end label. With
--skip N the start label is passed N times before the stopwatch starts
(the N+1th interrupt, say). A label may also be an address written
$hex, such as a KERNAL entry.

Prints the cycles and the PAL frames they make (19 656 cycles a frame)
and the raster line and cycle at the end label as JSON. The count
includes everything the machine does in between (with interrupts off,
only the program).
"""
import argparse
import json
from pathlib import Path
import re
import socket
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from vicemon import (DEFAULT_VICE, PAL_FRAME_CYCLES, PROJECT,  # noqa
                     Vice, load_labels)


class TextMonitor:
    """One link to VICE's text monitor, kept open for the whole
    measurement: closing a link lets the machine run on."""

    def __init__(self, port):
        self.link = socket.create_connection(("127.0.0.1", port),
                                             timeout=5)
        self.link.settimeout(0.5)

    def send(self, command, wait=10):
        self.link.sendall((command + "\n").encode())
        answer, deadline = bytearray(), time.monotonic() + wait
        while time.monotonic() < deadline:
            try:
                chunk = self.link.recv(4096)
            except (TimeoutError, OSError):
                chunk = b""
            answer.extend(chunk)
            if re.search(rb"\(C:\$[0-9a-f]{4}\) $", bytes(answer)):
                break
        return answer.decode(errors="replace")

    def close(self):
        self.link.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--vice", default=str(DEFAULT_VICE))
    parser.add_argument("--settle", type=float, default=3.0)
    parser.add_argument("--poke", action="append", default=[],
                        metavar="NAME[+N]=VALUE")
    parser.add_argument("--peek", action="append", default=[],
                        metavar="NAME[+N]")
    parser.add_argument("--skip", type=int, default=0,
                        help="pass the start label N times first")
    args = parser.parse_args()
    root = args.root if args.root.is_absolute() else PROJECT / args.root
    prg = root / "game/build/cryptmorrow.prg"
    labels = load_labels(root / "game/build/cryptmorrow.lbl")

    def where(name):
        """A label, or an address written $hex (a KERNAL entry)."""
        return int(name[1:], 16) if name.startswith("$") else labels[name]
    image = prg.read_bytes()
    load, body = image[0] | image[1] << 8, image[2:]
    log = Path("/tmp") / "measure-vice.log" if sys.platform != "win32" \
        else root / "measure-vice.log"
    vice = Vice(args.vice, prg, log)
    try:
        vice.connect(args.settle)       # binary link: not used further
        text = TextMonitor(vice.text_port)
        text.send(f'l "{prg.as_posix()}" 0')    # as LOAD leaves it
        text.send(f"r pc = {labels['entry']:04x}")
        placed = text.send(f"break {where(args.start):04x}")
        if args.skip:
            number = re.search(r"BREAK:\s*(\d+)", placed).group(1)
            # the monitor reads numbers as hexadecimal
            text.send(f"ignore {number} {args.skip:x}")
        text.send("g", wait=60)
        for poke in args.poke:
            place, value = poke.split("=")
            name, _, offset = place.partition("+")
            address = labels[name] + int(offset or 0)
            byte = int(value.replace("$", "0x"), 0) & 0xFF
            text.send(f"> {address:04x} {byte:02x}")
        reset = text.send("stopwatch reset")
        text.send("del")
        text.send(f"break {where(args.end):04x}")
        stop = text.send("g", wait=60)
        answer = text.send("stopwatch")
        registers = text.send("r")
        peeks = {}
        for place in args.peek:
            name, _, offset = place.partition("+")
            address = labels[name] + int(offset or 0)
            shown = text.send(f"m {address:04x} {address:04x}")
            found = re.search(rf">C:{address:04x}\s+([0-9a-f]{{2}})",
                              shown)
            peeks[place] = int(found.group(1), 16) if found else None
        text.close()
    finally:
        vice.close()
    stopped = re.findall(r"\(C:\$([0-9a-f]{4})\)", answer)
    if not stopped or int(stopped[-1], 16) != where(args.end):
        raise SystemExit(f"not at the end label: {answer!r}")
    numbers = [int(n) for n in re.findall(r"Stopwatch:\s*(\d+)", answer)]
    result = {"root": str(args.root), "start": args.start,
              "end": args.end, "skip": args.skip, "pokes": args.poke,
              "peeks": peeks,
              "reset_answer": reset.strip()[-200:],
              "answer": answer.strip()[-300:],
              "registers": registers.strip()[-300:],
              "cycles": numbers[-1] if numbers else None}
    # the raster position at the end label: "r" lists LIN and CYC
    lines = [l for l in registers.splitlines() if l.strip()]
    head = next((i for i, l in enumerate(lines) if "LIN" in l), None)
    if head is not None and head + 1 < len(lines):
        names, values = lines[head].split(), lines[head + 1].split()
        if len(names) == len(values):
            table = dict(zip(names, values))
            if "LIN" in table and "CYC" in table:
                result["raster_line"] = int(table["LIN"])
                result["raster_cycle"] = int(table["CYC"])
    if result["cycles"] is not None:
        result["frames"] = round(result["cycles"] / PAL_FRAME_CYCLES, 2)
    print(json.dumps(result, indent=1))
    return 0 if result["cycles"] is not None else 1


if __name__ == "__main__":
    sys.exit(main())

"""How long a PRG takes to load from a 1541 disk (chapter 13: the PRG
of step 07, with holes, against the packed PRG of step 08).

Usage: python tools/load_time.py
           [--vice PATH] [--root DIR ...]

For each DIR (default chain/07-title-and-ends and chain/08-complete),
c1541 (beside x64sc) writes game/build/cryptmorrow.prg into a new D64
image in a scratch folder, and reports the blocks it takes. VICE then
starts with a 1541 on unit 8, true drive emulation on, the image
attached and no autostart; through the text monitor the keyboard buffer
receives LOAD"NAME",8,1 and RETURN, as a user would type it. The
monitor holds the machine from its start (-initbreak ready), so every
run types at the same emulated moment and the disk turns the same way
(the clock at the LOAD call is reported); the machine stops where
BASIC's LOAD calls the KERNAL (JSR $FFD5 at $E175)
and where that call returns ($E178); the load time is the difference
of the two CPU clocks the monitor prints there, in cycles of the PAL
C64 (985 248 a second). At the end, $AE/$AF must hold the end address
of the loaded file. Warp mode only makes the run faster: the clocks
count emulated cycles. Prints JSON. Standard library only.
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
from vicemon import DEFAULT_VICE, free_port  # noqa: E402

PAL_CLOCK = 985248
CALL, BACK = 0xE175, 0xE178          # JSR $FFD5 in BASIC's LOAD, after it
ROOTS = ["chain/07-title-and-ends", "chain/08-complete"]


def clock(answer, address):
    """The CPU clock printed with the stop at address."""
    line = next(l for l in answer.splitlines()
                if l.startswith(f".C:{address:04x}"))
    return int(line.split()[-1])


def load(vice, image, name, port, scratch):
    log = open(Path(scratch) / f"{name}.log", "w")
    process = subprocess.Popen(
        [str(vice), "-default", "-pal", "-sound", "-sounddev", "dummy",
         "-warp", "-drive8type", "1541", "-drive8truedrive", "-8",
         str(image), "-initbreak", "ready", "-remotemonitor",
         "-remotemonitoraddress", f"127.0.0.1:{port}"], stdout=log,
        stderr=subprocess.STDOUT)
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
        text = TextMonitor(port)
        ready = text.send("r")                   # held at the start
        at = re.search(r"\.;([0-9a-f]{4})", ready)
        text.send(f'keybuf load\\"{name}\\",8,1\\n')
        text.send(f"break {CALL:04x}")
        start = clock(text.send("g", wait=120), CALL)
        text.send("del")
        text.send(f"break {BACK:04x}")
        end = clock(text.send("g", wait=300), BACK)
        shown = text.send("m ae af")
        low, high = re.search(r">C:00ae\s+([0-9a-f]{2})\s+([0-9a-f]{2})",
                              shown).groups()
        text.send("del")
        text.link.sendall(b"quit\n")
        time.sleep(1)
        text.close()
    finally:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=10)
        log.close()
    return end - start, int(high + low, 16), start, \
        at.group(1) if at else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vice", default=str(DEFAULT_VICE))
    parser.add_argument("--root", action="append", default=None)
    args = parser.parse_args()
    c1541 = Path(args.vice).with_name(
        "c1541.exe" if args.vice.endswith(".exe") else "c1541")
    results = []
    with tempfile.TemporaryDirectory() as scratch:
        for number, root in enumerate(args.root or ROOTS):
            prg = PROJECT / root / "game/build/cryptmorrow.prg"
            data = prg.read_bytes()
            name = f"step{number}"
            image = Path(scratch) / f"{name}.d64"
            listing = subprocess.run(
                [str(c1541), "-format", "cryptmorrow,cm", "d64",
                 str(image), "-write", str(prg), name, "-dir"],
                capture_output=True, text=True, check=True).stdout
            blocks = int(re.search(rf'^(\d+)\s+"{name}"', listing,
                                   re.M).group(1))
            cycles, end, start, ready = load(args.vice, image, name,
                                             free_port(), scratch)
            expected = data[0] | data[1] << 8
            expected += len(data) - 2
            if end != expected:
                raise SystemExit(f"{root}: load ended at ${end:04x}, "
                                 f"not ${expected:04x}")
            results.append({
                "root": root, "bytes": len(data), "blocks": blocks,
                "load_cycles": cycles,
                "load_seconds": round(cycles / PAL_CLOCK, 2),
                "bytes_per_second": round(len(data) / (cycles / PAL_CLOCK)),
                "end_address": f"${end:04x}",
                "clock_at_load_call": start, "pc_when_held": ready})
    print(json.dumps({"method": "LOAD\"NAME\",8,1 typed through the "
                      "monitor's keyboard buffer; 1541, true drive "
                      "emulation; clocks at $E175 and $E178",
                      "loads": results}, indent=1))


if __name__ == "__main__":
    main()

"""Which instructions of a program the route of its test executes.

Usage: python tools/exec_coverage.py [--root chain/08-complete]
           [--script tests/verify_game.py] [--vice PATH]
           [--out evidence/execution.json]

Every instruction of the program and its address come from the 64tass
listing of ROOT (game/build/cryptmorrow.lst). VICE loads the PRG; the
tool writes it into memory again as LOAD leaves it, puts a checkpoint
on every instruction and deletes each one at its first hit (the
monitor's own temporary checkpoints replace one another: not usable
here), starts the program from `entry` - the SYS of the BASIC line - and plays
the whole route of SCRIPT as the test does: a new game starts again
from `start` (after unpack) if the program has one, from `entry` if
not. Every stop at
one of those checkpoints is an instruction executed for the first time.
The result: how many instructions ran, and the address and source line
of every one that never did.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from vicemon import DEFAULT_VICE, PROJECT, Vice, load_labels  # noqa: E402

ALIGN = 32


def instructions(listing):
    """(address, source text) of every instruction in a 64tass listing:
    the lines that start with '.address' and carry a mnemonic."""
    found = []
    for line in listing.read_text(encoding="utf-8",
                                  errors="replace").splitlines():
        if not line.startswith("."):
            continue
        parts = line.split("\t")
        fields = [p for p in parts[1:-1] if p.strip()]
        if len(fields) >= 2 and all(len(b) == 2 for b in
                                    fields[0].split()):
            found.append((int(parts[0][1:], 16), parts[-1].strip()))
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path,
                        default=PROJECT / "chain/08-complete")
    parser.add_argument("--script", type=Path,
                        default=PROJECT / "tests/verify_game.py")
    parser.add_argument("--vice", type=Path, default=DEFAULT_VICE)
    parser.add_argument("--settle", type=float, default=4.0)
    parser.add_argument("--out", type=Path, default=PROJECT /
                        "evidence/execution.json")
    args = parser.parse_args()
    root = args.root.resolve()
    prg = root / "game/build/cryptmorrow.prg"
    labels = load_labels(root / "game/build/cryptmorrow.lbl")
    code = instructions(root / "game/build/cryptmorrow.lst")
    spec = importlib.util.spec_from_file_location("route", args.script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    image = prg.read_bytes()
    load, body = image[0] | image[1] << 8, image[2:]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    vice = Vice(args.vice, prg, args.out.parent / "coverage-vice.log",
                args.out.parent.resolve().relative_to(PROJECT).as_posix())
    executed = set()
    wanted = {address for address, _ in code}
    numbers = {}
    try:
        monitor = vice.connect(args.settle)

        def run():
            pc = monitor.run_until_stop()
            if pc in numbers:
                executed.add(pc)
                monitor.delete_checkpoint(numbers.pop(pc))
            return pc

        def word(address):
            return struct.unpack("<H", monitor.memory(address, 2))[0]
        joy_at = labels.get("joy_ready")
        zp = labels.get("joy_state", 2)
        monitor.checkpoint(labels["main_loop"])
        if joy_at:
            monitor.checkpoint(joy_at)
        for address in sorted(wanted):
            numbers[address] = monitor.checkpoint(address)

        def start(mode=None, first=False):
            point = None
            if mode is not None and "start_audio" in labels:
                point = monitor.checkpoint(labels["start_audio"])
            monitor.poke(load, body)        # as LOAD leaves it
            monitor.set_pc(labels["start"] if not first and "start" in
                           labels else labels["entry"])
            if point is not None:
                while run() != labels["start_audio"]:
                    pass
                monitor.poke(labels["audio_mode"], bytes([mode]))
                monitor.delete_checkpoint(point)
            while run() != labels["main_loop"]:
                pass

        def frame(joy):
            if joy_at:
                while run() != joy_at:
                    pass
                monitor.poke(zp, bytes([joy]))
            while run() != labels["main_loop"]:
                pass

        start(first=True)
        frames = 0
        for joy, count, expectation, _ in module.SCRIPT:
            if joy == "restart":
                start(None if count < 0 else count)
            elif joy in ("energy", "seals"):
                monitor.poke(labels[joy], bytes([count]))
                monitor.poke(labels["hud_dirty"], b"\x01")
            elif joy == "enemy":
                x, y = expectation
                for name, value in (("en_x_lo", x & 255),
                                    ("en_x_hi", x >> 8), ("en_y", y)):
                    monitor.poke(labels[name] + count, bytes([value]))
            elif joy == "slow":
                monitor.poke(labels["en_fast"] + count, b"\x00")
            else:
                if joy == "align":
                    joy, count = 0, (count - word(labels["frame_count"])
                                     ) % ALIGN
                for _ in range(count):
                    frame(joy)
                    frames += 1
    finally:
        vice.close()
    never = [{"address": f"${a:04x}", "source": s} for a, s in code
             if a not in executed]
    result = {"root": root.relative_to(PROJECT).as_posix(),
              "script": args.script.resolve().relative_to(
                  PROJECT).as_posix(),
              "prg_sha256": hashlib.sha256(image).hexdigest(),
              "vice": str(args.vice), "frames": frames,
              "instructions": len(code), "executed": len(executed),
              "executed_addresses": sorted(executed), "never": never}
    args.out.write_text(json.dumps(result, indent=1) + "\n",
                        encoding="utf-8", newline="\n")
    print(f"{len(executed)} of {len(code)} instructions executed in "
          f"{frames} frames; {len(never)} never")
    return 0


if __name__ == "__main__":
    sys.exit(main())

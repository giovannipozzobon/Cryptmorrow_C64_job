"""Take a native screenshot of a program at a point of a route.

Usage: python tools/shoot.py --root DIR --script FILE --upto K
                             [--extra N | --until EXPR] [--peek NAME ...]
                             --out chain/evidence/x.png [--vice PATH]

The PRG of DIR (game/build/cryptmorrow.prg) is loaded by VICE, written
into memory again as LOAD leaves it and started from `entry`; then the
first K entries of the route's SCRIPT are played with the joystick
(steps from 02 on: at joy_ready of every frame; step 01: frames), with
the test's own moves ('align', 'restart', 'energy', 'seals', 'enemy',
'slow'), and VICE exports the screen. --extra N plays N more frames of
entry K (its joystick); --until EXPR goes on from entry K frame by
frame, through as many entries as needed (at most --limit frames),
until EXPR, a Python expression over the peeked values (`m['name']`),
is true. --then N plays N frames more with the same stick: VICE
exports the last picture the VIC finished, and a change made after the
beam has passed shows only in the next frame. --peek reads memory at
the moment of the picture: a label or $address, with :count for more
than one byte ("hero_x:2", "$d000:17").

Nothing is compared with a model: this is how the book photographs a
program that is wrong on purpose ("Where it breaks"), and any scene of
a route. tools/make_figures.py checks each figure's facts on the peeked
values. Prints what it did as JSON.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from vicemon import DEFAULT_VICE, PROJECT, Vice, load_labels  # noqa: E402

ALIGN = 32


def parse_peek(text, labels):
    """'name', 'name:2', '$d015', '$d000:17' -> (key, address, count)."""
    name, _, count = text.partition(":")
    count = int(count) if count else 1
    if name.startswith("$"):
        return text, int(name[1:], 16), count
    if name not in labels:
        raise SystemExit(f"--peek: no label {name!r}")
    return text, labels[name], count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--upto", type=int, required=True,
                        help="entries of SCRIPT to play")
    parser.add_argument("--extra", type=int, default=0,
                        help="frames of the next entry to play as well")
    parser.add_argument("--until", default=None,
                        help="play on until this is true")
    parser.add_argument("--limit", type=int, default=3000,
                        help="frames --until may play")
    parser.add_argument("--then", type=int, default=0,
                        help="frames to play after the point, with the "
                             "same stick (VICE shows the frame before)")
    parser.add_argument("--peek", action="append", default=[])
    parser.add_argument("--out", required=True,
                        help="PNG path inside the project")
    parser.add_argument("--vice", type=Path, default=DEFAULT_VICE)
    parser.add_argument("--settle", type=float, default=4.0)
    args = parser.parse_args()
    root = args.root.resolve()
    prg = root / "game/build/cryptmorrow.prg"
    labels = load_labels(root / "game/build/cryptmorrow.lbl")
    peeks = [parse_peek(text, labels) for text in args.peek]
    spec = importlib.util.spec_from_file_location("route", args.script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    script = module.SCRIPT
    if args.extra and not isinstance(script[args.upto][0], int):
        raise SystemExit(f"entry {args.upto} is {script[args.upto][0]!r}"
                         ": --extra needs a joystick entry")
    if args.extra > (script[args.upto][1] if args.extra else 0):
        raise SystemExit(f"--extra {args.extra}: entry {args.upto} has "
                         f"only {script[args.upto][1]} frames")
    out = PROJECT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    image = prg.read_bytes()
    load, body = image[0] | image[1] << 8, image[2:]
    vice = Vice(args.vice, prg, out.parent / "shoot-vice.log",
                out.parent.relative_to(PROJECT).as_posix())
    try:
        monitor = vice.connect(args.settle)

        def word(address):
            return struct.unpack("<H", monitor.memory(address, 2))[0]

        def read_peeks():
            values = {}
            for key, address, count in peeks:
                data = list(monitor.memory(address, count))
                values[key] = data[0] if count == 1 else data
            return values
        joy_at = labels.get("joy_ready")
        zp = labels.get("joy_state", 2)
        monitor.checkpoint(labels["main_loop"])
        if joy_at:
            monitor.checkpoint(joy_at)

        def start(mode=None):
            point = None
            if mode is not None and "start_audio" in labels:
                point = monitor.checkpoint(labels["start_audio"])
            monitor.poke(load, body)        # as LOAD leaves it
            monitor.set_pc(labels["entry"])
            if point is not None:
                while monitor.run_until_stop() != labels["start_audio"]:
                    pass
                monitor.poke(labels["audio_mode"], bytes([mode]))
                monitor.delete_checkpoint(point)
            while monitor.run_until_stop() != labels["main_loop"]:
                pass

        def frame(joy):
            if joy_at:
                while monitor.run_until_stop() != joy_at:
                    pass
                monitor.poke(zp, bytes([joy]))
            while monitor.run_until_stop() != labels["main_loop"]:
                pass

        start()
        frames = extra = entries = partial = 0

        def reached():
            if args.until:
                return bool(eval(args.until, {"m": read_peeks()}))
            return extra == args.extra

        done = args.upto == 0 and reached()
        for index, (joy, count, expectation, _) in enumerate(script):
            if done:
                break
            inside = index >= args.upto     # frames counted as extra
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
                for here in range(count):
                    if inside and reached():
                        done, partial = True, here
                        break
                    frame(joy)
                    frames += 1
                    extra += inside
                    if args.until and extra > args.limit:
                        raise SystemExit(f"--until: not true after "
                                         f"{args.limit} frames")
            if not done:
                entries = index + 1
                done = entries >= args.upto and reached()
        if not done:
            raise SystemExit("the route ended first")
        stick = script[entries][0] if partial and isinstance(
            script[entries][0], int) else 0
        for _ in range(args.then):
            frame(stick)
            frames += 1
        values = read_peeks()
        counter = word(labels["frame_count"]) if "frame_count" in labels \
            else None
        capture = vice.screenshot(out.name)
        capture.update(root=root.relative_to(PROJECT).as_posix(),
                       script=args.script.as_posix(), entries=entries,
                       extra=partial, then=args.then, frames=frames,
                       frame_count=counter, peek=values)
        print(json.dumps(capture, indent=2))
    finally:
        vice.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

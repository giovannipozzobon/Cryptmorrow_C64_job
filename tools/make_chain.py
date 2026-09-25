"""Generate the chain of the book from the master source.

Usage: python tools/make_chain.py [--assemble] [--out DIR] [STEP ...]

The master is game/src: the complete game, whose comments also carry
tags that say in which steps of the chain each line exists:

  {3}       the line exists from step 3 on (the same as {3-})
  {3-6}     only in steps 3 to 6;  {-6}: up to step 6
  ;|text    a line of earlier steps only, not of the complete game:
            in the steps of its tag (which must end before the last
            step) it becomes `text`
  ;{3-6}    alone on a line: the lines up to the next ";{}" take this
            range too (blocks nest; a line keeps the narrower range)

A tag is the last thing on its line, inside the comment. Since tags
live in comments, game/src assembles as it is into the complete game,
and the last step is game/src without its tags.

For each step the script writes chain/NN-name/game/src (only the files
the step includes), a copy of game/assets, the tools to build and run
it, and README.md from chain/readme/NN.md; with --assemble it runs
64tass and checks the line length. With every step it also writes
chain/coverage.csv, the draft register of the labels of the complete
game with the step where each first appears. Standard library only.
"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STEPS = {1: "01-first-room", 2: "02-explorer", 3: "03-dungeon",
         4: "04-objects-doors", 5: "05-combat", 6: "06-sound",
         7: "07-title-and-ends", 8: "08-complete"}
LAST = max(STEPS)
TAG = re.compile(r"\s*\{(\d*)(-?)(\d*)\}$")
BLOCK = re.compile(r"^;\{(\d*)(-?)(\d*)\}$")
LINE_LIMIT = 60


def parse(first, dash, last):
    low = int(first) if first else 1
    high = int(last) if last else (LAST if dash or not first else low)
    if first and not dash:
        high = LAST                     # {3}: from 3 on
    return low, high


def step_lines(text, step, name):
    """The lines of one file in one step, tags removed."""
    out, blocks = [], [(1, LAST)]
    for number, line in enumerate(text.splitlines(), 1):
        where = f"{name}:{number}"
        if line == ";{}":
            if len(blocks) == 1:
                raise SystemExit(f"{where}: ;{{}} without a block")
            blocks.pop()
            continue
        block = BLOCK.match(line)
        if block:
            low, high = parse(*block.groups())
            outer = blocks[-1]
            blocks.append((max(low, outer[0]), min(high, outer[1])))
            continue
        low, high = blocks[-1]
        earlier = line.startswith(";|")
        if earlier:
            line = line[2:]
        tag = TAG.search(line)
        if tag:
            first, second = parse(*tag.groups())
            low, high = max(low, first), min(high, second)
            line = line[:tag.start()].rstrip()
            if line.endswith(";") and not line.strip() == ";":
                line = line[:-1].rstrip()
        elif earlier:
            raise SystemExit(f"{where}: ;| line without a tag")
        if earlier and high >= LAST:
            raise SystemExit(f"{where}: ;| line in the last step")
        if "{" in line and "}" in line and ";" in line:
            raise SystemExit(f"{where}: tag not at the end")
        if low <= step <= high:
            out.append(line)
    if len(blocks) != 1:
        raise SystemExit(f"{name}: block not closed")
    squeezed = []
    for line in out:                    # no double blank lines
        if line == "" and (not squeezed or squeezed[-1] == ""):
            continue
        squeezed.append(line)
    while squeezed and squeezed[-1] == "":
        squeezed.pop()
    return squeezed


def included(lines):
    return [m.group(1) for line in lines
            for m in [re.match(r'\s+\.include "([a-z_]+\.asm)"', line)]
            if m]


def generate(step, out_root):
    source = ROOT / "game/src"
    target = out_root / STEPS[step]
    if target.exists():
        shutil.rmtree(target)
    src = target / "game/src"
    src.mkdir(parents=True)
    todo, done = ["main.asm"], []
    while todo:
        name = todo.pop(0)
        if name in done:
            continue
        lines = step_lines((source / name).read_text(encoding="utf-8"),
                           step, name)
        (src / name).write_text("\n".join(lines) + "\n", encoding="utf-8",
                                newline="\n")
        done.append(name)
        todo += included(lines)
    shutil.copytree(ROOT / "game/assets", target / "game/assets",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (target / "tools").mkdir()
    for name in ("check_lines.py", "run-game.ps1"):
        shutil.copy2(ROOT / "tools" / name, target / "tools" / name)
    readme = ROOT / "chain/readme" / f"{step:02d}.md"
    if readme.exists():
        shutil.copy2(readme, target / "README.md")
    return target, done


def assemble(target, assembler="64tass"):
    build = target / "game/build"
    build.mkdir(exist_ok=True)
    result = subprocess.run(
        [str(assembler), "--cbm-prg", "-Wall", "-Werror", "--vice-labels-numeric",
         "-l", "game/build/cryptmorrow.lbl", "-L", "game/build/cryptmorrow.lst",
         "-o", "game/build/cryptmorrow.prg", "game/src/main.asm"],
        cwd=target, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f"{target.name}: 64tass failed\n{result.stdout}"
                         f"{result.stderr}")
    long = [f"{f.name}:{n}" for f in sorted((target / "game/src").glob("*.asm"))
            for n, line in enumerate(f.read_text().splitlines(), 1)
            if len(line) > LINE_LIMIT]
    if long:
        raise SystemExit(f"{target.name}: lines over {LINE_LIMIT}: {long}")
    data = (build / "cryptmorrow.prg").read_bytes()
    return len(data)


DEFINITION = re.compile(r"^([A-Za-z_]\w*)(?::|\s+=\s|\s+\.(?:logical|byte"
                        r"|word|fill|text|binary)\b|\s*$)")


def coverage(out_root):
    """chain/coverage.csv: every label and constant of the complete
    game, its file and the step where it first appears; checks that no
    label of a step is missing from the next one (the seams aside)."""
    first, previous, rows = {}, set(), []
    for step in sorted(STEPS):
        names = {}
        for path in sorted((out_root / STEPS[step] / "game/src").glob(
                "*.asm")):
            for number, line in enumerate(path.read_text().splitlines(), 1):
                match = DEFINITION.match(line)
                if match:
                    names.setdefault(match.group(1), (path.name, number))
        lost = previous - set(names) - {"START_MODE"}
        if lost:
            raise SystemExit(f"step {step} drops {sorted(lost)}")
        for name, (file, number) in names.items():
            first.setdefault(name, (step, file))
        previous = set(names)
        if step == LAST:
            rows = [(name, file, number) for name, (file, number)
                    in names.items()]
    lines = ["label,file,line,step,chapter"]
    for name, file, number in sorted(rows, key=lambda r: (r[1], r[2])):
        lines.append(f"{name},{file},{number},{first[name][0]:02d},")
    (out_root / "coverage.csv").write_text("\n".join(lines) + "\n",
                                           encoding="utf-8")
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("steps", nargs="*", type=int)
    parser.add_argument("--assemble", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "chain")
    args = parser.parse_args()
    for step in args.steps or sorted(STEPS):
        target, files = generate(step, args.out)
        size = assemble(target) if args.assemble else None
        print(f"{target.name}: {len(files)} files"
              + (f", PRG {size} bytes" if size else ""))
    if not args.steps:
        print(f"coverage.csv: {coverage(args.out)} labels")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Mutation test of the chain of the book: one-line defects in the new
code of each step, each of which its step's test must stop.

Usage: python tools/mutate_steps.py [--vice PATH] [STEP ...]

For every mutation the step's folder is copied to out/mutants/, the
line is changed (it must be there exactly once), the copy assembled
with 64tass (as tools/make_chain.py --assemble) and
tests/verify_step.py run on it: the test must fail. Steps 07 and 08
are the program of 1.0.1, whose own mutation test (49 defects, all
stopped) was run on the complete game before the chain was made.
Writes chain/evidence/mutations.json.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tools"))
import make_chain                               # noqa: E402

# (step, file, line as in the step, the defect, what it breaks)
MUTATIONS = [
    (1, "main.asm", "        and #3",
     "        and #1", "two flame frames of four"),
    (1, "world.asm", "        ldx #4                  ; four tables",
     "        ldx #3                  ; four tables",
     "set_zone copies three colour tables of four"),
    (1, "room.asm", "        inc torch_count",
     "        nop", "the torch list stays empty"),
    (2, "hero.asm", "        beq vertical            ; no horizontal input",
     "        bne vertical            ; no horizontal input",
     "horizontal input read the wrong way"),
    (2, "hero.asm", "WALK_RATE    = 8        ; frames between walk frames",
     "WALK_RATE    = 6        ; frames between walk frames",
     "walking frames every 6 frames"),
    (2, "hero.asm", "        lda #DIR_UP",
     "        lda #DIR_DOWN", "up walks up but faces down"),
    (3, "world.asm", "ENTRY_MARGIN = 8        ; pixels inside the new room",
     "ENTRY_MARGIN = 9        ; pixels inside the new room",
     "the explorer enters a pixel further in"),
    (3, "hud.asm", "        lda #LIGHT_RED << 4",
     "        lda #$20", "full cells of the bar in red"),
    (3, "world.asm", "        lda #NORTH_EDGE + ENTRY_MARGIN",
     "        lda #NORTH_EDGE + ENTRY_MARGIN + 1",
     "entry from the north one pixel off"),
    (4, "objects.asm", "        eor key_set             ; the key is used up",
     "        ora key_set             ; the key is used up",
     "a key opens its door and is kept"),
    (4, "objects.asm", "POTION_ENERGY  = 2      ; cells of the bar per potion",
     "POTION_ENERGY  = 4      ; cells of the bar per potion",
     "a potion gives four cells"),
    (4, "objects.asm", "points_middle:  .byte $10, $02",
     "points_middle:  .byte $10, $03", "a treasure is worth 350"),
    (5, "combat.asm", "        lda #0                  ; not below zero",
     "        nop                     ; not below zero",
     "energy not stopped at zero: 255 after the touch"),
    (5, "combat.asm", "SAFE_FRAMES   = 30      ; frames safe after a hit",
     "SAFE_FRAMES   = 50      ; frames safe after a hit",
     "50 frames of protection"),
    (5, "combat.asm", "enemy_hp:       .byte 0, 3, 1   ; kind 0: an empty slot",
     "enemy_hp:       .byte 0, 2, 1   ; kind 0: an empty slot",
     "skeletons fall at the second blow"),
    (6, "player.asm", "        bcc effect_refused      ; less important",
     "        bcs effect_refused      ; less important",
     "priorities of the effects the wrong way"),
    (6, "player.asm", "        sta sid_shadow+24       ; volume 0",
     "        nop                     ; volume 0",
     "SILENT keeps the volume up"),
    (6, "player.asm", "        inc fx_pos",
     "        nop", "an effect never moves on"),
]


def run(step, file, line, defect, vice, number):
    source = sorted((PROJECT / "chain").glob(f"{step:02d}-*"))[0]
    target = PROJECT / "out/mutants" / f"{source.name}-m{number:02d}"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(
        "build", "__pycache__"))
    path = target / "game/src" / file
    lines = path.read_text(encoding="utf-8").split("\n")
    count = lines.count(line)
    if count != 1:
        raise SystemExit(f"step {step} {file}: {line.strip()!r} found "
                         f"{count} times")
    lines[lines.index(line)] = defect
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    make_chain.assemble(target)
    evidence = f"out/mutants/evidence-m{number:02d}"
    begin = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(PROJECT / "tests/verify_step.py"), "--step",
         str(step), "--root", str(target), "--evidence", evidence,
         "--vice", str(vice)], cwd=PROJECT, capture_output=True,
        text=True, timeout=3600)
    seconds = round(time.monotonic() - begin)
    message = next((l for l in result.stderr.splitlines()
                    if "FAILED" in l), result.stderr.strip()[-200:])
    return result.returncode, message, seconds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("steps", nargs="*", type=int)
    parser.add_argument("--vice", type=Path, required=True)
    args = parser.parse_args()
    results, caught = [], 0
    for number, (step, file, line, defect, what) in enumerate(MUTATIONS, 1):
        if args.steps and step not in args.steps:
            continue
        code, message, seconds = run(step, file, line, defect, args.vice,
                                     number)
        stopped = code == 1 and "FAILED" in message
        caught += stopped
        results.append({"step": step, "file": file, "line": line.strip(),
                        "defect": defect.strip(), "breaks": what,
                        "stopped": stopped, "seconds": seconds,
                        "message": message})
        print(f"m{number:02d} step {step:02d} {what}: "
              f"{'STOPPED' if stopped else 'NOT STOPPED'} ({seconds} s) "
              f"{message}", flush=True)
    report = PROJECT / "chain/evidence/mutations.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    old = json.loads(report.read_text()) if report.exists() and \
        args.steps else {"mutations": []}
    kept = [m for m in old["mutations"] if m["step"] not in args.steps]
    everything = sorted(kept + results, key=lambda m: m["step"])
    report.write_text(json.dumps({
        "mutations": everything,
        "stopped": sum(m["stopped"] for m in everything),
        "total": len(everything),
        "note": "steps 07 and 08: the 49 mutations of 1.0.1, run on "
                "the complete game before the chain was made"},
        indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{caught} of {len(results)} stopped")
    return 0 if caught == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

"""Build, prove and describe the guided variants and the "Where it
breaks" versions of the chain (tools/variants.py).

Usage: python tools/make_variants.py [--plan] [--test] [--vice PATH]
           [--assembler PATH] [--readme] [ID ...]

For each one (all, or the IDs given):
1. variants/NN-name/ID/ = chain/NN-name/ with the edits; the asset
   builder runs again if an asset changed; the lines are checked and
   the program assembled (64tass).
2. --plan: a variant with its own route is planned with the same change
   in the model: tools/plan_route.py --step N --root ... --set ...
   tools/ROUTE > tests/routes/variant_ID.py.
3. --test: a variant runs the step's test with the changed model
   (tests/verify_step.py, or tests/verify_game.py for step 07) and must
   PASS with the facts of `expect`; a break runs the step's own test,
   which must FAIL with the pattern `fails`, then tools/shoot.py
   photographs it. Reports and pictures in variants/NN-name/ID/evidence/.
4. README.md in the folder: where, before and after, what you see,
   limits, what depends on it, how it was verified, how to restore.
Writes variants/variants.json with every result and the index
variants/README.md. --readme only writes the READMEs again.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tools"))
import make_chain                               # noqa: E402
from variants import BREAKS, VARIANTS           # noqa: E402

LANGUAGE = {".asm": "asm", ".py": "python", ".txt": "text"}


def step_folder(step):
    return sorted((PROJECT / "chain").glob(f"{step:02d}-*"))[0]


def folder(spec):
    return PROJECT / "variants" / step_folder(spec["step"]).name / spec["id"]


def rel(path):
    return Path(path).resolve().relative_to(PROJECT).as_posix()


def build(spec, assembler="64tass"):
    source, target = step_folder(spec["step"]), folder(spec)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(
        "build", "__pycache__", "evidence"))
    assets = False
    for file, old, new in spec["edits"]:
        path = target / file
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"{spec['id']}: {file}: the old text is there "
                             f"{text.count(old)} times")
        path.write_text(text.replace(old, new), encoding="utf-8",
                        newline="\n")
        assets |= file.startswith("game/assets/")
    if assets:
        subprocess.run([sys.executable, "game/assets/build_assets.py"],
                       cwd=target, check=True, capture_output=True)
    check = subprocess.run([sys.executable, "tools/check_lines.py"],
                           cwd=target, capture_output=True, text=True)
    if check.returncode:
        raise SystemExit(f"{spec['id']}: lines too long\n{check.stdout}")
    size = make_chain.assemble(target, assembler)
    return {"prg_bytes": size}


def model_options(spec):
    options = []
    for statement in spec.get("model", []):
        options += ["--set", statement]
    return options


def route_file(spec):
    return PROJECT / "tests/routes" / f"variant_{spec['id'][:3]}.py"


def plan(spec):
    if not spec.get("route"):
        return None
    command = [sys.executable, str(PROJECT / "tools/plan_route.py"),
               "--step", str(spec["step"]), "--root", str(folder(spec))]
    command += model_options(spec)
    command.append(str(PROJECT / "tools" / spec["route"]))
    result = subprocess.run(command, cwd=PROJECT, capture_output=True,
                            text=True)
    if result.returncode:
        raise SystemExit(f"{spec['id']}: planning failed\n"
                         f"{result.stderr[-2000:]}")
    route_file(spec).write_text(result.stdout, encoding="utf-8",
                                newline="\n")
    return rel(route_file(spec))


def test_command(spec, vice, variant):
    step, target = spec["step"], folder(spec)
    evidence = rel(target) + "/evidence"
    if step >= 7:
        command = [sys.executable, str(PROJECT / "tests/verify_game.py"),
                   "--step", str(step)]
    else:
        command = [sys.executable, str(PROJECT / "tests/verify_step.py"),
                   "--step", str(step)]
    command += ["--root", str(target), "--evidence", evidence,
                "--vice", str(vice)]
    if variant:
        command += model_options(spec)
        if spec.get("route"):
            command += ["--script", str(route_file(spec))]
        if spec.get("shows") is False:
            command.append("--no-shows")
    return command, PROJECT / evidence


def display(spec):
    """The test's command line as the README shows it."""
    command, _ = test_command(spec, "VICE", spec["kind"] == "variant")
    at = command.index("--vice")
    words = []
    for word in command[1:at] + command[at + 2:]:   # no python, --vice
        if Path(word).is_absolute():
            word = rel(word)
        words.append(f'"{word}"' if " " in word else word)
    return "python " + " ".join(words)


def test(spec, vice):
    variant = spec["kind"] == "variant"
    command, evidence = test_command(spec, vice, variant)
    result = subprocess.run(command, cwd=PROJECT, capture_output=True,
                            text=True, timeout=3600)
    message = next((l for l in result.stderr.splitlines()
                    if "FAILED" in l), "")
    report_name = "game-test.json" if spec["step"] >= 7 else \
        "step-test.json"
    report = json.loads((evidence / report_name).read_text())
    outcome = {"command": display(spec),
        "result": report["result"], "message": message,
        "frames": report.get("checked_frames")}
    if variant:
        facts = []
        for text, expression in spec["expect"]:
            ok = bool(eval(expression, {"r": report}))
            facts.append({"fact": text, "ok": ok})
        outcome["facts"] = facts
        outcome["proved"] = report["result"] == "PASS" and all(
            f["ok"] for f in facts)
    else:
        outcome["proved"] = result.returncode == 1 and bool(
            re.search(spec["fails"], message))
        if spec.get("shot"):
            outcome["picture"] = shoot(spec, vice)
    return outcome


def shoot(spec, vice):
    script_path, upto = spec["shot"]
    spec_module = importlib.util.spec_from_file_location(
        "route", PROJECT / script_path)
    sys.path.insert(0, str(PROJECT / "tests"))
    module = importlib.util.module_from_spec(spec_module)
    spec_module.loader.exec_module(module)
    count = eval(upto, {"s": module.SCRIPT})
    out = rel(folder(spec)) + f"/evidence/{spec['id']}.png"
    result = subprocess.run(
        [sys.executable, str(PROJECT / "tools/shoot.py"), "--root",
         str(folder(spec)), "--script", str(PROJECT / script_path),
         "--upto", str(count), "--out", out, "--vice", str(vice)],
        cwd=PROJECT, capture_output=True, text=True, timeout=1800)
    if result.returncode:
        raise SystemExit(f"{spec['id']}: shoot failed\n{result.stderr}")
    return {"file": Path(out).name, "entries": count,
            "frames": json.loads(result.stdout)["frames"]}


def block(file, text):
    language = LANGUAGE.get(Path(file).suffix, "text")
    return f"```{language}\n{text}\n```"


def readme(spec, outcome):
    step = step_folder(spec["step"])
    number = f"{spec['step']:02d}"
    lines = []
    if spec["kind"] == "variant":
        lines += [f"# Cryptmorrow, step {number} - variant "
                  f"{spec['id'][:3]}: {spec['title']}", "",
                  spec["summary"], "",
                  f"This folder is step {number} (`chain/{step.name}` in "
                  f"the project) with one change.", "", "## Where", "",
                  spec["where"], ""]
    else:
        lines += [f"# Cryptmorrow, step {number} - where it breaks: "
                  f"{spec['title']}", "", spec["summary"], "",
                  f"This folder is step {number} (`chain/{step.name}` in "
                  f"the project) with a mistake made on purpose.", ""]
    for n, (file, old, new) in enumerate(spec["edits"]):
        lines += [f"{'## Before' if not n else '### Before'} (`{file}`)", "",
                  block(file, old), "",
                  f"{'## After' if not n else '### After'}", "",
                  block(file, new), ""]
    if spec["kind"] == "variant":
        lines += ["## What you will see", "", spec["see"], "",
                  "## Allowed values and limits", "", spec["limits"], "",
                  "## What else depends on it", "", spec["depends"], ""]
    else:
        lines += ["## Symptom", "", spec["symptom"], "", "## Cause", "",
                  spec["cause"], ""]
    lines += ["## Try it", "",
              "`tools/run-game.ps1 -Mode Play` (Windows PowerShell) builds "
              "this folder and starts it in VICE.", ""]
    if outcome:
        if spec["kind"] == "variant":
            model = ", ".join(f"`{m}`" for m in spec.get("model", [])) or \
                "no change to the model"
            facts = "; ".join(f["fact"] for f in outcome["facts"])
            lines += ["## How it was verified", "",
                      f"Assembled with 64tass and run in VICE by the "
                      f"project's test (`{display(spec)}`): every "
                      f"frame compared with the model of the game changed "
                      f"in the same way ({model}). Result: "
                      f"{outcome['result']}, {outcome['frames']} frames; "
                      f"shown: {facts}. Report in `evidence/`.", ""]
        else:
            lines += ["## How the test catches it", "",
                      f"`{display(spec)}` stops: \"{outcome['message']}"
                      "\".", ""]
            if outcome.get("picture"):
                lines += [f"Picture: `evidence/{outcome['picture']['file']}`"
                          f", after {outcome['picture']['frames']} frames "
                          "of the step's route.", ""]
    lines += ["## Restore" if spec["kind"] == "variant" else "## Repair",
              "", "Put back the lines of *Before*, or start again from "
              f"`chain/{step.name}`.", ""]
    (folder(spec) / "README.md").write_text("\n".join(lines),
                                            encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--readme", action="store_true",
                        help="only write the READMEs again, from "
                             "variants.json")
    parser.add_argument("--vice", type=Path, default=None)
    parser.add_argument("--assembler", default="64tass",
                        help="the 64tass program, if not on the PATH")
    args = parser.parse_args()
    summary_path = PROJECT / "variants/variants.json"
    summary = json.loads(summary_path.read_text()) if \
        summary_path.exists() else {}
    for spec in VARIANTS + BREAKS:
        if args.ids and spec["id"] not in args.ids:
            continue
        entry = summary.get(spec["id"], {})
        if args.readme:
            readme(spec, entry.get("outcome"))
            continue
        entry.update(step=spec["step"], kind=spec["kind"],
                     title=spec["title"], folder=rel(folder(spec)),
                     **build(spec, args.assembler))
        print(f"{spec['id']}: built, PRG {entry['prg_bytes']} bytes",
              flush=True)
        if args.plan and spec.get("route"):
            entry["route"] = plan(spec)
            print(f"{spec['id']}: planned {entry['route']}", flush=True)
        outcome = entry.get("outcome")
        if args.test:
            outcome = test(spec, args.vice)
            entry["outcome"] = outcome
            print(f"{spec['id']}: {'PROVED' if outcome['proved'] else 'NOT PROVED'}"
                  f" ({outcome['result']}) {outcome['message']}", flush=True)
        readme(spec, outcome)
        summary[spec["id"]] = entry
        summary_path.parent.mkdir(exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2) + "\n",
                                encoding="utf-8", newline="\n")
    index(summary)
    proved = [e for e in summary.values() if e.get("outcome", {}).get(
        "proved")]
    print(f"{len(proved)} of {len(summary)} proved")
    return 0 if not args.test or len(proved) == len(summary) else 1


def index(summary):
    """variants/README.md: every variant and break, by step."""
    lines = ["# Cryptmorrow - guided variants and \"where it breaks\"", "",
             "Each folder is a step of the chain (`chain/NN-name` in the "
             "project) with one change: a guided variant to try, or a "
             "mistake made on purpose. Its README says where, before and "
             "after, what you will see, the limits, how it was verified "
             "and how to restore. `tools/run-game.ps1 -Mode Play` in a "
             "folder builds it and starts it in VICE.", "",
             "| Step | Folder | Kind | What it shows | Verified |",
             "|---|---|---|---|---|"]
    for spec in VARIANTS + BREAKS:
        entry = summary.get(spec["id"], {})
        outcome = entry.get("outcome")
        verified = "not yet" if not outcome else (
            "yes" if outcome["proved"] else "NO")
        kind = "variant" if spec["kind"] == "variant" else \
            "where it breaks"
        folder_name = f"{step_folder(spec['step']).name}/{spec['id']}"
        lines.append(f"| {spec['step']:02d} | `{folder_name}` | {kind} | "
                     f"{spec['summary']} | {verified} |")
    (PROJECT / "variants/README.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.exit(main())

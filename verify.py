"""Check the package of Cryptmorrow byte for byte.

Usage: python verify.py [--assembler PATH] [--keep] [NAME ...]

1. Every file listed in SHA256SUMS.txt is present and unchanged. A file
   you have edited for an experiment is named here: that is expected.
2. Every program of the package is built again in a temporary folder,
   the way tools/run-game.ps1 builds it: game/assets/build_assets.py
   writes the data, tools/check_lines.py checks that no line is longer
   than 60 characters, and 64tass assembles game/src/main.asm with the
   options of the book (chapter 1). The data written again must be the
   data in the package, and the program must be the reference program,
   byte for byte:
       game                       releases/cryptmorrow-1.0.1.prg
       chain/NN-name              reference/chain/NN-name.prg
       variants/NN-name/ID        reference/variants/ID.prg
   A variant's test report (evidence/*.json) must name the same program
   (its prg_sha256): the program tested is the program shipped.
3. The disk image releases/cryptmorrow-1.0.1.d64 holds the same program.
   It is read here with Python: the directory on track 18, then the
   chain of sectors of the file.

NAME limits the builds to the folders whose path contains it, for
example `chain/03` or `05b`. Nothing in the package is changed; the
temporary folder is deleted at the end unless --keep is given.

Needs Python 3.10 or later, standard library only, and 64tass on the
PATH or given with --assembler. The reference programs were made with
64tass 1.60.3243; 1.59.3120 gives the same bytes, another version may
not. Exit status 0 when everything matches, 1 when something does not.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
OPTIONS = ["--cbm-prg", "-Wall", "-Werror", "--vice-labels-numeric",
           "-l", "game/build/cryptmorrow.lbl",
           "-L", "game/build/cryptmorrow.lst",
           "-o", "game/build/cryptmorrow.prg", "game/src/main.asm"]
RELEASE = ROOT / "releases/cryptmorrow-1.0.1.prg"
DISK = ROOT / "releases/cryptmorrow-1.0.1.d64"
DISK_FILE = "CRYPTMORROW"
# Sectors of each track of a 35-track 1541 disk image.
SECTORS = [21] * 17 + [19] * 7 + [18] * 6 + [17] * 5
SKIP = shutil.ignore_patterns("build", "evidence", "__pycache__",
                              "*.pyc", "*.log")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def check_sums():
    """Files of SHA256SUMS.txt that are missing or changed."""
    problems, count = [], 0
    for line in (ROOT / "SHA256SUMS.txt").read_text(
            encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        name = name.lstrip("*")
        count += 1
        path = ROOT / name
        if not path.is_file():
            problems.append(f"missing: {name}")
        elif sha256(path.read_bytes()) != digest:
            problems.append(f"changed: {name}")
    return count, problems


def programs():
    """(folder, reference PRG) of every program in the package."""
    found = [(ROOT / "game", RELEASE)]
    for step in sorted((ROOT / "chain").glob("[0-9][0-9]-*")):
        found.append((step, ROOT / "reference/chain" / f"{step.name}.prg"))
    for variant in sorted((ROOT / "variants").glob("[0-9][0-9]-*/*")):
        if variant.is_dir():
            found.append((variant, ROOT / "reference/variants" /
                          f"{variant.name}.prg"))
    return found


def run(command, folder):
    result = subprocess.run(command, cwd=folder, capture_output=True,
                            text=True)
    return result.returncode, (result.stdout + result.stderr).strip()


def build(folder, work, assembler):
    """Build one folder in `work`; returns (PRG bytes, problems)."""
    shipped = folder / "game/assets/generated"
    if folder == ROOT / "game":
        # The master source: check_lines.py reads its step tags with
        # make_chain.py.
        shipped = folder / "assets/generated"
        shutil.copytree(folder, work / "game", ignore=SKIP)
        (work / "tools").mkdir()
        for name in ("check_lines.py", "make_chain.py"):
            shutil.copy2(ROOT / "tools" / name, work / "tools" / name)
    else:
        shutil.copytree(folder, work, ignore=SKIP, dirs_exist_ok=True)
    (work / "game/build").mkdir(parents=True, exist_ok=True)
    problems = []
    for command, what in (
            ([sys.executable, "game/assets/build_assets.py"], "data"),
            ([sys.executable, "tools/check_lines.py"], "line length"),
            ([assembler] + OPTIONS, "64tass")):
        status, output = run(command, work)
        if status:
            last = output.splitlines()[-3:] if output else []
            problems.append(f"{what} failed: " + " / ".join(last))
            return None, problems
        if what == "data":
            problems += same_data(shipped, work / "game/assets/generated")
    return (work / "game/build/cryptmorrow.prg").read_bytes(), problems


def same_data(expected, found):
    """The files in generated/ written again must be those shipped."""
    problems = []
    names = {p.name for p in expected.iterdir()} | \
            {p.name for p in found.iterdir()}
    for name in sorted(names):
        a, b = expected / name, found / name
        if not a.exists():
            problems.append(f"generated/{name} is new")
        elif not b.exists():
            problems.append(f"generated/{name} was not written")
        elif a.read_bytes() != b.read_bytes():
            problems.append(f"generated/{name} differs")
    return problems


def tested(folder, made):
    """Reports of the folder's tests that name another program."""
    problems = []
    for report in sorted((folder / "evidence").glob("*.json")):
        digest = json.loads(report.read_text(encoding="utf-8")).get(
            "prg_sha256")
        if digest and digest != sha256(made):
            problems.append(f"evidence/{report.name} tested another "
                            f"program ({digest[:16]})")
    return problems


def compare(made, reference):
    """None if the two programs are the same, or where they differ."""
    if made == reference:
        return None
    for offset, (x, y) in enumerate(zip(made, reference)):
        if x != y:
            address = reference[0] | reference[1] << 8
            return (f"byte {offset} differs (address "
                    f"${address + offset - 2:04X}: ${x:02X}, reference "
                    f"${y:02X})")
    return f"{len(made)} bytes, reference {len(reference)}"


def sector(image, track, number):
    start = (sum(SECTORS[:track - 1]) + number) * 256
    return image[start:start + 256]


def disk_file(image, wanted):
    """The bytes of the program `wanted` on a D64 image."""
    if len(image) != sum(SECTORS) * 256:
        raise ValueError(f"{len(image)} bytes: not a 35-track D64 image")
    track, number, seen, start = 18, 1, set(), None
    while track and start is None:
        if (track, number) in seen:
            raise ValueError("the directory loops")
        seen.add((track, number))
        block = sector(image, track, number)
        for entry in range(8):
            e = block[entry * 32:entry * 32 + 32]
            name = e[5:21].rstrip(b"\xa0").decode("latin-1")
            if e[2] == 0x82 and name.upper() == wanted:
                start = e[3], e[4]
        track, number = block[0], block[1]
    if start is None:
        raise ValueError(f"no program {wanted} in the directory")
    data, (track, number), seen = bytearray(), start, set()
    while True:
        if (track, number) in seen:
            raise ValueError("the file's sectors loop")
        seen.add((track, number))
        block = sector(image, track, number)
        if block[0] == 0:
            return bytes(data + block[2:block[1] + 1])
        data += block[2:]
        track, number = block[0], block[1]


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("names", nargs="*")
    parser.add_argument("--assembler", default=None,
                        help="64tass, if it is not on the PATH")
    parser.add_argument("--keep", action="store_true",
                        help="keep the temporary folder")
    args = parser.parse_args()
    assembler = args.assembler or shutil.which("64tass")
    if not assembler:
        sys.exit("64tass is not on the PATH: add its folder to the PATH "
                 "or give it with --assembler.")
    status, version = run([assembler, "--version"], ROOT)
    print(f"Python {sys.version.split()[0]}; "
          f"{version.splitlines()[0] if version else assembler}")
    failures = 0

    count, problems = check_sums()
    print(f"\nSHA256SUMS.txt: {count} files, "
          f"{'all unchanged' if not problems else f'{len(problems)} not'}")
    for line in problems:
        print("  " + line)
    failures += len(problems)

    selected = [(f, r) for f, r in programs()
                if not args.names or any(
                    n in f.relative_to(ROOT).as_posix() for n in args.names)]
    print(f"\nPrograms built again and compared: {len(selected)}")
    scratch = Path(tempfile.mkdtemp(prefix="cryptmorrow-verify-"))
    names = [f.relative_to(ROOT).as_posix() for f, _ in selected]
    same, reports, width = 0, 0, max([len(n) for n in names] + [4])
    try:
        for number, (folder, reference) in enumerate(selected):
            name = folder.relative_to(ROOT).as_posix()
            work = scratch / f"{number:02d}"
            made, problems = build(folder, work, assembler)
            if made is not None:
                if not reference.is_file():
                    problems.append(f"no reference program "
                                    f"{reference.relative_to(ROOT)}")
                else:
                    difference = compare(made, reference.read_bytes())
                    if difference:
                        problems.append(difference)
                problems += tested(folder, made)
                reports += len(list((folder / "evidence").glob("*.json")))
            if made is not None and not problems:
                same += 1
                print(f"  {name:{width}} {len(made):6} bytes  "
                      f"{sha256(made)[:16]}  same")
            else:
                print(f"  {name:{width}} DIFFERENT")
                for line in problems:
                    print("      " + line)
                failures += 1
    finally:
        if args.keep:
            print(f"\nThe builds are in {scratch}")
        else:
            shutil.rmtree(scratch, ignore_errors=True)
    print(f"  {same} of {len(selected)} identical to their reference; "
          f"test reports checked: {reports}")

    step8 = ROOT / "reference/chain/08-complete.prg"
    release = RELEASE.read_bytes()
    if step8.read_bytes() != release:
        print("\nreference/chain/08-complete.prg is not the release")
        failures += 1
    try:
        on_disk = disk_file(DISK.read_bytes(), DISK_FILE)
        disk_ok = on_disk == release
        print(f"\n{DISK.relative_to(ROOT).as_posix()}: {DISK_FILE}, "
              f"{len(on_disk)} bytes, "
              f"{'the release byte for byte' if disk_ok else 'DIFFERENT'}")
    except (OSError, ValueError) as error:
        print(f"\n{DISK.relative_to(ROOT).as_posix()}: {error}")
        disk_ok = False
    failures += not disk_ok

    print("\nResult:", "PASS" if not failures else f"FAIL ({failures})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

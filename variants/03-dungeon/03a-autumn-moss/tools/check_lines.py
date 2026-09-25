"""Fail the build if an Assembly line is longer than the book allows.

Listings in the manual are extracted from these sources, so every line
must fit the page: at most 60 characters (tabs count as 8). In the
master source of the chain the lines of every step are checked, without
their tags.
Usage: python tools/check_lines.py [--limit 60] [files...]
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args()
    files = args.files or sorted((ROOT / "game/src").glob("*.asm"))
    long_lines = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        versions = [("", text.splitlines())]
        if "{" in text and (";|" in text or "}" in text):
            # The master source of the chain (tools/make_chain.py):
            # check every step it generates, without the tags.
            sys.path.insert(0, str(ROOT / "tools"))
            import make_chain
            versions = [(f" (step {step})",
                         make_chain.step_lines(text, step, path.name))
                        for step in sorted(make_chain.STEPS)]
        for step, lines in versions:
            for number, line in enumerate(lines, 1):
                width = len(line.expandtabs(8))
                if width > args.limit:
                    long_lines.append(f"{path.name}{step}:{number}: "
                                      f"{width} chars")
    if long_lines:
        print("Lines longer than the book allows "
              f"({args.limit} characters):", file=sys.stderr)
        print("\n".join(long_lines), file=sys.stderr)
        return 1
    print(f"Line length checked: {len(files)} files, "
          f"limit {args.limit} characters.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

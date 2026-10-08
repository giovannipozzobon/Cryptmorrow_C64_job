#!/bin/bash
# Cryptmorrow: build a step of the book, or the complete game, and play
# it in VICE. macOS/Linux version of tools/run-game.ps1. Run it from
# anywhere: it works in the folder above tools/.
#   Build   write the data (game/assets/build_assets.py), check that no
#           line of the sources is longer than 60 characters
#           (tools/check_lines.py) and assemble with 64tass into
#           game/build: cryptmorrow.prg, .lst and .lbl;
#   Play    build, then start the program in VICE (x64sc): a PAL C64
#           with the SID chosen by --model, joystick 2 on the keypad;
#   Verify  build, then run the test of the complete game
#           (tests/verify_game.py), from the root of the package.
# 64tass, x64sc and python3 are looked for on the PATH (Homebrew puts
# them in /opt/homebrew/bin); --assembler, --vice and --python give
# their full paths instead.
#
# Usage: tools/run-game.sh [--mode Build|Play|Verify] [--model 6581|8580]
#                          [--python PATH] [--assembler PATH] [--vice PATH]
set -euo pipefail

mode=Play
model=6581
python=''
assembler=''
vice=''

usage() {
    echo "Usage: $0 [--mode Build|Play|Verify] [--model 6581|8580]" >&2
    echo "       [--python PATH] [--assembler PATH] [--vice PATH]" >&2
    exit 2
}

fail() {
    echo "run-game: $*" >&2
    exit 1
}

while [ $# -gt 0 ]; do
    case "$1" in
        --mode|-Mode)           mode=${2:-}; shift 2 ;;
        --model|-Model)         model=${2:-}; shift 2 ;;
        --python|-Python)       python=${2:-}; shift 2 ;;
        --assembler|-Assembler) assembler=${2:-}; shift 2 ;;
        --vice|-Vice)           vice=${2:-}; shift 2 ;;
        -h|--help)              usage ;;
        *)                      echo "Unknown option: $1" >&2; usage ;;
    esac
done

case "$mode" in
    Build|Play|Verify) ;;
    *) fail "--mode must be Build, Play or Verify, not '$mode'." ;;
esac
case "$model" in
    6581) engine=256 ;;
    8580) engine=257 ;;
    *) fail "--model must be 6581 or 8580, not '$model'." ;;
esac

# find_tool GIVEN SWITCH NAME...: the given path, or the first NAME on
# the PATH.
find_tool() {
    local given=$1 switch=$2 name
    shift 2
    if [ -n "$given" ]; then
        [ -x "$given" ] || fail "Not found: $given"
        echo "$given"
        return
    fi
    for name in "$@"; do
        if command -v "$name" >/dev/null 2>&1; then
            command -v "$name"
            return
        fi
    done
    fail "$1 is not on the PATH: install it (brew install ...)," \
         "add its folder to the PATH, or give its full path with $switch."
}

python=$(find_tool "$python" --python python3 python)
assembler=$(find_tool "$assembler" --assembler 64tass)
if [ "$mode" != Build ]; then
    vice=$(find_tool "$vice" --vice x64sc)
fi

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

mkdir -p game/build
"$python" game/assets/build_assets.py ||
    fail 'The data of game/assets could not be built: see the message above.'
"$python" tools/check_lines.py ||
    fail 'A line of the sources is longer than 60 characters.'
"$assembler" --cbm-prg -Wall -Werror --vice-labels-numeric \
    -l game/build/cryptmorrow.lbl -L game/build/cryptmorrow.lst \
    -o game/build/cryptmorrow.prg game/src/main.asm ||
    fail '64tass stopped: its message names the file and the line.'

case "$mode" in
    Build)
        if [ -f tools/memory_map.py ]; then
            "$python" tools/memory_map.py ||
                fail 'The memory map could not be made.'
        fi
        ;;
    Play)
        # VICE runs on its own: the terminal is free at once.
        nohup "$vice" -default -pal -sound -sidenginemodel "$engine" \
            +VICIIvcache -autostartprgmode 1 -joydev2 1 \
            -autostart "$root/game/build/cryptmorrow.prg" \
            >/dev/null 2>&1 &
        ;;
    Verify)
        [ -f tests/verify_game.py ] ||
            fail 'Verify works from the root of the package. For a step,' \
                 'run python3 tests/verify_step.py or tests/verify_game.py' \
                 'there (chapter 14).'
        "$python" tests/verify_game.py --vice "$vice" ||
            fail 'The test of the game failed: see evidence/game-test.json.'
        ;;
esac

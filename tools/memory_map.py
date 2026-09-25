"""The memory of Cryptmorrow as the assembled program uses it.

Usage: python tools/memory_map.py        (after assembling)

Reads game/build/cryptmorrow.prg and .lbl and the generated data, and
lists every area of the C64's memory from $0801 to $CFFF once the data
are unpacked: what is there, how many bytes, and the free gaps between
the areas; then the zero page the program names in memory.asm. Writes
evidence/memory-map.json and prints the table. tests/verify_game.py
calls build() and puts the same table in its report.
"""
import json
from pathlib import Path
import re
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tests"))
from vicemon import load_labels                 # noqa: E402

GENERATED = PROJECT / "game/assets/generated"
TOP = 0xD000                    # I/O from here; the KERNAL above


def build(labels, prg, memory_asm=None):
    """Areas in address order: (start, end, what), end inclusive.
    memory_asm: the memory.asm of the program (a step of the chain has
    its own); by default game/src/memory.asm."""
    load = prg[0] | prg[1] << 8
    size = {name: (GENERATED / name).stat().st_size for name in (
        "hero.sprites", "objects.sprites", "combat.sprites", "big.font",
        "big.styles", "tiles.bitmap", "tiles.attr", "flames.bin",
        "font.bin", "doors.bin", "screens.bin", "rooms.bin",
        "zones.color")}
    L = labels
    packed = "packed_data" in L
    if packed:
        code_end = L["packed_data"]
        music_end = L["MUSIC_DATA"] + L["packed_end"] - L["b_music"]
    else:                   # step 07 of the chain: no unpack, the PRG
        code_end = L["code_end"]        # holds every block at its
        music_end = load + len(prg) - 2         # address, music last
    areas = [
        (load, code_end - 1, "BASIC line, code, tables and variables"),
        (L["SPRITE_DATA"], None, "explorer sprites", "hero.sprites"),
        (L["OBJECT_SPRITES"], None, "object sprites", "objects.sprites"),
        (L["SCREEN"], L["SCREEN"] + 999, "screen RAM of the bitmap"),
        (L["SPRITE_PTRS"], L["SPRITE_PTRS"] + 7, "sprite pointers"),
        (L["COMBAT_SPRITES"], None, "enemy, dust and blade sprites",
         "combat.sprites"),
        (L["BIG_FONT"], None, "big letters", "big.font"),
        (L["BIG_STYLES"], None, "styles of the big letters",
         "big.styles"),
        (L["BITMAP"], L["BITMAP"] + 7999, "bitmap"),
        (L["TILE_BITMAP"], None, "metatile pictures", "tiles.bitmap"),
        (L["TILE_SCR_L"], L["TILE_COL_R"] + 255,
         "metatile colours of the zone (set_zone)"),
        (L["TILE_ATTR"], None, "metatile attributes", "tiles.attr"),
        (L["FLAMES"], None, "flame frames", "flames.bin"),
        (L["FONT"], None, "font", "font.bin"),
        (L["SOLID_MAP"], L["SOLID_MAP"] + 999, "walkability map"),
        (L["DOOR_TILES"], None, "open door tiles", "doors.bin"),
        (L["TITLE_PAGE"], None, "pages of the title and end screens",
         "screens.bin"),
        (L["ROOM_DATA"], None, "room pages (under the BASIC ROM)",
         "rooms.bin"),
        (L["ZONE_COLOURS"], None, "colour tables of the four zones",
         "zones.color"),
        (L["MUSIC_DATA"], music_end - 1,
         "music, pieces of the end, sound effects"),
    ]
    used = []
    for area in areas:
        start, end, what = area[:3]
        if end is None:
            end = start + size[area[3]] - 1
        used.append((start, end, what))
    used.sort()
    table, cursor, free = [], load, 0
    for start, end, what in used:
        if start < cursor:
            raise SystemExit(f"{what} at ${start:04x} overlaps")
        if start > cursor:
            gap = start - cursor
            note = "free"
            if cursor == code_end and packed:
                note = "free once unpacked (the packed data until then)"
            table.append({"from": f"${cursor:04x}",
                          "to": f"${start - 1:04x}",
                          "bytes": gap, "use": note})
            free += gap
        table.append({"from": f"${start:04x}", "to": f"${end:04x}",
                      "bytes": end - start + 1, "use": what})
        cursor = end + 1
    table.append({"from": f"${cursor:04x}", "to": f"${TOP - 1:04x}",
                  "bytes": TOP - cursor, "use": "free"})
    free += TOP - cursor
    names = re.findall(r"^(\w+)\s*=\s*\$([0-9a-f]{2})\b",
                       Path(memory_asm or PROJECT / "game/src/memory.asm")
                       .read_text(encoding="utf-8"), re.M)
    if "ZP_END" in L:
        zero_page = f"$02-${L['ZP_END'] - 1:02x}, " \
                    f"{len(names) - 1} names in memory.asm"
    else:                       # before step 08: no ZP_END yet
        zero_page = f"$02-${max(int(a, 16) for _, a in names) + 1:02x}, " \
                    f"{len(names)} names in memory.asm"
    return {
        "areas": table,
        "free_bytes_below_io": free,
        "code_bytes": code_end - load,
        "code_limit": f"${L['SPRITE_DATA']:04x}",
        "code_free_bytes": L["SPRITE_DATA"] - code_end,
        "metatiles": size["tiles.bitmap"] // 32,
        "prg_bytes": len(prg),
        "zero_page": zero_page,
        "kernal_vector": "$0314-$0315 (the sound interrupt)",
    }


def main():
    labels = load_labels(PROJECT / "game/build/cryptmorrow.lbl")
    prg = (PROJECT / "game/build/cryptmorrow.prg").read_bytes()
    result = build(labels, prg)
    out = PROJECT / "evidence" / "memory-map.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8",
                   newline="\n")
    print("| From | To | Bytes | Use |")
    print("|---|---|---:|---|")
    for area in result["areas"]:
        print(f"| `{area['from']}` | `{area['to']}` | {area['bytes']} | "
              f"{area['use']} |")
    for key in ("free_bytes_below_io", "code_bytes", "code_free_bytes",
                "metatiles", "prg_bytes", "zero_page"):
        print(f"{key}: {result[key]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

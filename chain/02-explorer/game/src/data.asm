; CRYPTMORROW - data built by game/assets, placed at the
; addresses of memory.asm. Every block checks its size.
GEN = "../assets/generated/"

        * = SPRITE_DATA
        .binary GEN .. "hero.sprites"
        .cerror * != SPRITE_DATA + 8 * 64, "hero frames"
        * = TILE_BITMAP
        .binary GEN .. "tiles.bitmap"
        .cerror * > TILE_BITMAP + 128 * 32, "tile bitmaps"
        * = TILE_ATTR
        .binary GEN .. "tiles.attr"
        .cerror * != TILE_ATTR + 128, "tile attributes"
        * = FLAMES
        .binary GEN .. "flames.bin"
        .cerror * != FLAMES + 32, "flame frames"
        * = FONT
        .binary GEN .. "font.bin"
        .cerror * > SOLID_MAP, "font"
        * = ROOM_DATA
        .binary GEN .. "rooms.bin"
        .cerror * != ROOM_DATA + 16 * 256, "rooms"
        * = ZONE_COLOURS
        .binary GEN .. "zones.color"
        .cerror * != ZONE_COLOURS + 4 * $400, "zones"

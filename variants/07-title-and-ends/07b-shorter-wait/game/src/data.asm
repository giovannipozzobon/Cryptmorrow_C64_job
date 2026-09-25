; CRYPTMORROW - data built by game/assets, placed at the
; addresses of memory.asm. Every block checks its size.
GEN = "../assets/generated/"

        * = SPRITE_DATA
        .binary GEN .. "hero.sprites"
        .cerror * != SPRITE_DATA + 8 * 64, "hero frames"
        * = OBJECT_SPRITES
        .binary GEN .. "objects.sprites"
        .cerror * != OBJECT_SPRITES + 4 * 64, "objects"
        * = COMBAT_SPRITES
        .binary GEN .. "combat.sprites"
        .cerror * != COMBAT_SPRITES + 9 * 64, "combat"
        * = BIG_FONT
        .binary GEN .. "big.font"
        .cerror * != BIG_FONT + 26 * 120, "big letters"
        .cerror * > BIG_STYLES, "big letters too long"
        * = BIG_STYLES
        .binary GEN .. "big.styles"
        .cerror * != BIG_STYLES + 3 * 16, "styles"
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
        * = DOOR_TILES
        .binary GEN .. "doors.bin"
        .cerror * != DOOR_TILES + 4 * 32, "door tiles"
        * = TITLE_PAGE
        .binary GEN .. "screens.bin"
        .cerror * != WON_PAGE + 256, "screen pages"
        * = ROOM_DATA
        .binary GEN .. "rooms.bin"
        .cerror * != ROOM_DATA + 16 * 256, "rooms"
        * = ZONE_COLOURS
        .binary GEN .. "zones.color"
        .cerror * != ZONE_COLOURS + 4 * $400, "zones"
        * = MUSIC_DATA
        .include "../assets/generated/music.asm"
        .cerror * > MUSIC_DATA + $1000, "music data"

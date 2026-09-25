; CRYPTMORROW - data built by game/assets.
; The blocks lie one after the other behind the code,
; each assembled for its address in memory.asm (the
; .logical of 64tass): the PRG has no holes. unpack
; (unpack.asm) copies each block to its address at the
; start. Every block checks its size and that it lies
; below its address in the PRG.
GEN = "../assets/generated/"

packed_data:
b_hero  .logical SPRITE_DATA
        .binary GEN .. "hero.sprites"
        .cerror * != SPRITE_DATA + 8 * 64, "hero frames"
        .endlogical
b_objects .logical OBJECT_SPRITES
        .binary GEN .. "objects.sprites"
        .cerror * != OBJECT_SPRITES + 4 * 64, "objects"
        .endlogical
b_combat .logical COMBAT_SPRITES
        .binary GEN .. "combat.sprites"
        .cerror * != COMBAT_SPRITES + 9 * 64, "combat"
        .endlogical
b_big   .logical BIG_FONT
        .binary GEN .. "big.font"
        .cerror * != BIG_FONT + 26 * 120, "big letters"
        .cerror * > BIG_STYLES, "big letters too long"
        .endlogical
b_styles .logical BIG_STYLES
        .binary GEN .. "big.styles"
        .cerror * != BIG_STYLES + 3 * 16, "styles"
        .endlogical
b_tiles .logical TILE_BITMAP
        .binary GEN .. "tiles.bitmap"
        .cerror * > TILE_BITMAP + 128 * 32, "tile bitmaps"
        .endlogical
b_attr  .logical TILE_ATTR
        .binary GEN .. "tiles.attr"
        .cerror * != TILE_ATTR + 128, "tile attributes"
        .endlogical
b_flames .logical FLAMES
        .binary GEN .. "flames.bin"
        .cerror * != FLAMES + 32, "flame frames"
        .endlogical
b_font  .logical FONT
        .binary GEN .. "font.bin"
        .cerror * > SOLID_MAP, "font"
        .endlogical
b_doors .logical DOOR_TILES
        .binary GEN .. "doors.bin"
        .cerror * != DOOR_TILES + 4 * 32, "door tiles"
        .endlogical
b_pages .logical TITLE_PAGE     ; OVER_PAGE, WON_PAGE
        .binary GEN .. "screens.bin"
        .cerror * != WON_PAGE + 256, "screen pages"
        .endlogical
b_rooms .logical ROOM_DATA      ; under the BASIC ROM
        .binary GEN .. "rooms.bin"
        .cerror * != ROOM_DATA + 16 * 256, "rooms"
        .endlogical
b_zones .logical ZONE_COLOURS   ; copied by set_zone
        .binary GEN .. "zones.color"
        .cerror * != ZONE_COLOURS + 4 * $400, "zones"
        .endlogical
b_music .logical MUSIC_DATA
        .include "../assets/generated/music.asm"
        .cerror * > MUSIC_DATA + $1000, "music data"
        .endlogical
packed_end:

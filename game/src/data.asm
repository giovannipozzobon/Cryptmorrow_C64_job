;|; CRYPTMORROW - data built by game/assets, placed at the {1-7}
;|; addresses of memory.asm. Every block checks its size. {1-7}
; CRYPTMORROW - data built by game/assets. {8}
; The blocks lie one after the other behind the code, {8}
; each assembled for its address in memory.asm (the {8}
; .logical of 64tass): the PRG has no holes. unpack {8}
; (unpack.asm) copies each block to its address at the {8}
; start. Every block checks its size and that it lies {8}
; below its address in the PRG. {8}
GEN = "../assets/generated/"

packed_data:                    ; {8}
b_hero  .logical SPRITE_DATA    ; {8}
;|        * = SPRITE_DATA {2-7}
        .binary GEN .. "hero.sprites" ; {2}
        .cerror * != SPRITE_DATA + 8 * 64, "hero frames" ; {2}
        .endlogical             ; {8}
b_objects .logical OBJECT_SPRITES ; {8}
;|        * = OBJECT_SPRITES {4-7}
        .binary GEN .. "objects.sprites" ; {4}
        .cerror * != OBJECT_SPRITES + 4 * 64, "objects" ; {4}
        .endlogical             ; {8}
b_combat .logical COMBAT_SPRITES ; {8}
;|        * = COMBAT_SPRITES {5-7}
        .binary GEN .. "combat.sprites" ; {5}
        .cerror * != COMBAT_SPRITES + 9 * 64, "combat" ; {5}
        .endlogical             ; {8}
b_big   .logical BIG_FONT       ; {8}
;|        * = BIG_FONT {7-7}
        .binary GEN .. "big.font" ; {7}
        .cerror * != BIG_FONT + 26 * 120, "big letters" ; {7}
        .cerror * > BIG_STYLES, "big letters too long" ; {7}
        .endlogical             ; {8}
b_styles .logical BIG_STYLES    ; {8}
;|        * = BIG_STYLES {7-7}
        .binary GEN .. "big.styles" ; {7}
        .cerror * != BIG_STYLES + 3 * 16, "styles" ; {7}
        .endlogical             ; {8}
b_tiles .logical TILE_BITMAP    ; {8}
;|        * = TILE_BITMAP {1-7}
        .binary GEN .. "tiles.bitmap"
        .cerror * > TILE_BITMAP + 128 * 32, "tile bitmaps"
        .endlogical             ; {8}
b_attr  .logical TILE_ATTR      ; {8}
;|        * = TILE_ATTR {1-7}
        .binary GEN .. "tiles.attr"
        .cerror * != TILE_ATTR + 128, "tile attributes"
        .endlogical             ; {8}
b_flames .logical FLAMES        ; {8}
;|        * = FLAMES {1-7}
        .binary GEN .. "flames.bin"
        .cerror * != FLAMES + 32, "flame frames"
        .endlogical             ; {8}
b_font  .logical FONT           ; {8}
;|        * = FONT {1-7}
        .binary GEN .. "font.bin"
        .cerror * > SOLID_MAP, "font"
        .endlogical             ; {8}
b_doors .logical DOOR_TILES     ; {8}
;|        * = DOOR_TILES {4-7}
        .binary GEN .. "doors.bin" ; {4}
        .cerror * != DOOR_TILES + 4 * 32, "door tiles" ; {4}
        .endlogical             ; {8}
b_pages .logical TITLE_PAGE     ; OVER_PAGE, WON_PAGE {8}
;|        * = TITLE_PAGE {7-7}
        .binary GEN .. "screens.bin" ; {7}
        .cerror * != WON_PAGE + 256, "screen pages" ; {7}
        .endlogical             ; {8}
b_rooms .logical ROOM_DATA      ; under the BASIC ROM {8}
;|        * = ROOM_DATA {1-7}
        .binary GEN .. "rooms.bin"
        .cerror * != ROOM_DATA + 16 * 256, "rooms"
        .endlogical             ; {8}
b_zones .logical ZONE_COLOURS   ; copied by set_zone {8}
;|        * = ZONE_COLOURS {1-7}
        .binary GEN .. "zones.color"
        .cerror * != ZONE_COLOURS + 4 * $400, "zones"
        .endlogical             ; {8}
b_music .logical MUSIC_DATA     ; {8}
;|        * = MUSIC_DATA {6-7}
        .include "../assets/generated/music.asm" ; {6}
        .cerror * > MUSIC_DATA + $1000, "music data" ; {6}
        .endlogical             ; {8}
packed_end:                     ; {8}

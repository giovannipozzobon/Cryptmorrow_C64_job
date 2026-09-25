# Route of step 04, planned by tools/plan_route.py --step 4
# tools/route_step_04.py: do not edit, plan again.
from hero_model import (JOY_UP as U, JOY_DOWN as D, JOY_LEFT as L,
                        JOY_RIGHT as R, JOY_FIRE as F)  # noqa: F401

SCRIPT = [
    (0, 16, 'blocked', 'step04-start.png'),         # the start: HUD, the Moss Gate
    (U, 60, 'moves', None),                         # north to the gate
    (U, 8, 'blocked', None),                        # the portal: shut without the three seals
    (D, 99, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (D, 58, 'moves', None),                         # to the west opening
    (L, 128, 'moves', None),
    (L, 24, 4, None),                               # west opening: Root Cellar
    (L, 29, 'moves', None),                         # onto the potion: full energy, it stays
    (U, 39, 'moves', None),
    (D, 58, 'moves', None),                         # against the locked door
    (L, 101, 'moves', None),
    (D, 42, 'moves', None),
    (D, 8, 'blocked', None),                        # door A without key: stays shut
    (R, 16, 'moves', None),                         # under the north opening
    (U, 119, 'moves', None),
    (U, 24, 0, None),                               # north opening: Bone Pit
    (R, 85, 'moves', None),                         # treasure
    (U, 73, 'moves', None),
    (L, 208, 'moves', None),                        # the potion: it stays
    (D, 64, 'moves', None),
    (R, 123, 'moves', None),                        # above the south steps
    (D, 11, 'moves', None),
    (D, 24, 4, None),                               # south opening: Root Cellar
    (D, 75, 'moves', None),                         # to the east opening
    (R, 102, 'moves', None),
    (U, 19, 'moves', None),
    (R, 14, 'moves', None),
    (R, 16, 5, None),                               # east opening: Crossroads
    (R, 266, 'moves', None),                        # across the Crossroads
    (R, 20, 6, None),                               # east opening: Long Gallery
    (R, 255, 'moves', None),                        # treasure
    (D, 57, 'moves', None),
    (R, 1, 'moves', None),                          # along the corridor to the east
    (U, 61, 'moves', None),
    (R, 20, 'moves', None),                         # door B without key: stays shut
    (L, 22, 'moves', None),                         # under the north opening
    (U, 54, 'moves', None),
    (U, 20, 2, None),                               # north opening: Old Well
    (L, 11, 'moves', None),                         # treasure
    (U, 93, 'moves', None),
    (0, 16, 'blocked', 'step04-old-well.png'),      # key A still on the floor
    (L, 208, 'moves', None),                        # key A
    (R, 95, 'moves', None),                         # against the well
    (D, 20, 'moves', None),
    (D, 8, 'blocked', None),                        # the well
    (R, 124, 'moves', None),                        # above the south steps
    (D, 71, 'moves', None),
    (D, 24, 6, None),                               # south opening: Long Gallery
    (D, 48, 'moves', None),                         # to the west opening
    (L, 244, 'moves', None),
    (L, 24, 5, None),                               # west opening: Crossroads
    (L, 262, 'moves', None),                        # to the west opening
    (D, 8, 'moves', None),
    (L, 24, 4, None),                               # west opening: Root Cellar
    (L, 48, 'moves', None),                         # against the door
    (D, 61, 'moves', None),
    (L, 82, 'moves', None),
    (D, 1, 'blocked', None),                        # door A opens with key A
    (D, 30, 8, None),                               # through the door: Ossuary
    (R, 101, 'moves', None),                        # the potion: full energy, it stays
    (D, 82, 'moves', None),
    (L, 181, 'moves', None),                        # above the south opening
    (D, 11, 'moves', None),
    (D, 24, 12, None),                              # south opening: Catacombs
    (D, 17, 'moves', None),                         # key B
    (R, 181, 'moves', None),
    (L, 208, 'moves', None),                        # treasure
    (D, 80, 'moves', None),
    (R, 245, 'moves', None),                        # to the east opening
    (U, 19, 'moves', None),
    (R, 16, 13, None),                              # east opening: Bone Shrine
    (R, 137, 'moves', None),                        # seal A
    (U, 45, 'moves', None),
    (U, 6, 'moves', None),                          # up to the altar
    (U, 8, 'blocked', None),                        # the altar
    (D, 51, 'moves', None),                         # to the west opening
    (L, 137, 'moves', None),
    (L, 24, 12, None),                              # west opening: Catacombs
    (L, 32, 'moves', None),                         # under the north opening
    (U, 41, 'moves', None),
    (L, 178, 'moves', None),
    (U, 39, 'moves', None),
    (U, 24, 8, None),                               # north opening: Ossuary
    (R, 80, 'moves', None),                         # under the north opening
    (U, 108, 'moves', None),
    (U, 24, 4, None),                               # north opening, open door: Root Cellar
    (R, 86, 'moves', None),                         # to the east opening
    (U, 50, 'moves', None),
    (R, 46, 'moves', None),
    (R, 16, 5, None),                               # east opening: Crossroads
    (R, 266, 'moves', None),                        # across the Crossroads
    (R, 20, 6, None),                               # east opening: Long Gallery
    (R, 256, 'moves', None),                        # along the corridor to the east
    (U, 4, 'moves', None),
    (R, 20, 'moves', None),                         # door B opens with key B
    (R, 30, 7, None),                               # through door B: Flooded Stair
    (R, 77, 'moves', None),                         # the potion: it stays
    (U, 35, 'moves', None),
    (R, 143, 'moves', None),
    (L, 105, 'moves', None),                        # under the north opening
    (U, 19, 'moves', None),
    (U, 24, 3, None),                               # north opening: Black Cistern
    (L, 7, 'moves', None),                          # key C
    (U, 41, 'moves', None),
    (D, 32, 'moves', None),                         # the potion: it stays
    (R, 112, 'moves', None),
    (L, 105, 'moves', None),                        # above the south steps
    (D, 11, 'moves', None),
    (D, 24, 7, None),                               # south opening: Flooded Stair
    (D, 11, 'moves', None),                         # round the water to the south steps
    (L, 70, 'moves', None),
    (D, 97, 'moves', None),
    (R, 70, 'moves', None),
    (D, 24, 11, None),                              # south opening: Drowned Shrine
    (D, 11, 'moves', None),                         # treasure
    (L, 74, 'moves', None),
    (D, 54, 'moves', None),
    (L, 29, 'moves', None),
    (R, 33, 'moves', None),                         # seal B
    (U, 16, 'moves', None),
    (R, 79, 'moves', None),
    (L, 31, 'moves', None),                         # under the north opening
    (U, 28, 'moves', None),
    (R, 22, 'moves', None),
    (U, 23, 'moves', None),
    (U, 24, 7, None),                               # north opening: Flooded Stair
    (L, 122, 'moves', None),                        # round the water to the west opening
    (U, 51, 'moves', None),
    (L, 6, 'moves', None),
    (L, 24, 6, None),                               # west opening, open door B: Long Gallery
    (L, 262, 'moves', None),                        # along the corridor to the west
    (L, 24, 5, None),                               # west opening: Crossroads
    (L, 134, 'moves', None),                        # to the south steps
    (D, 62, 'moves', None),
    (D, 12, 9, None),                               # south opening: Sunken Hall
    (L, 7, 'moves', None),                          # treasure
    (D, 99, 'moves', None),
    (U, 12, 'moves', None),                         # to the east door
    (R, 129, 'moves', None),
    (U, 17, 'moves', None),
    (R, 20, 'moves', None),                         # door C opens with key C
    (R, 30, 10, None),                              # through door C: Amber Hall
    (D, 40, 'moves', None),                         # above the south steps
    (R, 115, 'moves', None),
    (D, 24, 14, None),                              # south opening: Treasury
    (D, 17, 'moves', None),                         # treasure
    (L, 103, 'moves', None),
    (R, 208, 'moves', None),                        # treasure
    (D, 67, 'moves', None),                         # to the east opening
    (R, 37, 'moves', None),
    (R, 16, 15, None),                              # east opening: Sun Vault
    (R, 58, 'moves', None),                         # seal C
    (U, 35, 'moves', None),
    (R, 47, 'moves', None),
    (L, 99, 'moves', None),                         # to the west opening
    (D, 35, 'moves', None),
    (L, 6, 'moves', None),
    (L, 24, 14, None),                              # west opening: Treasury
    (L, 134, 'moves', None),                        # under the north opening
    (U, 86, 'moves', None),
    (U, 24, 10, None),                              # north opening: Amber Hall
    (U, 28, 'moves', None),                         # to the west opening
    (L, 128, 'moves', None),
    (L, 24, 9, None),                               # west opening, open door C: Sunken Hall
    (L, 134, 'moves', None),                        # under the north opening
    (U, 80, 'moves', None),
    (U, 24, 5, None),                               # north opening: Crossroads
    (U, 108, 'moves', None),                        # under the north opening
    (U, 24, 1, None),                               # north opening: Moss Gate
    (U, 87, 'moves', None),                         # before the gate
    (U, 1, 'blocked', None),                        # the portal opens with the three seals
    (0, 16, 'blocked', 'step04-portal.png'),        # the open portal
    (U, 33, 'ending', None),                        # north through the portal: VICTORY
    (U, 16, 'still', 'step04-victory.png'),         # the game stands still
    (L, 50, 'still', None),                         # the stick does nothing any more
    ('restart', -1, 'start', None),                 # the program started again: a new game
    ('energy', 4, 'set', None),                     # the test takes four cells of energy
    (D, 39, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (D, 58, 'moves', None),                         # to the west opening
    (L, 128, 'moves', None),
    (L, 24, 4, None),                               # west opening: Root Cellar
    (L, 29, 'moves', None),                         # the potion: two cells more, six
    (U, 39, 'moves', None),
    (0, 16, 'blocked', None),                       # the game goes on
]

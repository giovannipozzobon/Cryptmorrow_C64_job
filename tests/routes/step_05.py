# Route of step 05, planned by tools/plan_route.py --step 5
# tools/route_step_05.py: do not edit, plan again.
from hero_model import (JOY_UP as U, JOY_DOWN as D, JOY_LEFT as L,
                        JOY_RIGHT as R, JOY_FIRE as F)  # noqa: F401

SCRIPT = [
    (0, 16, 'blocked', 'step05-start.png'),         # idle at the start
    ('align', 17, 'idle', None),
    (U, 60, 'moves', None),                         # north to the gate
    (U, 8, 'blocked', None),                        # the portal: shut without the three seals
    (D | R, 24, 'moves', None),                     # diagonal: horizontal wins
    (U | D, 8, 'moves', None),                      # both vertical bits: up wins
    (F, 30, 'blocked', None),                       # Fire held: one blow only, standing still
    (0, 4, 'blocked', None),                        # released
    (L | F, 16, 'moves', None),                     # Fire while walking: the explorer stops while the blade is out
    (D, 8, 'moves', None),                          # to the south steps
    (L, 22, 'moves', None),
    (D, 99, 'moves', None),
    (D, 12, 5, None),                               # south opening: Crossroads
    (U, 24, 1, None),                               # north opening: Moss Gate
    (D, 24, 5, None),                               # south again: Crossroads
    (D, 16, 'moves', None),                         # onto the skeleton's row
    (R, 52, 'moves', None),
    (D, 70, 'moves', None),
    (L, 85, 'fight', None),                         # skeleton: three blows
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 16, 'moves', None),                         # to the west opening
    (L, 94, 'moves', None),
    (U, 11, 'moves', None),
    (L, 24, 4, None),                               # west opening: Root Cellar
    (L, 29, 'moves', None),                         # onto the potion: full energy, it stays
    (U, 39, 'moves', None),
    (D, 56, 'moves', None),                         # towards the bat
    (L, 18, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (D, 2, 'moves', None),
    (L, 35, 'moves', None),
    (U, 7, 'moves', None),
    (L, 48, 'moves', None),                         # against the locked door
    (D, 49, 'moves', None),
    (D, 8, 'blocked', None),                        # door A without key: stays shut
    (R, 16, 'moves', None),                         # under the north opening
    (U, 119, 'moves', None),
    (U, 24, 0, None),                               # north opening: Bone Pit
    (U, 1, 'fight', None),                          # the bone pit bat
    (0, 1, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 72, 'moves', None),                         # onto the skeleton's row
    (L, 69, 'moves', None),
    (U, 13, 'moves', None),
    (R, 39, 'fight', None),                         # the bone pit skeleton
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 113, 'moves', None),                        # treasure
    (D, 14, 'moves', None),
    (L, 208, 'moves', None),                        # the potion
    (D, 64, 'moves', None),
    (R, 123, 'moves', None),                        # above the south steps
    (D, 11, 'moves', None),
    (D, 24, 4, None),                               # south opening: Root Cellar
    (D, 16, 'moves', None),                         # down towards the bat
    (D, 5, 'fight', None),                          # an enemy in the way
    (L, 1, 'fight', None),
    (D, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 1, 'moves', None),
    (D, 6, 'moves', None),
    (D, 47, 'moves', None),                         # to the east opening
    (R, 72, 'moves', None),
    (U, 8, 'moves', None),
    (R, 44, 'moves', None),
    (U, 11, 'moves', None),
    (R, 16, 5, None),                               # east opening: Crossroads
    (R, 266, 'moves', None),                        # across the Crossroads
    (R, 20, 6, None),                               # east opening: Long Gallery
    (R, 26, 'moves', None),                         # into the corridor
    (U, 4, 'moves', None),
    (R, 164, 'fight', None),                        # the corridor skeleton
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (D, 56, 'moves', None),                         # down to the lower row
    (L, 5, 'moves', None),
    (D, 9, 'moves', None),
    (L, 74, 'fight', None),                         # the second skeleton
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 144, 'moves', None),                        # treasure
    (U, 2, 'moves', None),
    (R, 1, 'moves', None),                          # along the corridor to the east
    (U, 61, 'moves', None),
    (R, 20, 'moves', None),                         # door B without key: stays shut
    (L, 22, 'moves', None),                         # under the north opening
    (U, 54, 'moves', None),
    (U, 20, 2, None),                               # north opening: Old Well
    (L, 11, 'moves', None),                         # treasure
    (U, 93, 'moves', None),
    (L, 10, 'fight', None),                         # towards the bat
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 23, 'moves', None),
    (D, 3, 'moves', None),
    (L, 175, 'moves', None),                        # key A
    (U, 3, 'moves', None),
    (0, 16, 'blocked', None),
    ('align', 15, 'idle', None),
    (R, 95, 'moves', None),                         # against the well
    (D, 20, 'moves', None),
    (D, 8, 'blocked', None),                        # the well
    (R, 124, 'moves', None),                        # above the south steps
    (D, 71, 'moves', None),
    (D, 24, 6, None),                               # south opening: Long Gallery
    (L, 14, 'moves', None),                         # down into the corridor
    (D, 52, 'moves', None),
    (L, 4, 'fight', None),                          # the corridor skeleton is back
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 225, 'moves', None),                        # to the west opening
    (U, 3, 'moves', None),
    (L, 24, 5, None),                               # west opening: Crossroads
    (L, 262, 'moves', None),                        # to the west opening
    (D, 8, 'moves', None),
    (L, 24, 4, None),                               # west opening: Root Cellar
    (L, 16, 'moves', None),                         # towards the bat
    (D, 19, 'moves', None),
    (L, 64, 'moves', None),
    (F, 1, 'fight', None),                          # an enemy in the way
    (0, 8, 'fight', None),
    (L, 2, 'moves', None),
    (U, 7, 'moves', None),
    (L, 48, 'moves', None),                         # against the door
    (D, 49, 'moves', None),
    (D, 1, 'blocked', None),                        # door A opens with key A
    (D, 30, 8, None),                               # through the door: Ossuary
    (R, 4, 'fight', None),                          # the ossuary bat
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 84, 'moves', None),                         # onto the skeleton's row
    (D, 85, 'moves', None),
    (L, 171, 'fight', None),                        # the ossuary skeleton
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (0, 16, 'blocked', None),
    ('align', 2, 'idle', None),
    (R, 185, 'moves', None),                        # the potion, energy below full
    (U, 2, 'moves', None),
    (L, 181, 'moves', None),                        # above the south opening
    (D, 11, 'moves', None),
    (D, 24, 12, None),                              # south opening: Catacombs
    (L, 10, 'fight', None),                         # the catacomb bat
    (0, 1, 'fight', None),
    (D, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (D, 2, 'fight', None),                          # the upper skeleton
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 2, 'fight', None),
    (D, 1, 'fight', None),
    (R, 2, 'fight', None),
    (D, 6, 'fight', None),
    (R, 108, 'fight', None),
    (D, 2, 'fight', None),
    (R, 14, 'fight', None),
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 63, 'moves', None),                         # key B
    (D, 5, 'moves', None),
    (L, 3, 'moves', None),                          # onto the lower row
    (D, 83, 'moves', None),
    (L, 105, 'fight', None),                        # the lower skeleton
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 99, 'moves', None),                         # treasure
    (U, 2, 'moves', None),
    (R, 245, 'moves', None),                        # to the east opening
    (U, 19, 'moves', None),
    (R, 16, 13, None),                              # east opening: Bone Shrine
    (R, 12, 'fight', None),                         # the first shrine bat
    (0, 1, 'fight', None),
    (U, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 56, 'moves', None),                         # towards the second bat
    (R, 17, 'fight', None),                         # an enemy in the way
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 48, 'moves', None),
    (R, 19, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 27, 'moves', None),
    (U, 38, 'moves', None),
    (L, 44, 'moves', None),                         # below the skeleton, over the seal
    (D, 62, 'moves', None),
    (R, 1, 'moves', None),                          # seal A
    (U, 67, 'moves', None),
    (U, 6, 'moves', None),                          # up to the altar
    (U, 8, 'blocked', None),                        # the altar
    (D, 48, 'moves', None),                         # to the west opening
    (L, 137, 'moves', None),
    (D, 3, 'moves', None),
    (L, 24, 12, None),                              # west opening: Catacombs, enemies back
    (L, 152, 'moves', None),                        # west along the lower rows
    (L, 23, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 15, 'moves', None),
    (L, 52, 'moves', None),                         # up the left side
    (U, 50, 'moves', None),
    (R, 5, 'fight', None),                          # the upper skeleton is back
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 26, 'moves', None),                         # under the north opening
    (U, 29, 'moves', None),
    (U, 24, 8, None),                               # north opening: Ossuary
    (R, 70, 'fight', None),                         # the ossuary skeleton is back
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (R, 34, 'fight', None),
    (U, 5, 'fight', None),
    (R, 11, 'fight', None),
    (U, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 46, 'moves', None),                         # towards the bat
    (U, 73, 'moves', None),
    (U, 40, 'moves', None),                         # under the north opening
    (U, 24, 4, None),                               # north opening, open door: Root Cellar
    (F, 1, 'fight', None),                          # the cellar bat is back
    (0, 8, 'fight', None),
    (R, 86, 'moves', None),                         # to the east opening
    (U, 40, 'moves', None),
    (R, 46, 'moves', None),
    (U, 10, 'moves', None),
    (R, 16, 5, None),                               # east opening: Crossroads
    (R, 266, 'moves', None),                        # across the Crossroads
    (R, 20, 6, None),                               # east opening: Long Gallery
    (R, 26, 'moves', None),                         # into the corridor
    (U, 4, 'moves', None),
    (R, 164, 'fight', None),                        # the corridor skeleton is back
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 65, 'moves', None),                         # along the corridor to the east
    (D, 1, 'moves', None),
    (R, 20, 'moves', None),                         # door B opens with key B
    (R, 30, 7, None),                               # through door B: Flooded Stair
    (D, 8, 'moves', None),                          # towards the bat
    (R, 128, 'moves', None),
    (R, 6, 'fight', None),                          # an enemy in the way
    (D, 9, 'fight', None),
    (0, 5, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (0, 12, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 22, 'moves', None),
    (U, 5, 'moves', None),
    (R, 24, 'moves', None),                         # beside the skeleton's column
    (R, 39, 'moves', None),                         # the potion
    (U, 47, 'moves', None),
    (L, 105, 'moves', None),                        # under the north opening
    (U, 19, 'moves', None),
    (U, 24, 3, None),                               # north opening: Black Cistern
    (R, 32, 'moves', None),                         # towards the right bat
    (R, 10, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 10, 'moves', None),
    (L, 40, 'moves', None),                         # towards the left bat
    (L, 17, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 43, 'moves', None),
    (L, 60, 'moves', None),                         # up the left side
    (U, 72, 'moves', None),
    (U, 2, 'fight', None),                          # an enemy in the way
    (0, 3, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 1, 'moves', None),
    (U, 12, 'moves', None),
    (D, 71, 'moves', None),                         # key C
    (R, 101, 'moves', None),
    (U, 26, 'moves', None),
    (D, 32, 'moves', None),                         # the potion
    (R, 112, 'moves', None),
    (L, 105, 'moves', None),                        # above the south steps
    (D, 11, 'moves', None),
    (D, 24, 7, None),                               # south opening: Flooded Stair
    (D, 11, 'moves', None),                         # round the water to the south steps
    (L, 40, 'moves', None),
    (D, 48, 'moves', None),
    (R, 16, 'moves', None),
    (R, 22, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 24, 'moves', None),
    (D, 48, 'moves', None),
    (L, 22, 'moves', None),
    (D, 1, 'moves', None),
    (D, 24, 11, None),                              # south opening: Drowned Shrine
    (D, 16, 'moves', None),                         # towards the bat on the left
    (L, 28, 'moves', None),
    (D, 4, 'moves', None),
    (L, 1, 'fight', None),                          # the shrine bat on the left
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (D, 24, 'moves', None),                         # towards the bat on the right
    (R, 8, 'moves', None),
    (R, 17, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 32, 'moves', None),
    (D, 12, 'moves', None),
    (L, 46, 'moves', None),                         # above the skeleton's row
    (D, 22, 'moves', None),
    (L, 2, 'fight', None),                          # the fast skeleton of the shrine
    (D, 5, 'fight', None),
    (L, 1, 'fight', None),
    (D, 7, 'fight', None),
    (L, 3, 'fight', None),
    (D, 1, 'fight', None),
    (0, 3, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 48, 'moves', None),                         # treasure
    (U, 8, 'moves', None),
    (L, 30, 'moves', None),
    (U, 18, 'moves', None),
    (R, 32, 'moves', None),                         # seal B
    (U, 16, 'moves', None),
    (R, 80, 'moves', None),
    (0, 16, 'blocked', None),
    ('align', 20, 'idle', None),
    (L, 31, 'moves', None),                         # under the north opening
    (U, 28, 'moves', None),
    (R, 22, 'moves', None),
    (U, 23, 'moves', None),
    (U, 24, 7, None),                               # north opening: Flooded Stair
    (L, 72, 'moves', None),                         # round the water to the west opening
    (U, 40, 'moves', None),
    (L, 56, 'moves', None),
    (U, 11, 'moves', None),
    (L, 24, 6, None),                               # west opening, open door B: Long Gallery
    (L, 54, 'fight', None),                         # the corridor skeleton is back
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 207, 'moves', None),                        # along the corridor to the west
    (D, 1, 'moves', None),
    (L, 24, 5, None),                               # west opening: Crossroads
    (L, 52, 'moves', None),                         # above the skeleton's row
    (D, 12, 'moves', None),
    (L, 144, 'fight', None),                        # the crossroads skeleton is back
    (D, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 62, 'moves', None),                         # to the south steps
    (D, 49, 'moves', None),
    (D, 12, 9, None),                               # south opening: Sunken Hall
    (D, 13, 'moves', None),                         # towards the bat
    (L, 32, 'moves', None),
    (D, 7, 'fight', None),                          # an enemy in the way
    (L, 10, 'fight', None),
    (D, 1, 'fight', None),
    (L, 1, 'fight', None),
    (D, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 5, 'moves', None),
    (D, 48, 'moves', None),
    (D, 7, 'moves', None),                          # above the skeleton's row
    (R, 50, 'moves', None),
    (U, 7, 'moves', None),
    (D, 1, 'fight', None),                          # the sunken hall skeleton
    (U, 7, 'fight', None),
    (R, 2, 'fight', None),
    (U, 2, 'fight', None),
    (R, 1, 'fight', None),
    (D, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 12, 'moves', None),                         # treasure
    (D, 36, 'moves', None),
    (U, 12, 'moves', None),                         # to the east door
    (R, 129, 'moves', None),
    (U, 17, 'moves', None),
    (R, 20, 'moves', None),                         # door C opens with key C
    (R, 30, 10, None),                              # through door C: Amber Hall
    (R, 27, 'moves', None),                         # above the lower skeleton's row
    (D, 16, 'moves', None),
    (R, 58, 'fight', None),                         # the lower fast skeleton
    (D, 7, 'fight', None),
    (R, 13, 'fight', None),
    (U, 1, 'fight', None),
    (0, 2, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 2, 'moves', None),                          # below the upper skeleton's row
    (U, 38, 'moves', None),
    (U, 4, 'fight', None),                          # the upper fast skeleton
    (0, 2, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 1, 'fight', None),                          # towards the bat
    (0, 11, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 51, 'moves', None),
    (D, 37, 'moves', None),
    (L, 32, 'moves', None),                         # above the south steps
    (D, 24, 'moves', None),
    (D, 24, 14, None),                              # south opening: Treasury
    (D, 20, 'moves', None),                         # above the upper skeleton's row
    (D, 6, 'fight', None),                          # the upper fast skeleton of the treasury
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 6, 'fight', None),
    (0, 6, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 12, 'fight', None),                         # down the left side
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 5, 'moves', None),
    (L, 103, 'moves', None),
    (D, 47, 'moves', None),
    (D, 8, 'moves', None),                          # above the lower skeleton's row
    (R, 60, 'moves', None),
    (D, 8, 'moves', None),
    (F, 1, 'fight', None),                          # the lower fast skeleton of the treasury
    (0, 8, 'fight', None),
    (L, 7, 'fight', None),
    (D, 1, 'fight', None),
    (0, 4, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 48, 'moves', None),                         # treasure
    (U, 68, 'moves', None),
    (R, 208, 'moves', None),                        # treasure
    (0, 16, 'blocked', None),
    ('align', 19, 'idle', None),
    (D, 64, 'moves', None),                         # to the east opening
    (R, 37, 'moves', None),
    (D, 3, 'moves', None),
    (R, 16, 15, None),                              # east opening: Sun Vault
    (D, 7, 'moves', None),                          # towards the lower bat
    (R, 72, 'moves', None),
    (R, 17, 'fight', None),                         # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 21, 'moves', None),
    (U, 7, 'moves', None),
    (U, 16, 'moves', None),                         # towards the upper bat
    (L, 1, 'fight', None),                          # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 16, 'moves', None),
    (L, 69, 'moves', None),
    (U, 4, 'moves', None),
    (R, 152, 'moves', None),                        # beside the skeleton's column
    (D, 4, 'moves', None),
    (R, 1, 'fight', None),                          # the fast skeleton of the vault, up and down
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (R, 9, 'fight', None),
    (D, 1, 'fight', None),
    (0, 2, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 97, 'moves', None),                         # seal C
    (U, 4, 'moves', None),
    (L, 48, 'moves', None),                         # to the west opening
    (D, 32, 'moves', None),
    (L, 57, 'moves', None),
    (D, 3, 'moves', None),
    (L, 24, 14, None),                              # west opening: Treasury, enemies back
    (L, 134, 'moves', None),                        # into the middle passage
    (U, 26, 'moves', None),
    (F, 1, 'fight', None),                          # the upper skeleton is back
    (0, 8, 'fight', None),
    (U, 1, 'fight', None),
    (R, 1, 'fight', None),
    (U, 1, 'fight', None),
    (0, 9, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 1, 'moves', None),                          # under the north opening
    (U, 56, 'moves', None),
    (D, 1, 'fight', None),                          # an enemy in the way
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 3, 'moves', None),
    (U, 24, 10, None),                              # north opening: Amber Hall
    (F, 1, 'fight', None),                          # the lower skeleton is back at once
    (0, 8, 'fight', None),
    (L, 4, 'fight', None),
    (0, 5, 'fight', None),
    (L, 2, 'fight', None),
    (0, 2, 'fight', None),
    (L, 1, 'fight', None),
    (R, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 24, 'moves', None),                         # to the west opening
    (L, 122, 'moves', None),
    (U, 4, 'moves', None),
    (L, 24, 9, None),                               # west opening, open door C: Sunken Hall
    (L, 7, 'fight', None),                          # under the north opening
    (D, 1, 'fight', None),
    (L, 14, 'fight', None),
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 112, 'moves', None),
    (U, 80, 'moves', None),
    (U, 24, 5, None),                               # north opening: Crossroads
    (F, 1, 'fight', None),                          # the crossroads skeleton is back
    (0, 8, 'fight', None),
    (R, 1, 'fight', None),
    (U, 2, 'fight', None),
    (R, 36, 'fight', None),
    (U, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (U, 7, 'fight', None),
    (R, 1, 'fight', None),
    (0, 4, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (L, 38, 'moves', None),                         # under the north opening
    (U, 98, 'moves', None),
    (U, 24, 1, None),                               # north opening: Moss Gate
    (U, 87, 'moves', None),                         # before the gate
    (U, 1, 'blocked', None),                        # the portal opens with the three seals
    (0, 16, 'blocked', None),                       # the open portal
    ('align', 14, 'idle', None),
    (U, 33, 'ending', None),                        # north through the portal: VICTORY
    (U, 16, 'still', 'step05-victory.png'),         # the game stands still
    (L, 50, 'still', None),                         # the stick does nothing any more
    ('restart', -1, 'start', None),                 # the program started again: a game to lose
    (D, 39, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (D, 86, 'moves', None),                         # into the skeleton's way
    (R, 52, 'moves', None),
    (0, 204, 'blocked', None),                      # the skeleton hurts: the explorer blinks
    (0, 45, 'blocked', None),                       # it passes again and again: two cells of energy left
    (U, 1, 'moves', None),                          # facing up, away from the skeleton's row
    (F, 260, 'ending', None),                       # Fire held: one blow, then GAME OVER
    (F, 16, 'still', 'step05-game-over.png'),       # Fire still held: the game stands still
    ('restart', -1, 'start', None),                 # the program started again: the test helps
    (D, 39, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    ('slow', 0, 'set', None),                       # the test makes the skeleton slow
    (0, 48, 'blocked', None),                       # a slow patrol: one pixel every other frame
    (D, 48, 'moves', None),                         # to the west opening
    (L, 128, 'moves', None),
    (D, 10, 'moves', None),
    (L, 24, 4, None),                               # west opening: Root Cellar
    ('enemy', 0, (20, 110), None),                  # the test moves the bat far to the west
    (0, 24, 'blocked', None),                       # a bat 262 pixels away stays asleep
    ('energy', 2, 'set', None),                     # the test leaves two cells of energy
    (L, 29, 'moves', None),                         # the potion: two cells more, four
    (U, 39, 'moves', None),
    (D, 58, 'moves', None),                         # west, below the pillars
    (L, 103, 'moves', None),
    (D, 13, 'moves', None),
    ('energy', 1, 'set', None),                     # the test leaves one cell of energy
    (L, 83, 'ending', None),                        # west: the bat wakes and touches, two cells taken from one: energy 0, GAME OVER
    (L, 16, 'still', None),                         # the game stands still
    ('restart', -1, 'start', None),                 # the program started again: a fourth game
    (D, 39, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (0, 12, 'blocked', None),                       # rest
]

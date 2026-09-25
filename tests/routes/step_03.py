# Route of step 03, planned by tools/plan_route.py --step 3
# tools/route_step_03.py: do not edit, plan again.
from hero_model import (JOY_UP as U, JOY_DOWN as D, JOY_LEFT as L,
                        JOY_RIGHT as R, JOY_FIRE as F)  # noqa: F401

SCRIPT = [
    (0, 16, 'blocked', 'step03-dungeon.png'),       # the start room with the HUD
    (L, 120, 'moves', None),                        # west until the pillar stops the explorer
    (R, 90, 'moves', None),                         # north to the gate
    (U, 60, 'moves', None),
    (U, 8, 'blocked', None),                        # the portal: shut
    (D, 99, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (D, 48, 'moves', None),                         # to the west opening
    (L, 128, 'moves', None),
    (D, 10, 'moves', None),
    (L, 24, 4, None),                               # west opening: Root Cellar
    (L, 16, 'moves', None),                         # against door A
    (D, 19, 'moves', None),
    (L, 114, 'moves', None),
    (D, 42, 'moves', None),
    (D, 8, 'blocked', None),                        # door A: shut
    (R, 16, 'moves', None),                         # under the north opening
    (U, 119, 'moves', None),
    (U, 24, 0, None),                               # north opening: Bone Pit
    (D, 2, 'moves', None),                          # above the south steps
    (D, 24, 4, None),                               # south opening: Root Cellar
    (D, 75, 'moves', None),                         # to the east opening
    (R, 72, 'moves', None),
    (U, 8, 'moves', None),
    (R, 44, 'moves', None),
    (U, 11, 'moves', None),
    (R, 16, 5, None),                               # east opening: Crossroads
    (R, 266, 'moves', None),                        # across the Crossroads
    (R, 20, 6, None),                               # east opening: Long Gallery
    (R, 256, 'moves', None),                        # along the corridor to the east
    (U, 4, 'moves', None),
    (R, 20, 'moves', 'step03-long-gallery.png'),    # door B: shut
    (L, 22, 'moves', None),                         # under the north opening
    (U, 54, 'moves', None),
    (U, 20, 2, None),                               # north opening: Old Well
    (U, 2, 'moves', None),                          # above the south steps
    (D, 24, 6, None),                               # south opening: Long Gallery
    (D, 48, 'moves', None),                         # to the west opening
    (L, 244, 'moves', None),
    (L, 24, 5, None),                               # west opening: Crossroads
    (L, 134, 'moves', None),                        # to the south steps
    (D, 70, 'moves', None),
    (D, 12, 9, None),                               # south opening: Sunken Hall
    (D, 13, 'moves', None),                         # to the east door
    (R, 122, 'moves', None),
    (D, 57, 'moves', None),
    (R, 20, 'moves', None),                         # door C: shut
    (L, 16, 'moves', None),                         # under the north opening
    (U, 47, 'moves', None),
    (L, 122, 'moves', None),
    (U, 23, 'moves', None),
    (U, 24, 5, None),                               # north opening: Crossroads
    (U, 108, 'moves', None),                        # under the north opening
    (U, 24, 1, None),                               # north opening: Moss Gate
    (0, 16, 'blocked', None),                       # rest
]

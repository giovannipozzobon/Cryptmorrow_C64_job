# Route of step 05, planned by tools/plan_route.py --step 5
# tools/route_variant_05b.py: do not edit, plan again.
from hero_model import (JOY_UP as U, JOY_DOWN as D, JOY_LEFT as L,
                        JOY_RIGHT as R, JOY_FIRE as F)  # noqa: F401

SCRIPT = [
    (0, 16, 'blocked', None),                       # the start
    (D, 39, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (D, 48, 'moves', None),                         # to the west opening
    (L, 128, 'moves', None),
    (D, 10, 'moves', None),
    (L, 24, 4, None),                               # west opening: Root Cellar
    (L, 16, 'moves', None),                         # 66 pixels east of the bat
    (D, 19, 'moves', None),
    (L, 60, 'moves', None),
    (U, 7, 'moves', None),
    (0, 60, 'blocked', 'v05b-lazy-bat.png'),        # the bat sleeps
    (L, 20, 'moves', None),                         # closer: 50 pixels
    (L, 3, 'fight', None),                          # the bat wakes: one blow
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (0, 16, 'blocked', None),                       # the game goes on
]

# Route of step 06, planned by tools/plan_route.py --step 6
# tools/route_variant_06a.py: do not edit, plan again.
from hero_model import (JOY_UP as U, JOY_DOWN as D, JOY_LEFT as L,
                        JOY_RIGHT as R, JOY_FIRE as F)  # noqa: F401

SCRIPT = [
    (0, 16, 'blocked', None),                       # the start: no theme
    (D, 39, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (D, 16, 'moves', None),                         # onto the skeleton's row
    (R, 52, 'moves', None),
    (D, 70, 'moves', None),
    (L, 85, 'fight', None),                         # the skeleton: blade, hits and dust
    (U, 1, 'fight', None),
    (0, 3, 'fight', None),
    (L, 1, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 20, 'fight', None),
    (F, 1, 'fight', None),
    (0, 8, 'fight', None),
    (0, 16, 'blocked', None),                       # the game goes on
]

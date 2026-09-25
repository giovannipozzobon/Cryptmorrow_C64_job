# Route of step 02, planned by tools/plan_route.py --step 2
# tools/route_variant_02a.py: do not edit, plan again.
from hero_model import (JOY_UP as U, JOY_DOWN as D, JOY_LEFT as L,
                        JOY_RIGHT as R, JOY_FIRE as F)  # noqa: F401

SCRIPT = [
    (0, 16, 'blocked', None),                       # the explorer at the start
    (R, 10, 'moves', None),                         # ten frames east: twenty pixels
    (L, 60, 'moves', None),                         # west, two pixels a frame, until the pillar
    (U, 60, 'moves', None),                         # north until the wall
    (R, 100, 'moves', None),                        # east along the wall
    (D, 100, 'moves', None),                        # south until the wall
    (L, 100, 'moves', None),                        # west
    (0, 16, 'blocked', 'v02a-faster-explorer.png'), # rest
]

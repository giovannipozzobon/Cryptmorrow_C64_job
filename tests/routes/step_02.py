# Route of step 02, planned by tools/plan_route.py --step 2
# tools/route_step_02.py: do not edit, plan again.
from hero_model import (JOY_UP as U, JOY_DOWN as D, JOY_LEFT as L,
                        JOY_RIGHT as R, JOY_FIRE as F)  # noqa: F401

SCRIPT = [
    (0, 16, 'blocked', 'step02-explorer.png'),      # the explorer at the start, facing down
    (L, 120, 'moves', None),                        # west until the pillar stops the explorer
    (U, 120, 'moves', None),                        # north until the wall stops the explorer
    (R, 40, 'moves', None),                         # east along the wall
    (D, 8, 'moves', None),                          # north to the gate
    (R, 50, 'moves', None),
    (U, 8, 'blocked', None),                        # the portal: a door, it stops the explorer
    (D | R, 24, 'moves', None),                     # diagonal: horizontal wins
    (U | D, 8, 'moves', None),                      # both vertical bits: up wins
    (R, 200, 'moves', None),                        # east until the wall stops the explorer
    (D, 200, 'moves', None),                        # south until the wall stops the explorer
    (L, 122, 'moves', None),                        # to the south opening
    (D, 81, 'moves', None),
    (D, 40, 'moves', 'step02-south-opening.png'),   # south: the opening ends at the edge of the map
    (D, 8, 'blocked', None),                        # nothing below it
    (U, 54, 'moves', None),                         # back to the middle
    (0, 16, 'blocked', None),                       # rest
]

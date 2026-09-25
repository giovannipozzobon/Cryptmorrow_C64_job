# Route of step 05, planned by tools/plan_route.py --step 5
# tools/route_variant_05a.py: do not edit, plan again.
from hero_model import (JOY_UP as U, JOY_DOWN as D, JOY_LEFT as L,
                        JOY_RIGHT as R, JOY_FIRE as F)  # noqa: F401

SCRIPT = [
    (0, 16, 'blocked', None),                       # the start
    (D, 39, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (D, 86, 'moves', None),                         # into the skeleton's way: a first touch, seven cells
    (R, 52, 'moves', None),
    (0, 204, 'blocked', None),                      # six cells left
    (0, 45, 'blocked', None),                       # five
    (0, 253, 'blocked', None),                      # four
    (0, 45, 'blocked', None),                       # three
    (0, 253, 'blocked', None),                      # two
    (0, 45, 'blocked', None),                       # one
    (0, 253, 'ending', None),                       # the eighth touch: GAME OVER
    (0, 16, 'still', 'v05a-game-over.png'),         # the game stands still
    ('restart', -1, 'start', None),                 # a new game that goes on
    (0, 16, 'blocked', None),                       # rest
]

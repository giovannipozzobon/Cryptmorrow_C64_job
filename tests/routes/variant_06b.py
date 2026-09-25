# Route of step 06, planned by tools/plan_route.py --step 6
# tools/route_variant_06b.py: do not edit, plan again.
from hero_model import (JOY_UP as U, JOY_DOWN as D, JOY_LEFT as L,
                        JOY_RIGHT as R, JOY_FIRE as F)  # noqa: F401

SCRIPT = [
    (0, 600, 'blocked', None),                      # the theme, faster
    (D, 39, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (D, 80, 'moves', None),                         # onto the skeleton's way
    (0, 61, 'blocked', None),                       # six cells
    (0, 149, 'blocked', None),                      # four
    (0, 149, 'blocked', None),                      # two
    (0, 149, 'ending', None),                       # GAME OVER, its piece
    (0, 200, 'still', None),                        # the piece is over: every note released
    ('restart', -1, 'start', None),                 # a new game that goes on
    (0, 16, 'blocked', None),                       # rest
]

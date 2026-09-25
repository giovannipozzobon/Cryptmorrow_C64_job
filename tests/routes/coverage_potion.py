# Targeted route for tools/exec_coverage.py, step 04:
# the start of tests/routes/step_04.py to the Root Cellar, then the
# test sets the energy to 7 cells and the explorer takes the potion:
# 7 + 2 is more than ENERGY_MAX, so use_object stops it at 8.
from hero_model import (JOY_UP as U, JOY_DOWN as D, JOY_LEFT as L,
                        JOY_RIGHT as R, JOY_FIRE as F)  # noqa: F401

SCRIPT = [
    (0, 16, 'blocked', None),                       # the start: HUD, the Moss Gate
    (U, 60, 'moves', None),                         # north to the gate
    (U, 8, 'blocked', None),                        # the portal: shut without the three seals
    (D, 99, 'moves', None),                         # to the south steps
    (D, 12, 5, None),                               # south opening: Crossroads
    (D, 58, 'moves', None),                         # to the west opening
    (L, 128, 'moves', None),
    (L, 24, 4, None),                               # west opening: Root Cellar
    ('energy', 7, 'set', None),                     # seven cells
    (L, 29, 'moves', None),                         # towards the potion
    (U, 39, 'moves', None),                         # onto it: 8 cells, not 9
    (0, 16, 'blocked', None),
]

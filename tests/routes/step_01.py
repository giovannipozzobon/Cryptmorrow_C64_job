# Route of step 01, planned by tools/plan_route.py --step 1
# tools/route_step_01.py: do not edit, plan again.
from hero_model import (JOY_UP as U, JOY_DOWN as D, JOY_LEFT as L,
                        JOY_RIGHT as R, JOY_FIRE as F)  # noqa: F401

SCRIPT = [
    (0, 64, 'still', 'step01-first-room.png'),      # the room: the torches burn
    (0, 448, 'still', None),                        # and burn on: the rest of the bitmap never changes
]

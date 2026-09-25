# Route of step 02 (the explorer), for tools/plan_route.py --step 2.
# The explorer in the Moss Gate: the four directions and both walking
# frames of each, walls, pillars and the portal (a door) that stop the explorer,
# horizontal over vertical and up over down, and the south opening,
# which does not lead anywhere yet: the map simply ends.
run(0, 16, "the explorer at the start, facing down", "step02-explorer.png")
run(L, 120, "west until the pillar stops the explorer")
run(U, 120, "north until the wall stops the explorer")
run(R, 40, "east along the wall")
goto(148, 51, "north to the gate")
run(U, 8, "the portal: a door, it stops the explorer")
run(D | R, 24, "diagonal: horizontal wins")
run(U | D, 8, "both vertical bits: up wins")
run(R, 200, "east until the wall stops the explorer")
run(D, 200, "south until the wall stops the explorer")
goto(148, 150, "to the south opening")
run(D, 40, "south: the opening ends at the edge of the map",
    "step02-south-opening.png")
run(D, 8, "nothing below it")
goto(148, 111, "back to the middle")
run(0, 16, "rest")

# Route of step 01 (the first room), for tools/plan_route.py --step 1.
# No explorer and no joystick yet: the program draws the Moss Gate and
# the main loop animates its torches. The test watches 512 frames, the
# flames every 8 and the rest of the bitmap every 64, and takes the
# picture of the step.
run(0, 64, "the room: the torches burn", "step01-first-room.png")
run(0, 448, "and burn on: the rest of the bitmap never changes")

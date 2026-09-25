# Route of variant 02a (a faster explorer, HERO_SPEED = 2), for
# tools/plan_route.py --step 2 --root variants/02-explorer/02a-...
# --set "hero_model.HERO_SPEED = 2". Only run(): goto counts pixels.
run(0, 16, "the explorer at the start")
run(R, 10, "ten frames east: twenty pixels")
run(L, 60, "west, two pixels a frame, until the pillar")
run(U, 60, "north until the wall")
run(R, 100, "east along the wall")
run(D, 100, "south until the wall")
run(L, 100, "west")
run(0, 16, "rest", "v02a-faster-explorer.png")

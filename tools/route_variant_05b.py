# Route of variant 05b (lazy bats, CHASE_X = 60, CHASE_Y = 45), for
# tools/plan_route.py --step 5 ... --set "combat_model.CHASE_X = 60"
# --set "combat_model.CHASE_Y = 45". In the Root Cellar the bat
# (140, 100) sleeps with the explorer 66 pixels away, which would wake
# it with the values of the game; closer, it wakes and is fought.
run(0, 16, "the start")
goto(148, 150, "to the south steps")
run(D, 12, "south opening: Crossroads")
goto(20, 88, "to the west opening")
run(L, 24, "west opening: Root Cellar")
goto(206, 100, "66 pixels east of the bat")
run(0, 60, "the bat sleeps", "v05b-lazy-bat.png")
run(L, 20, "closer: 50 pixels")
fight(0, L, "the bat wakes: one blow")
run(0, 16, "the game goes on")

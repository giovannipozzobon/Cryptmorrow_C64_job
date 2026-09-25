# Route of variant 06a (START_MODE = MODE_FX), for tools/plan_route.py
# --step 6 --root variants/06-sound/06a-...: a game with the effects
# from the start: the Crossroads skeleton fought (blade, hit, dust).
run(0, 16, "the start: no theme")
goto(148, 150, "to the south steps")
run(D, 12, "south opening: Crossroads")
goto(200, 116, "onto the skeleton's row")
fight(0, L, "the skeleton: blade, hits and dust")
run(0, 16, "the game goes on")

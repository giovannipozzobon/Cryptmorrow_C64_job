# Route of variant 06b (faster music, SPEED = 5 in score.py), for
# tools/plan_route.py --step 6 --root variants/06-sound/06b-...: the
# theme for 600 frames, a game lost in the Crossroads skeleton's way,
# the piece of GAME OVER to its end and silence; a new game goes on.
run(0, 600, "the theme, faster")
goto(148, 150, "to the south steps")
run(D, 12, "south opening: Crossroads")
goto(148, 110, "onto the skeleton's way", safe=False)
wait_for("hurt by enemy 0", "six cells")
wait_for("hurt by enemy 0", "four")
wait_for("hurt by enemy 0", "two")
wait_for("GAME OVER", "GAME OVER, its piece")
run(0, 200, "the piece is over: every note released")
restart(note="a new game that goes on")
run(0, 16, "rest")

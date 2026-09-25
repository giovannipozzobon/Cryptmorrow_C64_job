# Route of variant 05a (gentler damage, DAMAGE = 1), for
# tools/plan_route.py --step 5 ... --set "combat_model.DAMAGE = 1".
# The explorer waits in the Crossroads skeleton's way: one cell a
# touch, eight touches, GAME OVER; then a new game goes on.
run(0, 16, "the start")
goto(148, 150, "to the south steps")
run(D, 12, "south opening: Crossroads")
goto(200, 116, "into the skeleton's way: a first touch, seven cells",
     safe=False)
wait_for("hurt by enemy 0", "six cells left")
wait_for("hurt by enemy 0", "five")
wait_for("hurt by enemy 0", "four")
wait_for("hurt by enemy 0", "three")
wait_for("hurt by enemy 0", "two")
wait_for("hurt by enemy 0", "one")
wait_for("GAME OVER", "the eighth touch: GAME OVER")
run(0, 16, "the game stands still", "v05a-game-over.png")
restart(note="a new game that goes on")
run(0, 16, "rest")

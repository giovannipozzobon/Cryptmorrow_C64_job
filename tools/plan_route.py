"""Plan the test route offline: turn the goals of a route file into the
explicit joystick segments of SCRIPT in tests/verify_game.py.

Usage: python tools/plan_route.py [--step N] [--root DIR]
           [--set STATEMENT ...] tools/route_1.0.1.py > script.txt

The planner plays the game with the same Python models as the test
(tests/game_model.py) on the assembled program's labels and HUD data, so
it needs game/build/cryptmorrow.prg and .lbl. The route file is Python
that calls the goals below:

  run(joy, frames, note, shot, expect)  hold the stick for some frames
  goto(x, y, note)        shortest walk (turns cost extra) to a position
  pick(column, row, note) walk onto the object of that metatile
  fight(n, face, note)    wait for enemy n, turning towards it, and press
                          Fire only when a trial copy of the game shows
                          that the blow will hit it
  wait_for(event, note, joy=0)  hold joy until an event of world_model
  wait_until(test, note, joy=0)  hold joy until test() is true, e.g.
                          lambda: game.state == "end"
  set_energy(n, note)     the test writes n into energy
  set_seals(n, note)      the test writes n into seals
  place_enemy(n, x, y, note)  the test moves enemy n
  slow_enemy(n, note)     the test clears enemy n's fast flag (1.0.1:
                          every skeleton of the game is fast)
  align(note)             the test waits until frame_count mod 32 is the
                          planner's, so enemies move as planned and the
                          torches show the same flame

The program starts on the title: run() segments there move
the menu's cursor or press Fire. A segment's expectation names the
change of state it makes: 'start' (title to game), 'ending' (the game
ends), 'end' (the end screen), 'back' (to the title); 'title' and
'still' when the state does not change outside the game.

With --step N the planner plays step N of the chain of the book
(chain/NN-name/game/build, tests/step_model.py for steps 01-06, whose
route tests/verify_step.py replays). Before step 07 a game begins at
once and stands still after its end; two more goals:

  restart(mode, note)     the test starts the program again from
                          `entry` (a new game, frame_count 0); in step
                          06 `mode` is the audio mode the test puts in
                          audio_mode as if START_MODE said so (None:
                          the mode assembled)
  (the end of a game)     a segment in which it comes expects 'ending',
                          one after it 'still'

SCRIPT goes to standard output, a log of every noted segment to
standard error. The test never searches or aims: it replays SCRIPT.
"""
import heapq
from pathlib import Path
import pickle
import sys

PROJECT = Path(__file__).resolve().parents[1]


def shown(path):
    """A path as the project names it: relative to its root if inside."""
    try:
        return Path(path).resolve().relative_to(PROJECT).as_posix()
    except ValueError:
        return Path(path).as_posix()


sys.path.insert(0, str(PROJECT / "tests"))

import combat_model as C                        # noqa: E402
import hero_model as H                          # noqa: E402
import world_model as W                         # noqa: E402
from game_model import Game                     # noqa: E402
import game_model                               # noqa: E402
import reference                                # noqa: E402
import step_model                               # noqa: E402
from vicemon import load_labels                 # noqa: E402

U, D, L, R, F = H.JOY_UP, H.JOY_DOWN, H.JOY_LEFT, H.JOY_RIGHT, H.JOY_FIRE
NAMES = {U: "U", D: "D", L: "L", R: "R", F: "F"}
STEPS = {U: (0, -1), D: (0, 1), L: (-1, 0), R: (1, 0)}
FACING = {U: H.DIR_UP, D: H.DIR_DOWN, L: H.DIR_LEFT, R: H.DIR_RIGHT}
TURN_COST = 12                          # pixels a turn is worth in goto
ALIGN = 32              # frame phase: enemies 16, torch flames 32


def step_root(step):
    """The folder of step `step` of the chain, or the project (or the
    folder given with --root: a variant)."""
    if ROOT is not None:
        return ROOT
    if step is None:
        return PROJECT
    found = sorted((PROJECT / "chain").glob(f"{step:02d}-*"))
    if len(found) != 1:
        raise SystemExit(f"step {step} not found in chain/")
    return found[0]


def load_game(step=None, mode=None):
    root = step_root(step)
    labels = load_labels(root / "game/build/cryptmorrow.lbl")
    prg = (root / "game/build/cryptmorrow.prg").read_bytes()
    memory = bytearray(65536)
    base = prg[0] | prg[1] << 8
    memory[base:base + len(prg) - 2] = prg[2:]

    def data(name, size):
        if name not in labels:
            return None                 # not in this step yet
        return bytes(memory[labels[name]:labels[name] + size])
    hud = data("hud_frame", 256)
    texts = [data(name, 32) for name in ("over_text", "won_text")]
    start = (labels.get("HERO_START_X"), labels.get("HERO_START_Y"))
    if step is not None and step < step_model.FIRST_TITLE:
        if mode is None:
            mode = labels.get("START_MODE", 0)
        return step_model.StepGame(step, hud, labels["START_ROOM"], texts,
                                   *start, mode=mode)
    return Game(hud, labels["START_ROOM"], texts, *start)


STEP, ROOT = None, None
while len(sys.argv) > 2 and sys.argv[1].startswith("--"):
    option, value = sys.argv[1], sys.argv[2]
    del sys.argv[1:3]
    if option == "--step":
        STEP = int(value)
    elif option == "--root":
        ROOT = Path(value).resolve()
    elif option == "--set":             # a variant changes the model
        exec(value, {"hero_model": H, "world_model": W,
                     "combat_model": C, "game_model": game_model,
                     "step_model": step_model})
    else:
        raise SystemExit(f"unknown option {option}")
reference.GENERATED = step_root(STEP) / "game/assets/generated"
game = load_game(STEP)
script = []         # (joy, count, expectation, shot, note, log)


CHANGES = {"play": "start", "ending": "ending", "end": "end",
           "title": "back"}


def state():
    hero = game.hero
    return (game.state, game.world.slot, hero and hero.x, hero and hero.y,
            game.world.energy)


def stepped():
    """Is the game a step before 07 (no title, no end screen)?"""
    return isinstance(game, step_model.StepGame)


def playing():
    """In a game that goes on (in the steps: not ended, an explorer)."""
    if stepped():
        return not game.world.ended and game.hero is not None
    return game.state == "play"


def restart(mode=None, note=None):
    """Steps 01-06: the program started again from entry."""
    global game
    if not stepped():
        raise SystemExit("restart() is for steps 01-06")
    game = load_game(STEP, mode)
    emit("restart", -1 if mode is None else mode, "start", note=note)


def emit(joy, count, expectation, shot=None, note=None, log=None):
    """A segment of SCRIPT; one without a note or capture continues the
    last one if it holds the same stick with the same expectation."""
    if script and note is None and shot is None and \
            expectation in ("moves", "blocked"):
        last = script[-1]
        if last[0] == joy and last[2] == expectation and last[3] is None:
            script[-1] = (joy, last[1] + count) + last[2:]
            return
    script.append((joy, count, expectation, shot, note, log))


def expectation(changes, rooms, steps, in_game):
    """What the test must see: a change of state, a change of room,
    a walk or none."""
    if changes:
        return CHANGES[changes[0]] if len(changes) == 1 else "?"
    if rooms:
        return rooms[0] if len(rooms) == 1 else "?"
    if not in_game or (stepped() and game.world.ended):
        return "title" if game.state == "title" else "still"
    return "moves" if steps else "blocked"


def segment(joy, count, stop=None):
    """Steps the game; returns changes of state, rooms, steps."""
    hero, steps_before = game.hero, game.hero and game.hero.steps
    changes, rooms, frames = [], [], 0
    while frames < count if stop is None else not stop():
        before, ended = game.state, game.world.ended
        result = game.step(joy)
        frames += 1
        if game.state != before:
            changes.append(game.state)
        elif stepped() and game.world.ended != ended:
            changes.append("ending")        # the game stops here
        elif result["room"] is not None:
            rooms.append(result["room"])
        if stop is not None and frames > 2000:
            raise SystemExit("the event did not come in 2000 frames")
    steps = game.hero.steps - steps_before \
        if hero is not None and game.hero is hero else 0
    return changes, rooms, steps, frames


def run(joy, count, note=None, shot=None, expect=None):
    start, events_before = state(), len(game.world.events)
    in_game = playing()
    changes, rooms, steps, _ = segment(joy, count)
    if expect is None:
        expect = expectation(changes, rooms, steps, in_game)
    emit(joy, count, expect, shot, note,
         (start, state(), game.world.events[events_before:]))
    if shot:
        game.step(0)        # the capture lets the C64 run a frame
        alive = [e.state() for e in game.combat.enemies if e.kind]
        print(f"# shot {shot}: enemies {alive}", file=sys.stderr)


def wait_for(event, note, limit=2000, shot=None, joy=0):
    start, events_before = state(), len(game.world.events)
    in_game = playing()
    changes, rooms, steps, count = segment(
        joy, None, lambda: event in game.world.events[events_before:])
    emit(joy, count, expectation(changes, rooms, steps, in_game), shot,
         note, (start, state(), game.world.events[events_before:]))


def wait_until(test, note, shot=None, joy=0):
    """Hold joy until test() is true: a state, PRESS FIRE shown."""
    start, events_before = state(), len(game.world.events)
    in_game = playing()
    changes, rooms, steps, count = segment(joy, None, test)
    emit(joy, count, expectation(changes, rooms, steps, in_game), shot,
         note, (start, state(), game.world.events[events_before:]))


def set_energy(value, note):
    game.world.energy = value
    emit("energy", value, "set", note=note)


def set_seals(value, note):
    game.world.seals = value
    emit("seals", value, "set", note=note)


def place_enemy(n, x, y, note):
    enemy = game.combat.enemies[n]
    enemy.x, enemy.y = x, y
    emit("enemy", n, (x, y), note=note)


def slow_enemy(n, note):
    game.combat.enemies[n].fast = 0
    emit("slow", n, "set", note=note)


def align(note=None):
    emit("align", game.frame % ALIGN, "idle", note=note)


def blocked_at(x, y, joy):
    probe = H.HeroModel(game.hero.solid, x, y)
    probe.dir = FACING[joy]
    return probe.blocked()


def path(tx, ty):
    """Dijkstra over (x, y, facing); returns [[joy, frames], ...]."""
    first = (game.hero.x, game.hero.y, 0)
    exits = not stepped() or game.has(step_model.FIRST_EXITS)
    done, before = {}, {}
    heap = [(0, game.hero.x, game.hero.y, 0, None)]
    while heap:
        cost, x, y, facing, came = heapq.heappop(heap)
        if (x, y, facing) in done:
            continue
        done[(x, y, facing)] = cost
        before[(x, y, facing)] = came
        if (x, y) == (tx, ty):
            end = (x, y, facing)
            break
        for joy, (dx, dy) in STEPS.items():
            if blocked_at(x, y, joy):
                continue
            nx, ny = x + dx, y + dy
            if exits and not (W.WEST_EDGE < nx < W.EAST_EDGE and
                              W.NORTH_EDGE < ny < W.SOUTH_EDGE):
                continue
            extra = TURN_COST if facing and joy != facing else 0
            if (nx, ny, joy) not in done:
                heapq.heappush(heap, (cost + 1 + extra, nx, ny, joy,
                                      (x, y, facing)))
    else:
        raise SystemExit(f"no path to {tx},{ty} from {first[:2]} in room "
                         f"{game.world.slot}")
    moves, node = [], end
    while before[node] is not None:
        moves.append(node[2])
        node = before[node]
    segments = []
    for joy in reversed(moves):
        if segments and segments[-1][0] == joy:
            segments[-1][1] += 1
        else:
            segments.append([joy, 1])
    return segments


def threat(moves, frames=40):
    """The enemy that would hurt the explorer if it walked `moves`,
    then stood, for `frames` frames; None if nobody would."""
    trial, count = clone(game), 0
    for joy, k in moves + [[0, frames]]:
        for _ in range(k):
            if count >= frames or trial.state != "play":
                return None
            trial.step(joy)
            count += 1
            for event in trial.world.events:
                if event.startswith("hurt by enemy"):
                    return int(event.split()[-1])
    return None


def goto(tx, ty, note=None, safe=True):
    """Shortest walk to (tx, ty). Since 1.0.1, with safe=True, before
    every stretch of up to 8 frames a trial copy walks on for 40: if
    an enemy would hurt the explorer, it fights that enemy first (fight)."""
    fights = 0
    if stepped() and not game.has(step_model.FIRST_COMBAT):
        safe = False                    # no enemies before step 05
    while (game.hero.x, game.hero.y) != (tx, ty) and game.state == "play":
        moves = path(tx, ty)
        if safe and fights < 6:
            n = threat(moves)
            if n is not None:
                fight(n, None, note or "an enemy in the way")
                note, fights = None, fights + 1
                continue
        joy, count = moves[0]
        run(joy, min(count, 8) if safe else count, note)
        note = None
    if (game.hero.x, game.hero.y) != (tx, ty):
        print(f"# WARNING goto {tx},{ty} ended at "
              f"{game.hero.x},{game.hero.y}", file=sys.stderr)


def pick(column, row, note):
    goto(column * 16 + 8 - W.HIT_X, 24 + row * 16 + 8 - W.HIT_Y, note)


def alive(n):
    enemy = game.combat.enemies[n]
    return enemy.kind and not enemy.dust


def clone(state):
    """A trial copy of the game (without its long list of events)."""
    events = state.world.events
    state.world.events = []
    try:
        return pickle.loads(pickle.dumps(state, -1))
    finally:
        state.world.events = events


def over(state, n):
    enemy = state.combat.enemies[n]
    return not enemy.kind or enemy.dust or state.state != "play"


def blow_hits(state, n):
    """Fire pressed now hits enemy n while the blade is out."""
    combat = state.combat
    if combat.slash or combat.fire_held:
        return False
    enemy, hero = combat.enemies[n], state.hero
    if abs(enemy.x - hero.x) > 48 or abs(enemy.y - hero.y) > 48:
        return False
    trial = clone(state)
    for k in range(C.BLADE_FRAMES):
        trial.step(F if k == 0 else 0)
        if trial.combat.enemies[n].hit or over(trial, n):
            return True
    return False


def policy(state, n, face=None):
    """What the fighter does between decisions: strike when a blow
    will hit, let Fire go after a blow, turn towards the enemy."""
    combat, hero = state.combat, state.hero
    if combat.blade_out() or combat.fire_held:
        return 0
    if blow_hits(state, n):
        return F
    enemy = combat.enemies[n]
    dx, dy = enemy.x - hero.x, enemy.y - hero.y
    if face is not None:
        want = face
    elif abs(dx) >= abs(dy):
        want = R if dx > 0 else L
    else:
        want = D if dy > 0 else U
    if FACING[want] != hero.dir and not combat.slash:
        return want
    return 0


def rollout(state, n, first, horizon):
    """Plays `first`, then the policy; returns (value, frames)."""
    trial = clone(state)
    energy, hp = trial.world.energy, trial.combat.enemies[n].hp
    room, frames = trial.world.slot, 0
    for joy in first:
        trial.step(joy)
        frames += 1
        if over(trial, n) or trial.world.slot != room:
            break
    while frames < horizon and not over(trial, n) and \
            trial.world.slot == room:
        trial.step(policy(trial, n))
        frames += 1
    if trial.world.slot != room or (trial.state != "play" and
                                    trial.world.ended == "lost"):
        return -10 ** 9, frames
    value = (trial.world.energy - energy) * 10000
    enemy, hero = trial.combat.enemies[n], trial.hero
    if not enemy.kind or enemy.dust:
        return value + 5000 - frames * 10, frames
    distance = abs(enemy.x - hero.x) + abs(enemy.y - hero.y)
    return value + (hp - enemy.hp) * 1000 - distance, frames


CANDIDATES = [[joy] * k for joy in (0, U, D, L, R) for k in (1, 4, 10, 20)]


def fight(n, face, note, max_frames=900, horizon=60):
    """Defeat enemy n, losing as little energy as possible (1.0.1):
    before every frame the fighter tries twenty short moves - stand,
    or walk up, down, left or right for 1, 4, 10 or 20 frames - each
    followed by the policy (strike when a trial copy shows the blow
    will hit, turn towards the enemy) for `horizon` frames, and takes
    the first frame of the best: least energy lost, then the enemy
    defeated soonest, then more blows landed, then closer. `face`:
    the direction to turn to first, as before 1.0.1."""
    frames, energy = [], game.world.energy
    while not over(game, n) and len(frames) < max_frames:
        if game.combat.blade_out() or game.combat.fire_held:
            joy = 0
        elif blow_hits(game, n):
            joy = F
        elif face is not None and FACING[face] != game.hero.dir:
            joy = face
        else:
            best = max(CANDIDATES, key=lambda moves: rollout(
                game, n, moves, horizon)[0])
            joy = best[0]
        face = None
        game.step(joy)
        frames.append(joy)
    while game.state == "play" and game.combat.blade_out():
        game.step(0)
        frames.append(0)
    segments = []
    for joy in frames:
        if segments and segments[-1][0] == joy:
            segments[-1][1] += 1
        else:
            segments.append([joy, 1])
    for k, (joy, count) in enumerate(segments):
        emit(joy, count, "fight", note=note if k == 0 else None)
    print(f"# fight {n} in room {game.world.slot} ({note}): energy "
          f"{energy} -> {game.world.energy}, {len(frames)} frames",
          file=sys.stderr)
    if not over(game, n) or game.state != "play":
        print(f"# WARNING enemy {n} still alive after the fight in room "
              f"{game.world.slot}", file=sys.stderr)


def joystick(joy):
    if isinstance(joy, str):
        return repr(joy)
    if joy == 0:
        return "0"
    return " | ".join(NAMES[bit] for bit in (U, D, L, R, F) if joy & bit)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    try:
        exec(Path(sys.argv[1]).read_text(encoding="utf-8"), globals())
    except SystemExit as stop:
        for joy, count, expectation, shot, note, log in script:
            if note and log:
                print(f"#   {note}: {log[0]} -> {log[1]} {log[2]}",
                      file=sys.stderr)
        print(f"# STOPPED: {stop}", file=sys.stderr)
        return 1
    frames = sum(s[1] for s in script if isinstance(s[0], int))
    world = game.world
    where = f"{game.hero.x},{game.hero.y}" if game.hero else "-"
    print(f"# {len(script)} segments, {frames} frames, final room "
          f"{world.slot} at {where}, HUD "
          f"{world.hud_values()}", file=sys.stderr)
    for joy, count, expectation, shot, note, log in script:
        if note and log:
            print(f"#   {note}: {log[0]} -> {log[1]} {log[2]}",
                  file=sys.stderr)
    if STEP is not None:                # a module for verify_step.py
        print(f"# Route of step {STEP:02d}, planned by tools/plan_route.py "
              f"--step {STEP}\n# {shown(sys.argv[1])}: do not "
              f"edit, plan again.\nfrom hero_model import (JOY_UP as U, "
              f"JOY_DOWN as D, JOY_LEFT as L,\n                        "
              f"JOY_RIGHT as R, JOY_FIRE as F)  # noqa: F401\n\n"
              f"SCRIPT = [")
    for joy, count, expectation, shot, note, log in script:
        line = f"    ({joystick(joy)}, {count}, {expectation!r}, {shot!r}),"
        if note:
            comment = "# " + note
            line = (f"{line:<52}{comment}" if len(line) < 52
                    else f"    {comment}\n{line}")
        print(line)
    if STEP is not None:
        print("]")
    return 0


if __name__ == "__main__":
    sys.exit(main())

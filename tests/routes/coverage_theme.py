# Targeted route for tools/exec_coverage.py, complete game:
# the title with MUSIC, left alone for longer than the theme (32 bars
# of 16 steps, 6 frames a step: 3072 frames), so that the order lists
# reach ORDER_LOOP and the theme starts again.
SCRIPT = [
    ('align', 0, 'idle', None),
    (0, 3300, 'title', None),       # the theme, then its loop
]

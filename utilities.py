class Row_track:
    def __init__(self):
        self.row = 0

    def same(self):
        return self.row

    def increase(self):
        self.row += 1
        return self.row

    def reset(self):
        self.row = 0
        return self.row


class RelativePositionTracker:
    def __init__(self):
        self.x = 5
        self.y = 10
        self.constant_y = 20

    def same(self, what: str):
        if what == "x":
            return self.x
        elif what == "y":
            return self.y

    def increase(self, what: str, how_much: int):
        if what == "x":
            self.x += how_much
            return self.x
        elif what == "y":
            self.y += how_much
            return self.y

    def reset(self, what: str):
        # Restores to factory value
        if what == "x":
            self.x = 5
            return self.x
        elif what == "y":
            self.y = 10
            return self.y

    def checkpoint_set(self, what, to_what):
        # Stores temporary memory for temporary resetting or loops purposes
        if what == "x":
            self.memory_x = to_what
            return self.memory_x
        elif what == "y":
            self.memory_y = to_what
            return self.memory_y

    def checkpoint_get(self, what):
        if what == "x":
            return self.memory_x
        elif what == "y":
            return self.memory_y

    def set(self, what: str, to_what: int):
        if what == "x":
            self.x = to_what
            return self.x
        elif what == "y":
            self.y = to_what
            return self.y

# Dice helpers moved to engine.dice (roll_die / max_die) — the single source of
# truth, which is seedable for deterministic tests.

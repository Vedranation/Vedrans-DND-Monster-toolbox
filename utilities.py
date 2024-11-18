import random

class Row_track():
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

class RelativePositionTracker():
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
        if what == "x":
            self.x = 5
            return self.x
        elif what == "y":
            self.y = 10
            return self.y

    def set(self, what: str, to_what: int):
        if what == "x":
            self.x = to_what
            return self.x
        elif what == "y":
            self.y = to_what
            return self.y

def RollDice(die_type: str) -> int:
    if die_type == "d4":
        die_max = 4
    elif die_type == "d6":
        die_max = 6
    elif die_type == "d8":
        die_max = 8
    elif die_type == "d10":
        die_max = 10
    elif die_type == "d12":
        die_max = 12
    elif die_type == "d20":
        die_max = 20
    elif die_type == "d100":
        die_max = 100
    return random.randint(1, die_max)
def ReturnMaxPossibleDie(die_type: str) -> int:
    if die_type == "d4":
        die_max = 4
    elif die_type == "d6":
        die_max = 6
    elif die_type == "d8":
        die_max = 8
    elif die_type == "d10":
        die_max = 10
    elif die_type == "d12":
        die_max = 12
    elif die_type == "d20":
        die_max = 20
    elif die_type == "d100":
        die_max = 100
    return die_max

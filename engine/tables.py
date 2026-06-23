"""Random tables (game content). Pure data — no UI."""

from __future__ import annotations

FUMBLE_TABLE = [
    "Get distracted: Disadvantage on next attack",
    "Overextended Swing: Next attack on you have advantage",
    "Hit yourself for half dmg",
    "Hit ally for half dmg",
    "String Snap: If using a bow or crossbow",
    "Fall prone",
    "Ranged attack/spell: Goes in completely random direction and hits something",
    "Drop your weapon",
    "Misjudged Distance: enemy within 5ft can attempt a free grapple check",
    "Twisted Ankle: half move speed next turn",
    "Overexertion: Lose bonus action this turn",
    "Self doubt: Lose reaction this turn",
    "Ice spells: Your feet freeze, is rooted until next turn",
    "Fire spells: Lit yourself on fire, 2 turns take 1d6 dmg or action to put it out",
    "Ranged weapons: Drop 10 pieces of ammunition, it scatters and needs action to collect",
    "A random glass item/potion breaks and spills",
    "Coin pouch rips, you lose 5d8 GP",
    "If spell: Roll wild magic table",
    "Loud noise: You cause a very loud noise",
    "Panic: Become frightened of whatever you just attacked",
    "Sand/Mud in eyes: Become blinded until your next turn",
    "Drop formation: Lose 2 AC until next turn",
    "Instinct movement: You provoke instincts in enemy, they move 10ft immediately",
    "Nothing happens, lucky day",
    "You got distracted by a coin on the ground! Add 1GP to your inventory",
]

# Full-caster spell-slot progression (D&D 5e). caster level → list where index i
# (0-based) is the number of slots at spell level i+1.
SPELL_SLOTS_BY_LEVEL = {
    1:  [2],
    2:  [3],
    3:  [4, 2],
    4:  [4, 3],
    5:  [4, 3, 2],
    6:  [4, 3, 3],
    7:  [4, 3, 3, 1],
    8:  [4, 3, 3, 2],
    9:  [4, 3, 3, 3, 1],
    10: [4, 3, 3, 3, 2],
    11: [4, 3, 3, 3, 2, 1],
    12: [4, 3, 3, 3, 2, 1],
    13: [4, 3, 3, 3, 2, 1, 1],
    14: [4, 3, 3, 3, 2, 1, 1],
    15: [4, 3, 3, 3, 2, 1, 1, 1],
    16: [4, 3, 3, 3, 2, 1, 1, 1],
    17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
    18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
    19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
    20: [4, 3, 3, 3, 3, 2, 2, 1, 1],
}


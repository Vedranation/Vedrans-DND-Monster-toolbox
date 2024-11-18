from GlobalStateManager import GSM
import tkinter as tk
import random

def RandomGenerator(RelPosRandGen):
    fumble_table = ["Get distracted: Disadvantage on next attack", "Overextended Swing: Next attack on you have advantage", "Hit yourself for half dmg",
                    "Hit ally for half dmg", "String Snap: If using a bow or crossbow", "Fall prone", "Ranged attack/spell: Goes in completely random direction and hits something",
                    "Drop your weapon", "Misjudged Distance: enemy within 5ft can attempt a free grapple check", "Twisted Ankle: half move speed next turn",
                    "Overexertion: Lose bonus action this turn", "Self doubt: Lose reaction this turn", "Ice spells: Your feet freeze, is rooted until next turn",
                    "Fire spells: Lit yourself on fire, 2 turns take 1d6 dmg or action to put it out", "Ranged weapons: Drop 10 pieces of ammunition, it scatters and needs action to collect",
                    "A random glass item/potion breaks and spills", "Coin pouch rips, you lose 5d8 GP", "If spell: Roll wild magic table", "Loud noise: You cause a very loud noise",
                    "Panic: Become frightened of whatever you just attacked", "Sand/Mud in eyes: Become blinded until your next turn", "Drop formation: Lose 2 AC until next turn",
                    "Instinct movement: You provoke instincts in enemy, they move 10ft immediately", "Nothing happens, lucky day", "You got distracted by a coin on the ground! Add 1GP to your inventory"]
    random_gen_result_label = None
    RelPosRandGen.constant_y = 40
    def RollFumbleButton():
        nonlocal random_gen_result_label
        if random_gen_result_label is not None:
            random_gen_result_label.destroy()

        random_gen_result_label = tk.Label(GSM.Random_generator_frame, text=(f"{random.choice(fumble_table)}"))
        random_gen_result_label.place(x=RelPosRandGen.reset("x"), y=RelPosRandGen.set("y", 120))

    # Random generator title
    random_generator_text_label = tk.Label(GSM.Random_generator_frame, text="Random Generator", font=GSM.Title_font)
    random_generator_text_label.place(x=RelPosRandGen.reset("x"), y=RelPosRandGen.reset("y"))

    roll_fumble_button = tk.Button(GSM.Random_generator_frame, text="Roll fumble", state="normal", command=RollFumbleButton,
                                               padx=9, background="grey")
    RelPosRandGen.reset("x")
    roll_fumble_button.place(x=RelPosRandGen.increase("x", 10), y=RelPosRandGen.increase("y", RelPosRandGen.constant_y))

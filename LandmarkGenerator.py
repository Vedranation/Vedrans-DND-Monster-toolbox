import random

# Lists of adjectives and nouns
adjectives = ["Abandoned", "Ancient", "Arcane", "Bewitched", "Blazing", "Celestial", "Crumbling", "Cursed", "Divine",
              "Echoing", "Enchanted", "Eternal", "Fabled", "Fallen", "Forbidden", "Forgotten", "Frosty", "Gleaming",
              "Glimmering", "Haunted", "Hidden", "Holy", "Imposing", "Infinite", "Lost", "Luminous", "Majestic", "Mysterious",
              "Mystic", "Obscured", "Ominous", "Pristine", "Radiant", "Rugged", "Sacred", "Secluded", "Shimmering", "Silent",
              "Sinister", "Soaring", "Stormy", "Tainted", "Timeless", "Tranquil", "Twisted", "Whispering", "Winding", "Infernal",
              "Floating", "Giant", "Tiny", "Large", "Small", "Goth", "Black", "Blue", "Green", "Yellow", "Colorful", "Purple",
              "White", "Grey", "Red", "Pink", "Multi-racial", "Metalic", "Underground", "Undead", "Underwater", "Dark",
              "Fleshy", "Tentacly", "Shadowy", "Rainbow", "Astral", "Elemental", "Bloody", "Sunken", "Gargantuan",
              "Glowing", "Wise", "Dumb", "Stupid", "Beautiful", "Pretty", "Ugly", "Starfall", "Invisible",
              "Ghostly", "Possessed", "Druidic", "Inverted", "Bandit", "Pirate", "Criminal", "Flying", "Cloudy"]

nouns = ["Abbey", "Archipelago", "Bastion", "Castle", "Cave", "Citadel", "Cliffs", "Crypt", "Dungeon", "Forest",
         "Fortress", "Garden", "Gorge", "Grove", "Harbor", "Island", "Lake", "Labyrinth", "Mountain", "Oasis",
         "Obelisk", "Palace", "Peak", "Pinnacle", "Portal", "Pyramid", "Swamp", "River", "Ruins", "Sanctuary", "Shrine",
         "Temple", "Tower", "Vault", "Village", "Volcano", "Waterfall", "Woods", "Bridge", "Ravine", "Hideout", "Cottage",
         "Monastery", "Trade Post", "Tavern", "Fountain", "Spring", "Desert", "Jungle", "Ship", "Battlefield", "Crystal",
         "Dragon", "School", "University", "City", "Gem", "Library", "Fairy", "Abyss", "Mines", "Pirate", "Cove",
         "Beach", "Dimension", "Grassland", "Goblin", "Market", "Unicorn", "Monster", "Shadow", "Observatory", "Fire",
         "Water", "Stone", "Metal", "Tree", "Ice", "Lantern", "Meteor", "Devil", "Demon", "Vampire", "Valley",
         "Illusion", "Marsh", "Ghost", "Circle", "Ring", "Square", "Druid", "Caravan", "Bandit", "Criminal", "Cloud",
         "Plateau", "House", "Treehouse"]

def check_for_repetition_item(item, item_list):
    if item in item_list:
        print(f"{item} is already in the list.")
    else:
        print(f"{item} NOT in the list.")

def generate_landmark():
    adjective = random.choice(adjectives)
    noun1 = random.choice(nouns)
    noun2 = random.choice(nouns)

    # Ensure noun1 and noun2 are not the same
    while noun1 == noun2:
        noun2 = random.choice(nouns)

    return f"{adjective} {noun1} {noun2}"

# Example usage to add new items
print("------")
check_for_repetition_item("Shadow", adjectives)
check_for_repetition_item("Shadowy", adjectives)
check_for_repetition_item("Dark", adjectives)
print("------")
check_for_repetition_item("Shadow", nouns)
check_for_repetition_item("Rock", nouns)
check_for_repetition_item("Treehouse", nouns)
print("------")
print(len(adjectives), len(nouns))
# Generate a landmark to see how it works
print(generate_landmark())

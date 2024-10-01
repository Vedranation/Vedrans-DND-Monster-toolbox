import time
import random
from PIL import Image
import pygame
from io import BytesIO

Tilemap = Image.open("WFC tiles.jpg")

class Tile:
    def __init__(self, grid_x:int, grid_y:int, ltop=0, lmid=0, lbot=0, topl=0, topm=0, topr=0, rtop=0, rmid=0, rbot=0, botl=0,
                 botm=0, botr=0, tile_type="default", name="tile"):
        self.Connection_points = {
            "ltop": ltop,
            "lmid": lmid,
            "lbot": lbot,
            "topl": topl,
            "topm": topm,
            "topr": topr,
            "rtop": rtop,
            "rmid": rmid,
            "rbot": rbot,
            "botl": botl,
            "botm": botm,
            "botr": botr,
        }
        self.tile_type = tile_type #start, goal, default
        self.tile = self._extract_tile(Tilemap, grid_x=grid_x, grid_y=grid_y)
        self.name = name
    def _extract_tile(self, tilemap: Image, grid_x: int, grid_y: int, grid_pixel_size:float=25.6) -> Image:
        x = grid_x * grid_pixel_size
        y = grid_y * grid_pixel_size
        width = height = 12 * grid_pixel_size
        return tilemap.crop((x, y, x + width, y + height))

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

def Pil_image_to_pygame(pil_image) -> pygame.image:
    shorter_dim = min(screen.get_width(), screen.get_height())
    tile_size_pixels = shorter_dim // max(Grid.width, Grid.height)
    resized_pil_image = pil_image.resize((tile_size_pixels, tile_size_pixels))

    mode = resized_pil_image.mode
    size = resized_pil_image.size
    data = resized_pil_image.tobytes()

    if mode == "RGBA":
        pygame_image = pygame.image.fromstring(data, size, mode)
    else:
        # Convert image to RGBA first
        resized_pil_image = resized_pil_image.convert("RGBA")
        data = resized_pil_image.tobytes()
        pygame_image = pygame.image.fromstring(data, size, "RGBA")
    return pygame_image
class Grid:
    def __init__(self, width: int, height: int, default_value=None):
        self.width = width
        self.height = height
        self.data = [default_value] * (width * height)

    def _index(self, x: int, y: int) -> int:
        '''Converts 2D coordinates into a 1D list index'''
        return x + y * self.width

    def set(self, x: int, y: int, tile: object) -> None:
        self.data[self._index(x, y)] = tile

    def get(self, x: int, y: int) -> object:
        return self.data[self._index(x, y)]

    def __str__(self) -> str:
        """String representation for debugging."""
        output = ''
        for y in range(self.height):
            output += ' '.join(str(self.get(x, y)) for x in range(self.width)) + '\n'
        return output

    def __len__(self) -> int:
        return len(self.data)

#Starting tiles, only 1
tile_start_T = Tile(grid_x=3, grid_y=2, lmid=1, rmid=1, tile_type="start")
tile_start_L = Tile(grid_x=17, grid_y=2, lmid=1, tile_type="start")
tile_start_split = Tile(grid_x=31, grid_y=2, topl=1, topr=1, tile_type="start")
start_tile = random.choice([tile_start_T, tile_start_L, tile_start_split])

#Default tiles
tile_I = Tile(grid_x=3, grid_y=16, topm=1, botm=1, tile_type="default", name="TileObj_I")
tile_cross = Tile(grid_x=17, grid_y=16, topm=1, botm=1, lmid=1, rmid=1, tile_type="default", name="TileObj_cross")
tile_sideway = Tile(grid_x=31, grid_y=16, topr=1, botl=1, tile_type="default", name="TileObj_sideway")
tile_L_toleft = Tile(grid_x=45, grid_y=16, lmid=1, botr=1, tile_type="default", name="TileObj_L_toleft")
tile_altar = Tile(grid_x=59, grid_y=16, botm=1, tile_type="default", name="TileObj__altar")

tile_chamber = Tile(grid_x=3, grid_y=30, topm=1, botm=1, tile_type="default", name="TileObj_chamber")
tile_bridge = Tile(grid_x=17, grid_y=30, lmid=1, rmid=1, tile_type="default", name="TileObj_bridge")
tile_round_deadend = Tile(grid_x=31, grid_y=30, botm=1, tile_type="default", name="TileObj_round_deadend")
tile_bot_left = Tile(grid_x=45, grid_y=30, lmid=1, botr=1, botl=1, tile_type="default", name="TileObj_bot_left")
tile_hallway_cap = Tile(grid_x=59, grid_y=30, botm=1, tile_type="default", name="TileObj_hallway_cap")
default_tiles = [tile_I, tile_cross, tile_sideway, tile_L_toleft, tile_altar,
                 tile_chamber, tile_bridge, tile_round_deadend, tile_bot_left, tile_hallway_cap]

Grid = Grid(6, 6)
Grid.set(x=random.randint(0, Grid.width-1), y=random.randint(0, Grid.height-1), tile=start_tile)

pygame.init()
screen_size = (800, 800)
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Dungeon generator")
pygame.font.init()  # You only need to call this once; initialize font module
font_size = 24
font = pygame.font.Font(None, font_size)  # Default font, and font size
pygame_tile_start = Pil_image_to_pygame(start_tile.tile)
running = True

def ComputeEntropy(x, y):
    '''Computes how many available connection points'''
    entropy = 0
    if x > 0: #Check left
        if Grid.get(x - 1, y):
            tile_l = Grid.get(x - 1, y)
            entropy += tile_l.Connection_points["rtop"]
            entropy += tile_l.Connection_points["rmid"]
            entropy += tile_l.Connection_points["rbot"]
        else:
            entropy += 3
    if x < Grid.width-1: #Check right
        if Grid.get(x + 1, y):
            tile_r = Grid.get(x + 1, y)
            entropy += tile_r.Connection_points["ltop"]
            entropy += tile_r.Connection_points["lmid"]
            entropy += tile_r.Connection_points["lbot"]
        else:
            entropy += 3
    if y > 0: #Check down
        if Grid.get(x, y - 1):
            tile_d = Grid.get(x, y - 1)
            entropy += tile_d.Connection_points["topl"]
            entropy += tile_d.Connection_points["topm"]
            entropy += tile_d.Connection_points["topr"]
        else:
            entropy += 3
    if y < Grid.height-1: #Check up
        if Grid.get(x, y + 1):
            tile_u = Grid.get(x, y + 1)
            entropy += tile_u.Connection_points["botl"]
            entropy += tile_u.Connection_points["botm"]
            entropy += tile_u.Connection_points["botr"]
        else:
            entropy += 3
    return entropy

def ChooseTileToPlace(x, y):
    free_connections = []
    forced_connections = []

    #Check available connection points
    if x > 0:  # Check left
        if Grid.get(x - 1, y):
            tile_l = Grid.get(x - 1, y)
            if tile_l.Connection_points["rtop"]:
                forced_connections.append("ltop")
            if tile_l.Connection_points["rmid"]:
                forced_connections.append("lmid")
            if tile_l.Connection_points["rbot"]:
                forced_connections.append("lbot")
        else:
            free_connections.append("ltop")
            free_connections.append("lmid")
            free_connections.append("lbot")
    if x < Grid.width - 1:  # Check right
        if Grid.get(x + 1, y):
            tile_r = Grid.get(x + 1, y)
            if tile_r.Connection_points["ltop"]:
                forced_connections.append("rtop")
            if tile_r.Connection_points["lmid"]:
                forced_connections.append("rmid")
            if tile_r.Connection_points["lbot"]:
                forced_connections.append("rbot")
        else:
            free_connections.append("rtop")
            free_connections.append("rmid")
            free_connections.append("rbot")
    if y > 0:  # Check down
        if Grid.get(x, y - 1):
            tile_d = Grid.get(x, y - 1)
            if tile_d.Connection_points["topl"]:
                forced_connections.append("botl")
            if tile_d.Connection_points["topm"]:
                forced_connections.append("botm")
            if tile_d.Connection_points["topr"]:
                forced_connections.append("botr")
        else:
            free_connections.append("botl")
            free_connections.append("botm")
            free_connections.append("botr")
    if y < Grid.height - 1:  # Check up
        if Grid.get(x, y + 1):
            tile_u = Grid.get(x, y + 1)
            if tile_u.Connection_points["botl"]:
                forced_connections.append("topl")
            if tile_u.Connection_points["botm"]:
                forced_connections.append("topm")
            if tile_u.Connection_points["botr"]:
                forced_connections.append("topr")
        else:
            free_connections.append("topl")
            free_connections.append("topm")
            free_connections.append("topr")

    available_tiles = []
    print(free_connections)
    for tile in default_tiles:
        if len(forced_connections) != 0: #Solve for all forced points
            if all(tile.Connection_points.get(conn_point) == 1 for conn_point in forced_connections):
                available_tiles.append(tile)
        else: #If no forced points, grab all tiles that may satisfy any free points and go there
            if any(tile.Connection_points.get(conn_point) == 1 for conn_point in free_connections):
                available_tiles.append(tile)
    if len(available_tiles) == 0:
        available_tiles = [tile_start_split]
    Grid.set(x, y, random.choice(available_tiles))
    print(available_tiles)
    return forced_connections

def draw_text(screen, text, position, font, color=(255, 255, 255)):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)

while running:
    #Clear the screen with a black background
    screen.fill((0, 0, 0))
    tile_dim = pygame_tile_start.get_height()
    max_y = screen_size[1] - tile_dim #Handles display Y inversion
    min_entropy_x_y = (0, 0)
    min_entropy = 999

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    '''Displays to display'''
    for y in range(Grid.height):
        for x in range(Grid.width):
            if not Grid.get(x, y): #No tile present
                tile_entropy = ComputeEntropy(x, y)
                if tile_entropy < min_entropy:
                    min_entropy_x_y = (x, y)
                    min_entropy = tile_entropy
                text_x = (tile_dim * x) + tile_dim // 2
                text_y = (max_y - tile_dim * y) + tile_dim // 2
                draw_text(screen, str(tile_entropy), (text_x, text_y), font)
                continue
            pygame_tile = Pil_image_to_pygame(Grid.get(x, y).tile)
            screen.blit(pygame_tile, (
                tile_dim * x,
                max_y - tile_dim * y))

    if min_entropy == 999:
        pygame.display.flip()
        continue

    connections = ChooseTileToPlace(min_entropy_x_y[0], min_entropy_x_y[1])
    text_x = (tile_dim * min_entropy_x_y[0]) + tile_dim // 3
    text_y = (max_y - tile_dim * min_entropy_x_y[1]) + tile_dim // 3
    draw_text(screen, str(connections), (text_x, text_y), font)
    # Update the display
    pygame.display.flip()

    time.sleep(1)


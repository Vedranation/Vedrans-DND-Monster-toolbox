import time
import random
import copy
from PIL import Image
import pygame
from typing import Literal, List

Tilemap = Image.open("WFC tiles 4k.jpg")

class Tile:
    def __init__(self, grid_x:int, grid_y:int, orientations:Literal[1, 2, 4]=1, mirror=False, ltop=0, lmid=0, lbot=0, topl=0, topm=0, topr=0, rtop=0, rmid=0, rbot=0, botl=0,
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
        self.tile_type = tile_type #start, goal, empty, default, bigroom
        self.tile = self._extract_tile(Tilemap, grid_x=grid_x, grid_y=grid_y)
        self.name = name
        self.orientations = orientations
        self.mirror = mirror
        self.variations = [self] #Will store itself + rotations/mirrors

    def GenerateVariations(self) -> List[object]:
        '''Generates the mirrors and rotations of the tile, since __init__ can't return values'''
        if (self.orientations == 2 or self.orientations == 4):
            rotations = self._generate_rotations(self, self.orientations)
            self.variations.extend(rotations)
        elif self.orientations != 1:
            raise ValueError("A tile can only have 1, 2, or 4 possible rotations")

        if self.mirror:
            mirror_tile = self._createMirrorHorCopy(self) #Generate mirror
            self.variations.append(mirror_tile)
            rotations = self._generate_rotations(mirror_tile, self.orientations) #Generate mirror rotations
            self.variations.extend(rotations)
        return self.variations

    def _extract_tile(self, tilemap: Image, grid_x: int, grid_y: int, grid_pixel_size:float=25.6) -> Image:
        """
    Extracts a tile from the specified position in a tilemap image.

    :param tilemap: The image from which to extract the tile.
    :type tilemap: Image
    :param grid_x: The x-coordinate of the tile in the grid.
    :type grid_x: int
    :param grid_y: The y-coordinate of the tile in the grid.
    :type grid_y: int
    :param grid_pixel_size: The size of one grid square in pixels, defaults to 25.6.
    :type grid_pixel_size: float
    :return: A cropped image of the tile.
    :rtype: Image

    This method calculates the pixel coordinates to extract based on the grid position and pixel size,
    then returns the cropped portion of the image.
    """
        x = grid_x * grid_pixel_size
        y = grid_y * grid_pixel_size
        width = height = 12 * grid_pixel_size
        return tilemap.crop((x, y, x + width, y + height))

    def _rotate90CounterClockwise(self, tile_obj: object) -> None:
        '''Rotates the passed object, does NOT return a copied one'''
        current = {
            'ltop': tile_obj.Connection_points.get('ltop', 0),
            'lmid': tile_obj.Connection_points.get('lmid', 0),
            'lbot': tile_obj.Connection_points.get('lbot', 0),
            'topl': tile_obj.Connection_points.get('topl', 0),
            'topm': tile_obj.Connection_points.get('topm', 0),
            'topr': tile_obj.Connection_points.get('topr', 0),
            'rtop': tile_obj.Connection_points.get('rtop', 0),
            'rmid': tile_obj.Connection_points.get('rmid', 0),
            'rbot': tile_obj.Connection_points.get('rbot', 0),
            'botl': tile_obj.Connection_points.get('botl', 0),
            'botm': tile_obj.Connection_points.get('botm', 0),
            'botr': tile_obj.Connection_points.get('botr', 0),
        }

        # Assign new positions based on CCW rotation
        tile_obj.Connection_points['botl'] = current['ltop']
        tile_obj.Connection_points['botm'] = current['lmid']
        tile_obj.Connection_points['botr'] = current['lbot']

        tile_obj.Connection_points['rtop'] = current['botr']
        tile_obj.Connection_points['rmid'] = current['botm']
        tile_obj.Connection_points['rbot'] = current['botl']

        tile_obj.Connection_points['topr'] = current['rbot']
        tile_obj.Connection_points['topm'] = current['rmid']
        tile_obj.Connection_points['topl'] = current['rtop']

        tile_obj.Connection_points['lbot'] = current['topl']
        tile_obj.Connection_points['lmid'] = current['topm']
        tile_obj.Connection_points['ltop'] = current['topr']
        tile_obj.tile = tile_obj.tile.transpose(Image.Transpose.ROTATE_90)

    def _createMirrorHorCopy(self, tile_obj: object) -> object:
        '''Creates a copy of passed object, mirrors it and returns it'''
        current = {
            'ltop': tile_obj.Connection_points.get('ltop', 0),
            'lmid': tile_obj.Connection_points.get('lmid', 0),
            'lbot': tile_obj.Connection_points.get('lbot', 0),
            'topl': tile_obj.Connection_points.get('topl', 0),
            'topm': tile_obj.Connection_points.get('topm', 0),
            'topr': tile_obj.Connection_points.get('topr', 0),
            'rtop': tile_obj.Connection_points.get('rtop', 0),
            'rmid': tile_obj.Connection_points.get('rmid', 0),
            'rbot': tile_obj.Connection_points.get('rbot', 0),
            'botl': tile_obj.Connection_points.get('botl', 0),
            'botm': tile_obj.Connection_points.get('botm', 0),
            'botr': tile_obj.Connection_points.get('botr', 0),
        }
        new_tile_obj = copy.deepcopy(tile_obj)
        new_tile_obj.name = f"{new_tile_obj.name}_mir"

        # Assign new positions based on horizontal (LR) flip
        new_tile_obj.Connection_points['botl'] = current['botr']
        new_tile_obj.Connection_points['botr'] = current['botl']

        new_tile_obj.Connection_points['rtop'] = current['ltop']
        new_tile_obj.Connection_points['rmid'] = current['lmid']
        new_tile_obj.Connection_points['rbot'] = current['lbot']

        new_tile_obj.Connection_points['topr'] = current['topl']
        new_tile_obj.Connection_points['topl'] = current['topr']

        new_tile_obj.Connection_points['lbot'] = current['rbot']
        new_tile_obj.Connection_points['lmid'] = current['rmid']
        new_tile_obj.Connection_points['ltop'] = current['rtop']
        new_tile_obj.tile = new_tile_obj.tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        return new_tile_obj

    def _generate_rotations(self, original_tile: object, n_orientations: Literal[2, 4]) -> list:
        '''Produces 1-3 extra rotations of the passed tile, n_orientations = 2 (1 extra rotation) or 4 (3 extra rotations)
        '''
        rotations = []
        tile_name_base = original_tile.name
        current_tile = original_tile
        # 0 degrees is the original, so start with 90
        for i in range(1, n_orientations):  # 1*90=90, 2*90=180, 3*90=270
            new_tile = copy.deepcopy(current_tile)
            new_tile.name = f"{tile_name_base}_{i * 90}"
            self._rotate90CounterClockwise(new_tile)  # Assume this modifies new_tile to rotate it
            rotations.append(new_tile)
            current_tile = new_tile  # Set the current tile to the newly rotated tile for the next iteration
        return rotations
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



class TileObjectsFactory:
    '''Stores all tile objects for encapsulation purposes - time to make this a Factory'''
    def TileRelativePosToBlocksX(self, x_pos:int, n_blocks_between=2, n_tile_width=12, start_blocks_x=3) -> int:
        """
    Transforms relative X into number of blocks so it can be passed into Tile class

    :param x_pos: the position of tile relative to other tiles on the X axis (from 0 to inf)
    :type x_pos: int
    :param n_blocks_between: How many blocks separates each tile in X
    :type n_blocks_between: int
    :param n_tile_width: How many blocks in X is the tile wide
    :type n_tile_width: int
    :param start_blocks_x: The offset from left side of screen to the first tile
    :type start_blocks_x: int
    :return: The position in X from left side of screen to wanted tile in a number of blocks
    :rtype: int
    """
        return start_blocks_x + x_pos * (n_blocks_between + n_tile_width)

    def TileRelativePosToBlocksY(self, y_pos:int, n_blocks_between=2, n_tile_width=12, start_blocks_y=2) -> int:
        """
    Transforms relative Y into number of blocks so it can be passed into Tile class

    :param y_pos: the position of tile relative to other tiles on the Y axis (from 0 to inf)
    :type y_pos: int
    :param n_blocks_between: How many blocks separates each tile in Y
    :type n_blocks_between: int
    :param n_tile_width: How many blocks in Y is the tile tall
    :type n_tile_width: int
    :param start_blocks_y: The offset from top of screen to the first tile
    :type start_blocks_y: int
    :return: The position in Y from top of screen to wanted tile in a number of blocks
    :rtype: int
    """
        return start_blocks_y + y_pos * (n_blocks_between + n_tile_width)

    def __init__(self):
        '''Factory that creates all tiles and their mirrored or rotated variations'''

        '''for easy position tracking'''
        self.default_tiles = []
        self.start_tiles = []
        x0 = self.TileRelativePosToBlocksX(0)
        x1 = self.TileRelativePosToBlocksX(1)
        x2 = self.TileRelativePosToBlocksX(2)
        x3 = self.TileRelativePosToBlocksX(3)
        x4 = self.TileRelativePosToBlocksX(4)

        y0 = self.TileRelativePosToBlocksY(0)
        y1 = self.TileRelativePosToBlocksY(1)
        y2 = self.TileRelativePosToBlocksY(2)
        y3 = self.TileRelativePosToBlocksY(3)
        y4 = self.TileRelativePosToBlocksY(4)
        y5 = self.TileRelativePosToBlocksY(5)
        '''Start tiles'''
        # Y=0
        start_tiles_constructor = [
{"name": "TileObj_start_T", "grid_x": 3, "grid_y": 2, "lmid": 1, "rmid": 1, "tile_type": "start", "orientations": 4, "mirror": False},
{"name": "TileObj_start_L", "grid_x": 17, "grid_y": 2, "lmid": 1, "tile_type": "start", "orientations": 4, "mirror": True},
{"name": "TileObj_start_split", "grid_x": 31, "grid_y": 2, "topl": 1, "topr": 1, "tile_type": "start", "orientations": 4, "mirror": False},
{"name": "TileObj_start_pentagon", "grid_x": 45, "grid_y": 2, "topm": 1, "tile_type": "start", "orientations": 4, "mirror": False},
{"name": "TileObj_start_crookedL", "grid_x": 59, "grid_y": 2, "topm": 1, "lbot": 1, "tile_type": "start", "orientations": 4, "mirror": True}
]

        for data in start_tiles_constructor:
            tile = Tile(**data) #Create a tile and unpack kwargs
            self.start_tiles.extend(tile.GenerateVariations())
        self.start_tile = random.choice(self.start_tiles)

        '''Default tiles'''
        # Y=1
        default_tiles_constructor = [
{"name": "TileObj_I", "grid_x": 3, "grid_y": 16, "topm": 1, "botm": 1, "tile_type": "default", "orientations": 2},
{"name": "TileObj_cross", "grid_x": 17, "grid_y": 16, "topm": 1, "botm": 1, "lmid": 1, "rmid": 1, "tile_type": "default"},
{"name": "TileObj_sideway", "grid_x": 31, "grid_y": 16, "topr": 1, "botl": 1, "tile_type": "default", "orientations": 4, "mirror": True},
{"name": "TileObj_L_toleft", "grid_x": 45, "grid_y": 16, "lmid": 1, "botr": 1, "tile_type": "default", "orientations": 4, "mirror": True},
{"name": "TileObj_altar", "grid_x": 59, "grid_y": 16, "botm": 1, "tile_type": "default", "orientations": 4},

        # Y=2
{"name": "TileObj_chamber", "grid_x": 3, "grid_y": 30, "topm": 1, "botm": 1, "tile_type": "default", "orientations": 2},
{"name": "TileObj_bridge", "grid_x": 17, "grid_y": 30, "lmid": 1, "rmid": 1, "tile_type": "default", "orientations": 2},
{"name": "TileObj_round_deadend", "grid_x": 31, "grid_y": 30, "botm": 1, "tile_type": "default", "orientations": 4},
{"name": "TileObj_bot_left", "grid_x": 45, "grid_y": 30, "lmid": 1, "botr": 1, "botl": 1, "tile_type": "default",
 "mirror": True, "orientations": 4},
{"name": "TileObj_hallway_cap", "grid_x": 59, "grid_y": 30, "botm": 1, "tile_type": "default", "orientations": 4},

        # Y=3
{"name": "TileObj_corner", "grid_x": 3, "grid_y": 44, "topm": 1, "rmid": 1, "tile_type": "default", "orientations": 4},
{"name": "TileObj_half_diagonal", "grid_x": 17, "grid_y": 44, "lmid": 1, "rtop": 1, "tile_type": "default",
 "orientations": 4, "mirror": True},
{"name": "TileObj_bigroom_corner", "grid_x": x2, "grid_y": y3, "topl": 1, "topm": 1, "topr": 1, "rtop": 1,
 "rmid": 1, "rbot": 1, "tile_type": "default", "orientations": 4},
{"name": "TileObj_bigroom_walled_entrance", "grid_x": x3, "grid_y": y3, "rmid": 1, "ltop": 1, "lmid": 1, "lbot": 1,
 "tile_type": "default", "orientations": 4},
{"name": "TileObj_T_block", "grid_x": x4, "grid_y": y3, "lmid": 1, "rmid": 1, "topm": 1, "tile_type": "default", "orientations": 4},

        # Y=4
{"name": "TileObj_mini_double_corner", "grid_x": x0, "grid_y": y4, "topl": 1,
 "ltop": 1, "rbot": 1, "botr": 1, "tile_type": "default", "orientations": 2},
{"name": "TileObj_V", "grid_x": x1, "grid_y": y4, "topl": 1, "topr": 1, "botm": 1,
 "tile_type": "default", "orientations": 4},
{"name": "TileObj_bigroom_corner_entrance", "grid_x": x2, "grid_y": y4, "lmid": 1,
 "rtop": 1, "rmid": 1, "rbot": 1, "botl": 1, "botm": 1, "botr": 1, "tile_type": "default",
 "orientations": 4, "mirror": True},
{"name": "TileObj_bigroom_walled", "grid_x": x3, "grid_y": y4, "ltop": 1, "lmid": 1,
 "lbot": 1, "tile_type": "default", "orientations": 4},
{"name": "TileObj_mini_corner", "grid_x": x4, "grid_y": y4, "topl": 1, "ltop": 1,
 "tile_type": "default", "orientations": 2},

        # Y=5
{"name": "TileObj_pillars", "grid_x": x1, "grid_y": y5, "topm": 1, "botm": 1, "tile_type": "default",
 "orientations": 2},
{"name": "TileObj_stripes_side", "grid_x": x2, "grid_y": y5, "lbot": 1, "rbot": 1, "topl": 1, "topr": 1,
 "tile_type": "default", "orientations": 4},
{"name": "TileObj_corner_humped", "grid_x": x3, "grid_y": y5, "ltop": 1, "topm": 1,
 "tile_type": "default", "orientations": 4, "mirror": True},
{"name": "TileObj_corner_humped2", "grid_x": x4, "grid_y": y5, "ltop": 1, "topr": 1,
 "tile_type": "default", "orientations": 4, "mirror": True},
]

        for data in default_tiles_constructor:
            tile = Tile(**data) #Create a tile and unpack kwargs
            self.default_tiles.extend(tile.GenerateVariations())

        # Empty tile (when can't find a tile that solves)
        empty_constructor = {"name": "TileObj_empty", "grid_x": x0, "grid_y": y5, "tile_type": "empty"}
        self.tile_empty = Tile(**empty_constructor)

TileObj = TileObjectsFactory()
Grid = Grid(6, 6)
Grid.set(x=random.randint(1, Grid.width-2), y=random.randint(1, Grid.height-2), tile=TileObj.start_tile)

pygame.init()
screen_size = (800, 800)
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Dungeon generator")
pygame.font.init()  # You only need to call this once; initialize font module
font_size = 24
font = pygame.font.Font(None, font_size)  # Default font, and font size
pygame_tile_start = Pil_image_to_pygame(TileObj.start_tile.tile)
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
    else:
        entropy += 3
    return entropy

def ChooseTileToPlace(x, y):
    forced_connections = []
    blocked_connections = []

    #Check available connection points
    if x > 0:  # Check left
        if Grid.get(x - 1, y):
            tile_l = Grid.get(x - 1, y)
            if not tile_l.tile_type == "empty":  # if tile is empty, no connections are required or blocked
                if tile_l.Connection_points["rtop"]:
                    forced_connections.append("ltop")
                else:
                    blocked_connections.append("ltop") #If there isn't a connection on occupied tile, we gotta block it
                if tile_l.Connection_points["rmid"]:
                    forced_connections.append("lmid")
                else:
                    blocked_connections.append("lmid")
                if tile_l.Connection_points["rbot"]:
                    forced_connections.append("lbot")
                else:
                    blocked_connections.append("lbot")
    else: # World edge, no connection allowed
        blocked_connections.append("ltop")
        blocked_connections.append("lmid")
        blocked_connections.append("lbot")

    if x < Grid.width - 1:  # Check right
        if Grid.get(x + 1, y):
            tile_r = Grid.get(x + 1, y)
            if not tile_r.tile_type == "empty":  # if tile is empty, no connections are required or blocked
                if tile_r.Connection_points["ltop"]:
                    forced_connections.append("rtop")
                else:
                    blocked_connections.append("rtop") #If there isn't a connection on occupied tile, we gotta block it
                if tile_r.Connection_points["lmid"]:
                    forced_connections.append("rmid")
                else:
                    blocked_connections.append("rmid") #If there isn't a connection on occupied tile, we gotta block it
                if tile_r.Connection_points["lbot"]:
                    forced_connections.append("rbot")
                else:
                    blocked_connections.append("rbot") #If there isn't a connection on occupied tile, we gotta block it
    else:
        blocked_connections.append("rtop")
        blocked_connections.append("rmid")
        blocked_connections.append("rbot")
    if y > 0:  # Check down
        if Grid.get(x, y - 1):
            tile_d = Grid.get(x, y - 1)
            if not tile_d.tile_type == "empty":  # if tile is empty, no connections are required or blocked
                if tile_d.Connection_points["topl"]:
                    forced_connections.append("botl")
                else:
                    blocked_connections.append("botl") #If there isn't a connection on occupied tile, we gotta block it
                if tile_d.Connection_points["topm"]:
                    forced_connections.append("botm")
                else:
                    blocked_connections.append("botm") #If there isn't a connection on occupied tile, we gotta block it
                if tile_d.Connection_points["topr"]:
                    forced_connections.append("botr")
                else:
                    blocked_connections.append("botr") #If there isn't a connection on occupied tile, we gotta block it
    else:
        blocked_connections.append("botl")
        blocked_connections.append("botm")
        blocked_connections.append("botr")
    if y < Grid.height - 1:  # Check up
        if Grid.get(x, y + 1):
            tile_u = Grid.get(x, y + 1)
            if not tile_u.tile_type == "empty":  # if tile is empty, no connections are required or blocked
                if tile_u.Connection_points["botl"]:
                    forced_connections.append("topl")
                else:
                    blocked_connections.append("topl") #If there isn't a connection on occupied tile, we gotta block it
                if tile_u.Connection_points["botm"]:
                    forced_connections.append("topm")
                else:
                    blocked_connections.append("topm") #If there isn't a connection on occupied tile, we gotta block it
                if tile_u.Connection_points["botr"]:
                    forced_connections.append("topr")
                else:
                    blocked_connections.append("topr") #If there isn't a connection on occupied tile, we gotta block it
    else:
        blocked_connections.append("topl")
        blocked_connections.append("topm")
        blocked_connections.append("topr")

    available_tiles = []
    for tile in TileObj.default_tiles:
        if all(tile.Connection_points.get(conn_point) == 1 for conn_point in forced_connections) and \
            not any(tile.Connection_points.get(conn_point) == 1 for conn_point in blocked_connections):
            available_tiles.append(tile)


    if len(available_tiles) == 0:
        available_tiles = [TileObj.tile_empty]
    Grid.set(x, y, random.choice(available_tiles))
    return blocked_connections

def draw_text(screen, text, position, font, color=(255, 255, 255)):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)

'''Main loop'''
First_Pass = True
while running:

    #First pass - place down all tiles according to rules
    #Clear the screen with a black background
    screen.fill((0, 0, 0))
    tile_dim = pygame_tile_start.get_height()
    max_y = screen_size[1] - tile_dim #Handles display Y inversion
    min_entropy_x_y = (0, 0)
    min_entropy = 999

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    '''Compute entropy and draw tiles and text'''
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
        First_Pass = False
        time.sleep(0.5)
        continue

    connections = ChooseTileToPlace(min_entropy_x_y[0], min_entropy_x_y[1])
    text_x = (tile_dim * min_entropy_x_y[0]) + tile_dim // 3
    text_y = (max_y - tile_dim * min_entropy_x_y[1]) + tile_dim // 3
    draw_text(screen, str(connections), (text_x, text_y), font)
    # Update the display
    pygame.display.flip()
    time.sleep(0.05)
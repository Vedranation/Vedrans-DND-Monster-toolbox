import time
import random
import copy
from PIL import Image, ImageDraw
import pygame
from typing import Literal, List

Tilemap = Image.open("WFC tiles 4k.jpg")
Tilemap_mask = Image.open("WFC tiles mask 4k.jpg")
Decoratormap = Image.open("WFC objects decorators 4k transparent.png")



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
        self.tile = self._extract_tile(Tilemap, global_grid_x=grid_x, global_grid_y=grid_y)
        self.tile_mask = self._extract_tile(Tilemap_mask, grid_x, global_grid_y=grid_y) #Image of the tilemap
        self.name = name
        self.orientations = orientations
        self.mirror = mirror
        self.variations = [self] #Will store itself + rotations/mirrors

        self.valid_decorator_locations: List[tuple] = [] #Decorator - items which make map prettier but are not interractible or tangible
        self.valid_obstacles_locations: List[tuple] = [] #Obstacle - items which cannot be passed through
        self.obstacles: List = []
        self.decorators = []

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

    def _extract_tile(self, tilemap: Image, global_grid_x: int, global_grid_y: int, grid_pixel_size:float=26,
                      blocks_in_tile: int = 12) -> Image:
        """
    Extracts a tile from the specified position in a tilemap image.

    :param tilemap: The image from which to extract the tile.
    :type tilemap: Image
    :param global_grid_x: The x-coordinate of the tile in the GLOBAL grid.
    :type global_grid_x: int
    :param global_grid_y: The y-coordinate of the tile in the GLOBAL grid.
    :type global_grid_y: int
    :param grid_pixel_size: The size of one grid square in pixels, defaults to 25.6.
    :type grid_pixel_size: float
    :return: A cropped image of the tile.
    :rtype: Image

    This method calculates the pixel coordinates to extract based on the grid position and pixel size,
    then returns the cropped portion of the image.
    """
        x = global_grid_x * grid_pixel_size
        y = global_grid_y * grid_pixel_size
        width = height = blocks_in_tile * grid_pixel_size
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
        tile_obj.tile_mask = tile_obj.tile_mask.transpose(Image.Transpose.ROTATE_90)

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
        new_tile_obj.tile_mask = new_tile_obj.tile_mask.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
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

    def CanPlaceObject(self, local_tile_grid_x: int, local_tile_grid_y: int, item: Literal["obstacle, decorator"]):
        """ Check mask to see if an object can be placed at (x, y)
         :param local_tile_grid_x This means the blocks on the LOCAL tile grid, from 0 to tile width/height
         :param item: What to search for - green is obstacle, decorator is blue"""
        block_length = self.tile_mask.size[0] // 12
        middle_x = local_tile_grid_x * block_length + block_length // 2
        middle_y = local_tile_grid_y * block_length + block_length // 2
        block_mask_pixel = self.tile_mask.getpixel((middle_x, middle_y))
        blue = (23, 73, 141)
        green = (22, 199, 49)
        color = blue if item == "decorator" else green
        result = self._is_color_within_tolerance(block_mask_pixel, color)
        return result

    def DrawRedSquare(self, local_tile_grid_x: int, local_tile_grid_y: int):
        '''Draws a red square on tilemask for debugging'''
        block_length = self.tile_mask.size[0] // 12
        self.draw = ImageDraw.Draw(self.tile_mask)  # Allows drawing on the mask

        # draw red square
        top_left = (
        local_tile_grid_x * block_length + int(block_length * 0.25), local_tile_grid_y * block_length + int(block_length * 0.25))
        bottom_right = (top_left[0] + block_length // 2, top_left[1] + block_length // 2)
        self.draw.rectangle([top_left, bottom_right], fill=(255, 0, 0))  # Red for visibility

    def _is_color_within_tolerance(self, pixel_color: tuple, target_color: tuple, tolerance=5) -> bool:
        """
        Check if the pixel color is within the tolerance range of the target color.

        :param pixel_color: The RGB color of the pixel (r, g, b).
        :param target_color: The RGB target color (r, g, b).
        :param tolerance: The tolerance level for each color channel.

        :return bool: True if the pixel color is within the tolerance, False otherwise.
        """
        return all(abs(pixel_color[i] - target_color[i]) <= tolerance for i in range(3))

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

class Decorator:
    def __init__(self, name: str, dimensions: tuple, type: Literal["decorator", "obstacle"], grid_x, grid_y):
        '''Decorators, obstacles and the like to be placed onto individual tiles

        :param name: the name of the decorator (chest, rug, pillar etc)
        :param dimensions: (width, height)
        :param type: What type of item this is, basically what color to dump it on
        :param grid_x: On tilemap where is this (same for grid_y)'''
        self.width: int = dimensions[0]
        self.height: int = dimensions[1]
        self.type: str = type #decorator (blue), obstacle (green)
        self.x: int = None
        self.y: int = None
        self.image = self._extract_tile(Decoratormap, global_grid_x=grid_x, global_grid_y=grid_y)
        self.name: str = name

    def _extract_tile(self, tilemap: Image, global_grid_x: int, global_grid_y: int, grid_pixel_size:float=26,
                      blocks_in_tile: int = 6) -> Image:
        """
    Extracts a tile from the specified position in a tilemap image.

    :param tilemap: The image from which to extract the tile.
    :type tilemap: Image
    :param global_grid_x: The x-coordinate of the tile in the GLOBAL grid.
    :type global_grid_x: int
    :param global_grid_y: The y-coordinate of the tile in the GLOBAL grid.
    :type global_grid_y: int
    :param grid_pixel_size: The size of one grid square in pixels, defaults to 25.6.
    :type grid_pixel_size: float
    :return: A cropped image of the tile.
    :rtype: Image

    This method calculates the pixel coordinates to extract based on the grid position and pixel size,
    then returns the cropped portion of the image.
    """
        x = global_grid_x * grid_pixel_size
        y = global_grid_y * grid_pixel_size
        width = height = blocks_in_tile * grid_pixel_size
        return tilemap.crop((x, y, x + width, y + height))

def Pil_image_to_pygame(pil_image, is_tile=True) -> pygame.image:
    shorter_dim = min(screen.get_width(), screen.get_height())
    tile_size_pixels = shorter_dim // max(Grid.width, Grid.height)
    if is_tile: #Is main tile using 12x12 blocks
        resized_pil_image = pil_image.resize((tile_size_pixels, tile_size_pixels))
    else: #Is decorator using 6x6 blocks
        resized_pil_image = pil_image.resize((tile_size_pixels//2, tile_size_pixels//2))


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
        y6 = self.TileRelativePosToBlocksY(6)
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

        # Y=6
{"name": "TileObj_diagonal", "grid_x": x0, "grid_y": y6, "ltop": 1, "botr": 1, "tile_type": "default",
 "orientations": 4, "mirror": True},
{"name": "TileObj_bigroom_walled_entrance_side", "grid_x": x1, "grid_y": y6, "rmid": 1, "topl": 1, "topm": 1,"topr": 1,
 "tile_type": "default", "orientations": 4, "mirror": True},
{"name": "TileObj_fork", "grid_x": x2, "grid_y": y6, "botm": 1, "topl": 1, "topr": 1,
 "tile_type": "default", "orientations": 4},
{"name": "TileObj_bigroom_corner_entrance_side", "grid_x": x3, "grid_y": y6, "ltop": 1, "rtop": 1, "rmid": 1, "rbot": 1,
 "botl": 1, "botm": 1, "botr": 1, "tile_type": "default", "orientations": 4, "mirror": True},

]

        for data in default_tiles_constructor:
            tile = Tile(**data) #Create a tile and unpack kwargs
            self.default_tiles.extend(tile.GenerateVariations())

        # Empty tile (when can't find a tile that solves)
        empty_constructor = {"name": "TileObj_empty", "grid_x": x0, "grid_y": y5, "tile_type": "empty"}
        self.tile_empty = Tile(**empty_constructor)

TileObj = TileObjectsFactory()
Grid = Grid(6, 6) #Keep it square
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

def ChooseAndPlaceTile(x:int, y:int) -> list:
    '''Places a tile down and returns blocked_connections or forced_connections for debug purposes'''
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

def HandleEvents() -> None:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            global running
            running = False

def FirstPass(tile_dim: int, max_y: int) -> (tuple, int):
    '''Compute entropy and draw current tiles and text to screen

    :param tile_dim: the dimension (pixels) of each individual tile
    :param max_y: max_y so screen can be inverted from window to cartesian coordinates
    :return (x, y) of minimum entropy, and its int value'''
    min_entropy_x_y = (0, 0)
    min_entropy = 999

    for y in range(Grid.height):
        for x in range(Grid.width):
            if not Grid.get(x, y):  # No tile present
                tile_entropy = ComputeEntropy(x, y)
                if tile_entropy < min_entropy:
                    min_entropy_x_y = (x, y)
                    min_entropy = tile_entropy
                text_x = (tile_dim * x) + tile_dim // 2
                text_y = (max_y - tile_dim * y) + tile_dim // 2
                draw_text(screen, str(tile_entropy), (text_x, text_y), font)
                continue
            global Debug
            if Debug:
                pygame_tile = Pil_image_to_pygame(Grid.get(x, y).tile_mask)  # Draw tile mask to screen
            else:
                pygame_tile = Pil_image_to_pygame(Grid.get(x, y).tile)  # Draw tile to screen
            screen.blit(pygame_tile, (tile_dim * x, max_y - tile_dim * y))

    return min_entropy_x_y, min_entropy

def SecondPass() -> bool:
    '''Delete all empty tiles and their adjacents

    return True if there are missing tiles on the map'''
    missing_tiles_present = False #Are there any missing tiles on the map
    for y in range(Grid.height):
        for x in range(Grid.width):
            current_tile = Grid.get(x, y)
            if current_tile and current_tile.tile_type == "empty":  # An empty tile is present
                Grid.set(x, y, None)  # Delete the empty tile
                # Check and delete adjacent tiles, ensuring they exist and are not 'start' tiles
                if y > 0:
                    north_tile = Grid.get(x, y - 1)
                    if north_tile and north_tile.tile_type != "start":
                        Grid.set(x, y - 1, None)
                        missing_tiles_present = True
                if y < Grid.height - 1:
                    south_tile = Grid.get(x, y + 1)
                    if south_tile and south_tile.tile_type != "start":
                        Grid.set(x, y + 1, None)
                        missing_tiles_present = True
                if x > 0:
                    west_tile = Grid.get(x - 1, y)
                    if west_tile and west_tile.tile_type != "start":
                        Grid.set(x - 1, y, None)
                        missing_tiles_present = True
                if x < Grid.width - 1:
                    east_tile = Grid.get(x + 1, y)
                    if east_tile and east_tile.tile_type != "start":
                        Grid.set(x + 1, y, None)
                        missing_tiles_present = True
    return missing_tiles_present

def ThirdPass(tile_dim):
    '''Identifies placeable areas, stores them as tuples

    :param tile_dim: Dimension of the individual tile (must be square), passed from main loop
    '''
    #Identify placeable areas
    for y in range(Grid.height):
        for x in range(Grid.width):
            tile = Grid.get(x, y)
            for local_y in range(12):
                for local_x in range(12):
                    if tile.CanPlaceObject(local_x, local_y, "obstacle"):

                        local_y = 11 - local_y
                        tile.valid_obstacles_locations.append((local_x, local_y))
                    elif tile.CanPlaceObject(local_x, local_y, "decorator"):
                        # tile.DrawRedSquare(local_x, local_y)

                        local_y = 11 - local_y  # invert Y for displaying

                        grid_pixel_size = screen_size[0] // (Grid.width * 12)
                        global_decorator_x = tile_dim * x + local_x * grid_pixel_size
                        global_decorator_y = screen_size[1] - (
                                    tile_dim * y + (local_y * grid_pixel_size + grid_pixel_size))
                        # pygame.draw.rect(screen, "red", (global_decorator_x, global_decorator_y, 10, 10))


                        tile.valid_decorator_locations.append((local_x, local_y))

    #Place decorators
    n_decorations = 3
    n_obstacles = 2
    grid_pixel_size = screen_size[0] // (Grid.width * 12) #Compute DISPLAY size of each pixel (this is different to export picture)

    data = {"name": "bear_trap", "dimensions": (1, 1), "type":"decorator", "grid_x":3, "grid_y":11} #TODO: make it automatic factory in another file
    bear_trap = Decorator(**data)
    data = {"name": "stone_rubble_1", "dimensions": (3, 2), "type": "decorator", "grid_x": 27,
            "grid_y": 11}
    stone_rubble_1 = Decorator(**data)

    def _is_valid_decorator_placement(start_pos, decorator, tile):
        """Check if the decorator can be placed starting at start_pos."""
        start_x, start_y = start_pos

        # Collect all positions the decorator will occupy
        required_positions = [
            (start_x + dx, start_y + dy)
            for dx in range(decorator.width)  # Width of the decorator
            for dy in range(decorator.height)  # Height of the decorator
        ]

        # Check if all required positions are available
        for pos in required_positions:
            if pos not in tile.valid_decorator_locations:
                return False  # One or more required positions are invalid

        return True  # All positions are valid

    for y in range(Grid.height):
        for x in range(Grid.width):
            tile = Grid.get(x, y)

            if not tile.valid_decorator_locations: #Tile has no locations to place it on
                continue

            random_pos = random.choice(tile.valid_decorator_locations)
            if not _is_valid_decorator_placement(random_pos, stone_rubble_1, tile):
                continue

            # Remove all positions that the decorator will occupy from valid locations
            for dx in range(bear_trap.width):
                for dy in range(bear_trap.height):
                    occupied_pos = (random_pos[0] + dx, random_pos[1] + dy)
                    tile.valid_decorator_locations.remove(occupied_pos)


            stone_rubble_1.x, stone_rubble_1.y = random_pos[0], random_pos[1]
            tile.decorators.append(stone_rubble_1)

            pygame_decorator = Pil_image_to_pygame(stone_rubble_1.image, is_tile=False)  # Draw tile to screen

            global_decorator_x = tile_dim * x + stone_rubble_1.x * grid_pixel_size
            global_decorator_y = screen_size[1] - (tile_dim * y + (stone_rubble_1.y * grid_pixel_size + grid_pixel_size))

            screen.blit(pygame_decorator, (global_decorator_x, global_decorator_y))

            if Debug:
                # pygame.draw.rect(screen, "red", (global_decorator_x, global_decorator_y, 10, 10))
                pass
            # print(f"Tile: ({x}, {y}) - pos: ({bear_trap.x}, {bear_trap.y}) - pixel: ({global_decorator_x},{global_decorator_y})")
            pygame.display.flip()
            # time.sleep(0.1)


'''Main loop'''
Second_Pass = False
Third_Pass = False
Debug = False
while running:

    #Second pass - delete all tiles adjacent to empty, and try again
    if Second_Pass:
        Third_Pass = not SecondPass() #Returns True once there are no more white (empty) tiles to fix
        Second_Pass = False

    #First pass - place down all tiles according to rules
    screen.fill((0, 0, 0)) #Clear the screen with a black background
    tile_dim = pygame_tile_start.get_height()
    max_y = screen_size[1] - tile_dim  # Handles display Y inversion

    HandleEvents()
    min_entropy_x_y, min_entropy = FirstPass(tile_dim, max_y) #Computes entropy and draws present tiles

    if min_entropy != 999: #The board isn't filled entirely with tiles (including empty tiles)
        connections = ChooseAndPlaceTile(min_entropy_x_y[0], min_entropy_x_y[1])
        text_x = (tile_dim * min_entropy_x_y[0]) + tile_dim // 3
        text_y = (max_y - tile_dim * min_entropy_x_y[1]) + tile_dim // 3
        draw_text(screen, str(connections), (text_x, text_y), font)
        pygame.display.flip()

    else:
        Second_Pass = True
        pygame.display.flip()
        # time.sleep(0.5)

    # time.sleep(0.5)

    if Third_Pass:
        ThirdPass(tile_dim)
        # screen.fill((0, 0, 0))  # Clear the screen with a black background
        # tile_dim = pygame_tile_start.get_height()
        # max_y = screen_size[1] - tile_dim  # Handles display Y inversion
        #
        # HandleEvents()
        # min_entropy_x_y, min_entropy = FirstPass(tile_dim, max_y)  # Computes entropy and draws present tiles
        while True:
            HandleEvents()
            pygame.display.flip()
        pass

    Third_Pass = False

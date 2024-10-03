import time
import random
import copy
from PIL import Image
import pygame
from typing import Literal

Tilemap = Image.open("WFC tiles 4k.jpg")

class Tile:
    def __init__(self, grid_x:int, grid_y:int, rotations:Literal[0, 1, 3]=0, mirror=False, ltop=0, lmid=0, lbot=0, topl=0, topm=0, topr=0, rtop=0, rmid=0, rbot=0, botl=0,
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
        self.tile_type = tile_type #start, goal, empty, default
        self.tile = self._extract_tile(Tilemap, grid_x=grid_x, grid_y=grid_y)
        self.name = name
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

def Rotate90CounterClockwise(tile_obj: object) -> None:
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

def CreateMirrorHorCopy(tile_obj: object) -> object:
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

def Generate_rotations(original_tile: object, tile_name_base: str, n_positions: int) -> list:
    '''Produces 3 rotations of the passed tile, n_positions 2 (only 1 rotation) or 4 (3 rotations)
    '''
    rotations = []
    current_tile = original_tile
    # 0 degrees is the original, so start with 90
    for i in range(1, n_positions):  # 1*90=90, 2*90=180, 3*90=270
        new_tile = copy.deepcopy(current_tile)
        new_tile.name = f"{tile_name_base}_{i * 90}"
        Rotate90CounterClockwise(new_tile)  # Assume this modifies new_tile to rotate it
        rotations.append(new_tile)
        current_tile = new_tile  # Set the current tile to the newly rotated tile for the next iteration
    return rotations

class DefineTileObjects():
    '''Stores all tile objects for encapsulation purposes'''
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
        '''Create all tiles'''

        '''Starting tiles, only 1, Y=0'''
        self.default_tiles = []
        tile_start_T = Tile(grid_x=3, grid_y=2, lmid=1, rmid=1, tile_type="start", name="TileObj_start_T")
        tile_start_L = Tile(grid_x=17, grid_y=2, lmid=1, tile_type="start", name="TileObj_start_L")
        tile_start_split = Tile(grid_x=31, grid_y=2, topl=1, topr=1, tile_type="start", name="TileObj_start_split")
        tile_start_pentagon = Tile(grid_x=45, grid_y=2, topm=1, tile_type="start", name="TileObj_start_pentagon")
        tile_start_crookedL = Tile(grid_x=59, grid_y=2, topm=1, lbot=1, tile_type="start", name="TileObj_start_crookedL")
        self.start_tiles = [tile_start_T, tile_start_L, tile_start_split, tile_start_pentagon, tile_start_crookedL]
        rotations = Generate_rotations(tile_start_T, tile_start_T.name, 4)
        self.start_tiles.extend(rotations)
        rotations = Generate_rotations(tile_start_L, tile_start_L.name, 4)
        self.start_tiles.extend(rotations)
        rotations = Generate_rotations(tile_start_split, tile_start_split.name, 4)
        self.start_tiles.extend(rotations)
        rotations = Generate_rotations(tile_start_pentagon, tile_start_pentagon.name, 4)
        self.start_tiles.extend(rotations)
        rotations = Generate_rotations(tile_start_crookedL, tile_start_crookedL.name, 4)
        self.start_tiles.extend(rotations)
        self.start_tile = random.choice(self.start_tiles)

        '''Start tiles and rotations for mirrored versions'''
        #TODO: This code can be cleaned up further, functionized to required less copy pasting, and sourced from outside
        flipped_new_tile = CreateMirrorHorCopy(tile_start_L)
        self.start_tiles.append(flipped_new_tile)
        rotations = Generate_rotations(flipped_new_tile, flipped_new_tile.name, 4)
        self.start_tiles.extend(rotations)
        flipped_new_tile = CreateMirrorHorCopy(tile_start_crookedL)
        self.start_tiles.append(flipped_new_tile)
        rotations = Generate_rotations(flipped_new_tile, flipped_new_tile.name, 4)
        self.start_tiles.extend(rotations)

        '''Default tiles'''
        # Y=1
        tile_I = Tile(grid_x=3, grid_y=16, topm=1, botm=1, tile_type="default", name="TileObj_I")
        tile_cross = Tile(grid_x=17, grid_y=16, topm=1, botm=1, lmid=1, rmid=1, tile_type="default", name="TileObj_cross")
        tile_sideway = Tile(grid_x=31, grid_y=16, topr=1, botl=1, tile_type="default", name="TileObj_sideway")
        tile_L_toleft = Tile(grid_x=45, grid_y=16, lmid=1, botr=1, tile_type="default", name="TileObj_L_toleft")
        tile_altar = Tile(grid_x=59, grid_y=16, botm=1, tile_type="default", name="TileObj_altar")
        # Y=2
        tile_chamber = Tile(grid_x=3, grid_y=30, topm=1, botm=1, tile_type="default", name="TileObj_chamber")
        tile_bridge = Tile(grid_x=17, grid_y=30, lmid=1, rmid=1, tile_type="default", name="TileObj_bridge")
        tile_round_deadend = Tile(grid_x=31, grid_y=30, botm=1, tile_type="default", name="TileObj_round_deadend")
        tile_bot_left = Tile(grid_x=45, grid_y=30, lmid=1, botr=1, botl=1, tile_type="default", name="TileObj_bot_left")
        tile_hallway_cap = Tile(grid_x=59, grid_y=30, botm=1, tile_type="default", name="TileObj_hallway_cap")
        # Y=3
        tile_corner = Tile(grid_x=3, grid_y=44, topm=1, rmid=1, tile_type="default", name="TileObj_corner")
        tile_half_diagonal = Tile(grid_x=17, grid_y=44, lmid=1, rtop=1, tile_type="default", name="TileObj_half_diagonal")
        tile_bigroom_corner = Tile(grid_x=self.TileRelativePosToBlocksX(2), grid_y=self.TileRelativePosToBlocksY(3),
                                   topl=1, topm=1, topr=1, rtop=1, rmid=1, rbot=1, tile_type="default", name="TileObj_bigroom_corner")
        tile_bigroom_walled_entrance = Tile(grid_x=self.TileRelativePosToBlocksX(3), grid_y=self.TileRelativePosToBlocksY(3),
                                            rmid=1, ltop=1, lmid=1, lbot=1, tile_type="default", name="TileObj_bigroom_walled_entrance")
        tile_T_block = Tile(grid_x=self.TileRelativePosToBlocksX(4), grid_y=self.TileRelativePosToBlocksY(3), lmid=1, rmid=1, topm=1, tile_type="default", name="TileObj_T_block")
        # Y=4
        tile_mini_double_corner = Tile(grid_x=self.TileRelativePosToBlocksX(0), grid_y=self.TileRelativePosToBlocksY(4),
                                       topl=1, ltop=1, rbot=1, botr=1, tile_type="default", name="TileObj_mini_double_corner")
        tile_V = Tile(grid_x=self.TileRelativePosToBlocksX(1), grid_y=self.TileRelativePosToBlocksY(4),
                                topl=1, topr=1, botm=1, tile_type="default", name="TileObj_V")
        tile_bigroom_corner_entrance = Tile(grid_x=self.TileRelativePosToBlocksX(2), grid_y=self.TileRelativePosToBlocksY(4),
                                   lmid=1, rtop=1, rmid=1, rbot=1, botl=1, botm=1, botr=1, tile_type="default", name="TileObj_bigroom_corner_entrance")
        tile_bigroom_walled = Tile(grid_x=self.TileRelativePosToBlocksX(3), grid_y=self.TileRelativePosToBlocksY(4),
                                            ltop=1, lmid=1, lbot=1, tile_type="default", name="TileObj_bigroom_walled")
        tile_mini_corner = Tile(grid_x=self.TileRelativePosToBlocksX(4), grid_y=self.TileRelativePosToBlocksY(4),
                                       topl=1, ltop=1, tile_type="default", name="TileObj_mini_corner")
        # Y=5
        '''Empty tile (can't compile)'''
        self.tile_empty = Tile(grid_x=self.TileRelativePosToBlocksX(0), grid_y=self.TileRelativePosToBlocksY(5),
                               tile_type="empty", name="TileObj_empty")
        tile_pillars = Tile(grid_x=self.TileRelativePosToBlocksX(1), grid_y=self.TileRelativePosToBlocksY(5),
                      topm=1, botm=1, tile_type="default", name="TileObj_pillars")
        tile_stripes_side = Tile(grid_x=self.TileRelativePosToBlocksX(2), grid_y=self.TileRelativePosToBlocksY(5),
                                            lbot=1, rbot=1, topl=1, topr=1, tile_type="default", name="TileObj_stripes_side")
        tile_corner_humped = Tile(grid_x=self.TileRelativePosToBlocksX(3), grid_y=self.TileRelativePosToBlocksY(5),
                                   ltop=1, topm=1, tile_type="default", name="TileObj_corner_humped")
        tile_corner_humped2 = Tile(grid_x=self.TileRelativePosToBlocksX(4), grid_y=self.TileRelativePosToBlocksY(5),
                                ltop=1, topr=1, tile_type="default", name="TileObj_corner_humped2")
        self.default_tiles = [tile_I, tile_cross, tile_sideway, tile_L_toleft, tile_altar,
                              tile_chamber, tile_bridge, tile_round_deadend, tile_bot_left, tile_hallway_cap,
                              tile_corner, tile_half_diagonal, tile_bigroom_corner, tile_bigroom_walled_entrance, tile_T_block,
                              tile_mini_double_corner, tile_V, tile_bigroom_corner_entrance, tile_bigroom_walled, tile_mini_corner,
                              tile_pillars, tile_stripes_side, tile_corner_humped, tile_corner_humped2]

        '''3 or 1 rotations of each tile'''
        # Y=1
        rotations = Generate_rotations(tile_altar, tile_altar.name,4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_I, tile_I.name, 2)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_sideway, tile_sideway.name, 4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_L_toleft, tile_L_toleft.name, 4)
        self.default_tiles.extend(rotations)
        # Y=2
        rotations = Generate_rotations(tile_chamber, tile_chamber.name, 2)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_bridge, tile_bridge.name, 2)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_round_deadend, tile_round_deadend.name, 4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_bot_left, tile_bot_left.name, 4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_hallway_cap, tile_hallway_cap.name, 4)
        self.default_tiles.extend(rotations)
        # Y=3
        rotations = Generate_rotations(tile_corner, tile_corner.name, 4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_half_diagonal, tile_half_diagonal.name, 4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_bigroom_corner, tile_bigroom_corner.name, 4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_bigroom_walled_entrance, tile_bigroom_walled_entrance.name, 4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_T_block, tile_T_block.name, 4)
        self.default_tiles.extend(rotations)
        # Y=4
        rotations = Generate_rotations(tile_mini_double_corner, tile_mini_double_corner.name, 2)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_V, tile_V.name, 4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_bigroom_corner_entrance, tile_bigroom_corner_entrance.name, 4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_bigroom_walled, tile_bigroom_walled.name, 4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_mini_corner, tile_mini_corner.name, 2)
        self.default_tiles.extend(rotations)
        # Y=5
        rotations = Generate_rotations(tile_pillars, tile_pillars.name, 2)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_stripes_side, tile_stripes_side.name, 4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_corner_humped, tile_corner_humped.name, 4)
        self.default_tiles.extend(rotations)
        rotations = Generate_rotations(tile_corner_humped2, tile_corner_humped2.name, 4)
        self.default_tiles.extend(rotations)

        #TODO: Intergrate rotations and flipping into tile creation to get rid of this shit
        '''Mirrored defaults and their rotations'''
        # Y=1
        flipped_new_tile = CreateMirrorHorCopy(tile_sideway)
        self.default_tiles.append(flipped_new_tile)
        rotations = Generate_rotations(flipped_new_tile, flipped_new_tile.name, 4)
        self.default_tiles.extend(rotations)
        flipped_new_tile = CreateMirrorHorCopy(tile_L_toleft)
        self.default_tiles.append(flipped_new_tile)
        rotations = Generate_rotations(flipped_new_tile, flipped_new_tile.name, 4)
        self.default_tiles.extend(rotations)
        # Y=2
        flipped_new_tile = CreateMirrorHorCopy(tile_bot_left)
        self.default_tiles.append(flipped_new_tile)
        rotations = Generate_rotations(flipped_new_tile, flipped_new_tile.name, 4)
        self.default_tiles.extend(rotations)
        # Y=3
        flipped_new_tile = CreateMirrorHorCopy(tile_half_diagonal)
        self.default_tiles.append(flipped_new_tile)
        rotations = Generate_rotations(flipped_new_tile, flipped_new_tile.name, 4)
        self.default_tiles.extend(rotations)
        # Y=4
        flipped_new_tile = CreateMirrorHorCopy(tile_bigroom_corner_entrance)
        self.default_tiles.append(flipped_new_tile)
        rotations = Generate_rotations(flipped_new_tile, flipped_new_tile.name, 4)
        self.default_tiles.extend(rotations)
        # Y=5
        flipped_new_tile = CreateMirrorHorCopy(tile_corner_humped)
        self.default_tiles.append(flipped_new_tile)
        rotations = Generate_rotations(flipped_new_tile, flipped_new_tile.name, 4)
        self.default_tiles.extend(rotations)

        flipped_new_tile = CreateMirrorHorCopy(tile_corner_humped2)
        self.default_tiles.append(flipped_new_tile)
        rotations = Generate_rotations(flipped_new_tile, flipped_new_tile.name, 4)
        self.default_tiles.extend(rotations)

TileObj = DefineTileObjects()
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
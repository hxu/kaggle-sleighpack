"""
Classes for Sleigh packing problem.
"""
MAX_X = 1000
MAX_Y = 1000
import logging

logger = logging.getLogger(__name__)


class Present(object):
    """
    A Present to be packed in the sleigh
    """
    def __init__(self, pid, dim1, dim2, dim3):
        self.pid = int(pid)
        self.x = int(dim1)  # "X" without rotation
        self.y = int(dim2)  # "Y" without rotation
        self.z = int(dim3)  # "Z" without rotation

    def __unicode__(self):
        return "Present: {}, {}, {}".format(self.x, self.y, self.z)

    def get_opposite_corner(self, x1, y1, z1=1):
        x2 = x1 + self.x - 1
        y2 = y1 + self.y - 1
        z2 = z1 + self.z - 1
        return x2, y2, z2

    def get_vertices(self, x1, y1, z1):
        """
        Given a starting x, y, and z coordinate, get the eight vertices of the Present

        Vertex convention: x1 y1 z1
                           x1 y2 z1
                           x2 y1 z1
                           x2 y2 z1
                           x1 y1 z2
                           x1 y2 z2
                           x2 y1 z2
                           x2 y2 z2
        """
        x2, y2, z2 = self.get_opposite_corner(x1, y1, z1)
        list_vertices = [
            [x1, y1, z1],
            [x1, y2, z1],
            [x2, y1, z1],
            [x2, y2, z1],
            [x1, y1, z2],
            [x1, y2, z2],
            [x2, y1, z2],
            [x2, y2, z2]
        ]
        return list_vertices


class Layer(object):
    """
    A Layer is one slice of the Sleigh containing one or more Presents.
    Presents are aligned on the z-axis on the layer at the bottom of each Present
    and extend upwards into the Sleigh.  The Layer ends at the topmost coordinate of all Presents in the layer.
    """
    def __init__(self, z=1):
        # Layer starts at (1, 1, z)
        self.x = 1
        self.y = 1
        self.z = z
        # Annotations for keeping track of the maximum extent of the Layer
        self.max_x = 1
        self.max_y = 1
        self.max_z = z
        # Cursor object
        self.cursor = LayerCursor()
        # Keys are (x, y, z) coordinates for the Present, values are the Present object
        self.presents = {}

    def place_present(self, present):
        """
        - Start at (1,1,1). Pack along y=1, z=1 until full
        - Move y = max_occupied_y. Pack until full
        - Return False if present doesn't fit on this Layer
        """
        logger.info("Placing present: {}".format(present))
        x2, y2, z2 = present.get_opposite_corner(self.cursor.x, self.cursor.y, self.z)

        if x2 > MAX_X:
            logger.info("Present doesn't fit in row, starting new row")
            # If it exceeds the MAX_X coordinate, reset cursor to new row in layer and re-position the present
            self.cursor.x = 1
            self.cursor.y = self.max_y
            x2, y2, z2 = present.get_opposite_corner(self.cursor.x, self.cursor.y, self.z)

        if y2 > MAX_Y:
            # If it exceeds the MAX_Y coordinate, then return False to indicate Present doesn't fit
            logger.info("Present doesn't fit in Layer")
            return False

        # If we can place it, add the Present to the hash
        logger.info("Placing present at {}, {}".format(self.cursor.x, self.cursor.y))
        self.presents[(self.cursor.x, self.cursor.y)] = present
        # Update the max coordinates
        if x2 > self.max_x:
            self.max_x = x2
        if y2 > self.max_y:
            self.max_y = y2
        if z2 > self.max_z:
            self.max_z = z2

        # Update the cursor
        self.cursor.x = self.max_x
        return True


class LayerCursor(object):
    """
    Cursor object for keeping track of where we are in a layer
    """
    def __init__(self):
        self.x = 1
        self.y = 1


class Sleigh(object):
    """
    A Sleigh is a collection of Layers
    """
    def __init__(self):
        # Hash of layers
        # Keys are z coordinates of the layer, values are the Layer object
        self.layers = {}
        self.max_z = 1

    def get_new_layer(self):
        pass

    def score(self):
        pass

"""
Classes for Sleigh packing problem.
"""


class Present(object):
    """
    A Present to be packed in the sleigh
    """
    def __init__(self, dim1, dim2, dim3):
        self.dim1 = dim1  # "X" without rotation
        self.dim2 = dim2  # "Y" without rotation
        self.dim3 = dim3  # "Z" without rotation

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
        x2 = x1 + int(self.dim1) - 1
        y2 = y1 + int(self.dim2) - 1
        z2 = z1 + int(self.dim3) - 1
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
        self.presents = []


class Sleigh(object):
    """
    A Sleigh is a collection of Layers
    """
    MAX_X = 1000
    MAX_Y = 1000

    def __init__(self):
        self.layers = []

    def score(self):
        pass

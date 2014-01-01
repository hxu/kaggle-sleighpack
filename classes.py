"""
Classes for Sleigh packing problem.
"""
import csv
import itertools


MAX_X = 1000
MAX_Y = 1000
NUM_PRESENTS = 1000000
import logging

logger = logging.getLogger(__name__)


def create_header():
    header = ['PresentId']
    for i in xrange(1,9):
        header += ['x' + str(i), 'y' + str(i), 'z' + str(i)]
    return header


class Present(object):
    """
    A Present to be packed in the sleigh
    """
    def __init__(self, pid, dim1, dim2, dim3, position=(1, 1, 1)):
        self.pid = int(pid)
        self.x = int(dim1)  # "X" without rotation
        self.y = int(dim2)  # "Y" without rotation
        self.z = int(dim3)  # "Z" without rotation
        self.x1 = position[0]
        self.y1 = position[1]
        self.z1 = position[2]

    def __repr__(self):
        return "Present #{}: {}, {}, {}".format(self.pid, self.x, self.y, self.z)

    def __eq__(self, other):
        """
        Compare if the present has the same id and is of the same size as other
        """
        if not isinstance(other, Present):
            raise TypeError("{} is not an instance of Present".format(other))
        return (self.pid == other.pid) and (self.dimensions == other.dimensions)

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def position(self):
        return self.x1, self.y1, self.z1

    @position.setter
    def position(self, position):
        self.x1 = position[0]
        self.y1 = position[1]
        self.z1 = position[2]

    @property
    def x2(self):
        return self.x1 + self.x - 1

    @property
    def y2(self):
        return self.y1 + self.y - 1

    @property
    def z2(self):
        return self.z1 + self.z - 1

    @property
    def xmax(self):
        return max(self.x1, self.x2)

    @property
    def xmin(self):
        return min(self.x1, self.x2)

    @property
    def ymax(self):
        return max(self.y1, self.y2)

    @property
    def ymin(self):
        return min(self.y1, self.y2)

    @property
    def zmax(self):
        return max(self.z1, self.z2)

    @property
    def zmin(self):
        return min(self.z1, self.z2)

    @property
    def dimensions(self):
        return {self.x, self.y, self.z}

    @property
    def opposite_corner(self):
        return self.x2, self.y2, self.z2

    @property
    def vertices(self):
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
        x1, y1, z1 = self.position
        x2, y2, z2 = self.opposite_corner
        list_vertices = [
            x1, y1, z1,
            x1, y2, z1,
            x2, y1, z1,
            x2, y2, z1,
            x1, y1, z2,
            x1, y2, z2,
            x2, y1, z2,
            x2, y2, z2
        ]
        return list_vertices


def get_all_presents():
    """
    Factory function that returns a dict that contains all presents
    Keys are IDs, values are Present objects
    """
    presents_file = './data/presents.csv'
    res = {}
    logger.info('Loading all presents')
    with open(presents_file, 'rb') as presents:
        presents.readline() # skip header
        read = csv.reader(presents)
        for row in read:
            present = Present(*row)
            res[present.pid] = present
            if len(res) % 100000 == 0:
                logger.info('Loaded {} Presents'.format(len(res)))
    return res


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
        self._errors = []

    def __repr__(self):
        return "Layer at {}".format(self.z)

    def place_present(self, present):
        """
        - Start at (1,1,1). Pack along y=1, z=1 until full
        - Move y = max_occupied_y. Pack until full
        - Return False if present doesn't fit on this Layer
        """
        logger.info("Placing present: {}".format(present))
        present.position = (self.cursor.x, self.cursor.y, self.z)
        x2, y2, z2 = present.opposite_corner

        if x2 > MAX_X:
            logger.info("Present doesn't fit in row, starting new row")
            # If it exceeds the MAX_X coordinate, reset cursor to new row in layer and re-position the present
            self.cursor.x = 1
            self.cursor.y = self.max_y + 1
            # Also need to reset the maximum x
            self.max_x = 1
            present.position = (self.cursor.x, self.cursor.y, self.z)
            x2, y2, z2 = present.opposite_corner

        if y2 > MAX_Y:
            # If it exceeds the MAX_Y coordinate, then return False to indicate Present doesn't fit
            logger.info("Present doesn't fit in Layer")
            return False

        # If we can place it, add the Present to the hash
        logger.info("Placing present at {}, {}".format(self.cursor.x, self.cursor.y))
        present.position = (self.cursor.x, self.cursor.y, self.z)
        self.presents[(self.cursor.x, self.cursor.y, self.z)] = present
        # Update the max coordinates
        if x2 > self.max_x:
            self.max_x = x2
        if y2 > self.max_y:
            self.max_y = y2
        if z2 > self.max_z:
            self.max_z = z2

        # Update the cursor
        self.cursor.x = self.max_x + 1  # add 1, since coordinates indicate a filled cell in the sleigh
        return True

    def check_collisions(self):
        # Ensure that no presents overlap on the xy plane
        for p1, p2 in itertools.combinations(self.presents.values(), 2):
            overlaps = True
            if (p1.xmax < p2.xmin) or (p2.xmax < p1.xmin):
                overlaps = False
            if (p1.ymax < p2.ymin) or (p2.ymax < p1.ymin):
                overlaps = False
            if overlaps:
                self._errors.append('Present {} overlaps with present {}'.format(p1.pid, p2.pid))
                return False
        return True


class LayerCursor(object):
    """
    Cursor object for keeping track of where we are in a layer
    """
    def __init__(self):
        self.x = 1
        self.y = 1

    def __repr___(self):
        return 'Cursor at {}, {}'.format(self.x, self.y)


class Sleigh(object):
    """
    A Sleigh is a collection of Layers
    """
    def __init__(self):
        # Hash of layers
        # Keys are z coordinates of the layer, values are the Layer object
        self.layers = {}
        self.max_z = 1
        self._errors = []

    @staticmethod
    def load_from_file(filename):
        """
        Loads a sleigh from a file
        """
        sleigh = Sleigh()
        count = 0
        with open(filename, 'rb') as f:
            fcsv = csv.reader(f)
            header = fcsv.next()
            # Check that the header matches
            if header != create_header():
                raise RuntimeError('CSV header is not correct: {}'.format(header.join(', ')))
            for p in fcsv:
                pid = int(p[0])
                x1, y1, z1 = map(int, p[1:4])
                x2, y2, z2 = map(int, p[22:25])
                x = x2 - x1 + 1
                y = y2 - y1 + 1
                z = z2 - z1 + 1
                # Get the layer that the block belongs to
                layer = sleigh.layers.get(z1, None)
                if layer is None:
                    layer = Layer(z=z1)
                    sleigh.layers[z1] = layer
                # Create the present and add it to the layer
                present = Present(pid, x, y, z, (x1, y1, z1))
                layer.presents[(x1, y1, z1)] = present
                count += 1
        logger.info("Loaded {} presents into sleigh".format(count))
        return sleigh

    def add_layer(self, layer):
        # Add a layer to the layer hash and update the max_z of the Sleigh
        self.layers[layer.z] = layer
        self.max_z = layer.max_z

    def score(self):
        pass

    def check_count(self):
        # Check that there are a million presents
        return sum([len(x.presents) for x in self.layers.values()]) == NUM_PRESENTS

    def check_presents(self):
        all_presents = get_all_presents()
        sleigh_presents = itertools.chain.from_iterable([x.presents.values() for x in self.layers.values()])
        for p in sleigh_presents:
            # Check that each of the presents is the right dimension
            actual_present = all_presents[p.pid]
            if p != actual_present:
                self._errors.append('Present {} has dimensions {}, should be {}'.format(p.pid, p.dimensions, actual_present.dimensions))
                return False
            # Check that each present is in the sleigh
            vertices = [p.x1, p.x2, p.y1, p.y2]
            if max(vertices) > MAX_Y or min(vertices) < 1:
                self._errors.append('Present {} exceeds boundaries of sleigh'.format(p.pid))
                return False
        return True

    def check_collisions(self):
        # Check that layers are non-overlapping
        sorted_layers = sorted(self.layers.values(), key=lambda l: l.z)
        a, b = itertools.tee(sorted_layers)
        next(b, None)
        for l1, l2 in itertools.izip(a, b):
            if not l1.max_z < l2.z:
                self._errors.append('Layers at {} and {} overlap'.format(l1.z, l2.z))
                return False
            # Check that the boxes in each layer don't overlap
            if not l2.check_collisions():
                self._errors.append('Overlap in layer at z {}'.format(l1.z))
                return False
            # Need to also be sure to check the first layer
            if l1.z == 1:
                if not l1.check_collisions():
                    self._errors.append('Overlap in layer at z {}'.format(l1.z))
                    return False
        return True

    def check_all(self):
        return self.check_count() and self.check_presents() and self.check_collisions()

    def write(self):
        """
        Output the contents of the sleigh into a submission file
        """
        all_presents = itertools.chain.from_iterable(l.presents.values() for l in self.layers.values())
        all_presents = sorted(all_presents, key=lambda x: x.pid, reverse=True)
        for p in all_presents:
            vertices = p.vertices
            yield [p.pid] + vertices

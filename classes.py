"""
Classes for Sleigh packing problem.
"""
import csv
import itertools
import collections
import math


MAX_X = 1000
MAX_Y = 1000
NUM_PRESENTS = 1000000
import logging

logger = logging.getLogger('Sleighpack')
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
# Log to console
logstream = logging.StreamHandler()
logstream.setLevel(logging.INFO)
logstream.setFormatter(log_formatter)

logger.addHandler(logstream)


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
        self.update_opposite_corner()
        self.update_extents()
        self.dimensions = {self.x, self.y, self.z}

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
        self.update_opposite_corner()
        self.update_extents()

    def update_opposite_corner(self):
        self.x2 = self.x1 + self.x - 1
        self.y2 = self.y1 + self.y - 1
        self.z2 = self.z1 + self.z - 1
        self.opposite_corner = self.x2, self.y2, self.z2

    def update_extents(self):
        self.xmax = max(self.x1, self.x2)
        self.xmin = min(self.x1, self.x2)
        self.ymax = max(self.y1, self.y2)
        self.ymin = min(self.y1, self.y2)
        self.zmax = max(self.z1, self.z2)
        self.zmin = min(self.z1, self.z2)

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

    def contains_xy(self, otherPresent):
        """
        Checks on the x,y plane if otherPresent is fully contained in this present
        """
        return otherPresent.xmin >= self.xmin and otherPresent.ymin >= self.ymin and \
               otherPresent.xmax <= self.xmax and otherPresent.ymax <= self.ymax

    def overlaps_xy(self, otherPresent):
        """
        Checks on the x,y plane if otherPresent overlaps with this present
        """
        overlaps = True
        if (self.xmax < otherPresent.xmin) or (otherPresent.xmax < self.xmin):
            overlaps = False
        if (self.ymax < otherPresent.ymin) or (otherPresent.ymax < self.ymin):
            overlaps = False
        if overlaps:
            return True
        return False

    def rotate_xy(self):
        """
        Rotates the present along the z-axis.  Basically swaps x and y lengths
        """
        x = self.x
        self.x = self.y
        self.y = x

        self.update_opposite_corner()
        self.update_extents()

    def rotate_shortest_z(self):
        """
        Rotates the present so that the z dimension is the shortest
        """
        # One of the other dimensions is shorter than z
        if not (self.z < self.y and self.z < self.x):
            if self.x < self.y:
                x = self.x
                self.x = self.z
                self.z = x
            else:
                y = self.y
                self.y = self.z
                self.z = y
            self.update_opposite_corner()
            self.update_extents()


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

    @property
    def height(self):
        return self.max_z - self.z + 1

    @property
    def n_presents(self):
        return len(self.presents)

    def place_present(self, present):
        """
        - Start at (1,1,1). Pack along y=1, z=1 until full
        - Move y = max_occupied_y. Pack until full
        - Return False if present doesn't fit on this Layer
        """
        logger.debug("Placing present: {}".format(present))
        present.position = (self.cursor.x, self.cursor.y, self.z)
        x2, y2, z2 = present.opposite_corner

        if x2 > MAX_X:
            logger.debug("Present doesn't fit in row, starting new row")
            # If it exceeds the MAX_X coordinate, reset cursor to new row in layer and re-position the present
            self.cursor.x = 1
            self.cursor.y = self.max_y + 1
            # Also need to reset the maximum x
            self.max_x = 1
            present.position = (self.cursor.x, self.cursor.y, self.z)
            x2, y2, z2 = present.opposite_corner

        if y2 > MAX_Y:
            # If it exceeds the MAX_Y coordinate, then return False to indicate Present doesn't fit
            logger.debug("Present doesn't fit in Layer")
            return False

        # If we can place it, add the Present to the hash
        logger.debug("Placing present at {}, {}".format(self.cursor.x, self.cursor.y))
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
        # This is really slow right now
        # Ensure that no presents overlap on the xy plane
        for p1, p2 in itertools.combinations(self.presents.values(), 2):
            if p1.overlaps_xy(p2):
                logger.info('Present {} overlaps with present {}'.format(p1.pid, p2.pid))
                self._errors.append('Present {} overlaps with present {}'.format(p1.pid, p2.pid))
                return False
        return True

    def flip_layer(self):
        """
        Flip the layer along the x,y plane.
        Used for loading top down, when the z on the layer == 1
        """
        presents = self.presents.items()
        self.presents.clear()
        for coords, present in presents:
            new_coords = (coords[0], coords[1], present.z1 - present.z - 1)
            present.position = new_coords
            self.presents[new_coords] = present

        # update the z and the max_z
        self.z = -1 * self.max_z
        self.max_z = -1

    def reposition_at_z(self, new_z):
        """
        Shifts all presents to a new z index
        """
        presents = self.presents.items()
        self.presents.clear()
        diff = new_z - self.z
        for coords, present in presents:
            new_coords = (coords[0], coords[1], coords[2] + diff)
            present.position = new_coords
            self.presents[new_coords] = present

        self.max_z = self.max_z + diff
        self.z = new_z

    def z_shift_by_diff(self, diff):
        presents = self.presents.items()
        self.presents.clear()
        for coords, present in presents:
            new_coords = (coords[0], coords[1], coords[2] + diff)
            present.position = new_coords
            self.presents[new_coords] = present

        self.max_z += diff
        self.z += diff


class MaxRectsLayer(Layer):
    """
    Layer that places presents based on the MaxRects algorithm
    """
    def __init__(self):
        super(MaxRectsLayer, self).__init__()
        first_free_rect = Present(-1, 1000, 1000, 0)
        self._free_rectangles = [first_free_rect]

    def place_present(self, present):
        """
        Decide which free rectangle to pack into
            - If no rectangle, start a new bin
        Pack the present into the chosen rectangle
        Split the remaining free space into two children free rectangles and add the free rectangles to the list
        For each free rectangle, check if the placed present intersects with it
            - If it does intersect, then split the free rectangle, and add them to the list
        Prune the list of free rectangles (check if any free rectangles are fully contained by other free rectangles
        """
        logger.debug("Placing present: {}".format(present))
        free_rect = self.choose_free_rectangle(present)
        if free_rect is None:
            # Layer is full
            logger.debug("Present doesn't fit in Layer")
            return False

        # Place the present
        logger.debug("Placing present at {}, {}".format(free_rect.position[0], free_rect.position[1]))
        present.position = free_rect.position
        self.presents[present.position] = present
        if present.zmax > self.max_z:
            self.max_z = present.zmax

        if present.xmax > MAX_X or present.ymax > MAX_Y:
            logger.warn("Present {} exceeds bounds of layer".format(present.pid))

        # Iterate over the free rectangles to check for splits
        # Keep only rectangles that do not overlap and new rectangles created from splits
        new_rectangles = []
        for i, rect in enumerate(self._free_rectangles):
            if present.overlaps_xy(rect):
                new_rectangles += self.split_rectangle(rect, present)
            else:
                new_rectangles.append(rect)

        # Prune the rectangles
        self._free_rectangles = self.prune_rectangles(new_rectangles)
        return True

    def choose_free_rectangle(self, present):
        """
        Decides which free rectangle to put the present into.  Returns the free rectangle
        We use the bottom left rule
        """
        chosen_rect = None
        best_y = 1001
        for rect in self._free_rectangles:
            # Place as is and see if it'll fit
            first_y = self.place_present_in_rectangle(present, rect)
            if first_y is not False and first_y < best_y:
                best_y = first_y
                chosen_rect = rect

            # Rotate and place and see if it'll fit
            present.rotate_xy()
            second_y = self.place_present_in_rectangle(present, rect)
            if second_y is not False and second_y < best_y:
                best_y = second_y
                chosen_rect = rect
            else:
                # Otherwise be sure to rotate the present back
                present.rotate_xy()
        return chosen_rect

    def place_present_in_rectangle(self, present, rectangle):
        """
        Tries to place the present in the rectangle.
        Returns False if it doesn't fit.  Otherwise returns the new maximum y coordinate
        """
        present.position = rectangle.position
        # Check if it fits
        if present.ymax > rectangle.ymax or present.xmax > rectangle.xmax:
            return False
        # If it does, return the ymax
        return present.ymax

    def prune_rectangles(self, rectangles):
        """
        Takes a list of rectangles, and returns a new list, removing rectangles that are fully encompassed by others
        """
        new_rects = []
        for r1 in rectangles:
            contained = False
            for r2 in rectangles:
                if r1.xmin > r2.xmax or r1.xmax < r2.xmin or r1.ymin > r2.ymax or r1.ymax < r2.ymin:
                    continue
                if (r1.x1, r1.y1, r1.x2, r1.y2) == (r2.x1, r2.y1, r2.x2, r2.y2):
                    continue
                # Apparently faster than doing the method call
                if (r1.xmin >= r2.xmin and r1.ymin >= r2.ymin) and \
                        (r1.xmax <= r2.xmax and r1.ymax <= r2.ymax):
                    contained = True
                    break
            if not contained:
                new_rects.append(r1)
        logger.debug("Pruned {} rectangles".format(len(rectangles) - len(new_rects)))
        return new_rects

    def split_rectangle(self, rectangle, present):
        """
        Given a rectangle and a present that overlaps with the rectangle, split the rectangle into at most four new MaxRects
        """
        new_rects = []
        # Check left
        if rectangle.xmin < present.xmin < rectangle.xmax:
            # Create new rectangle to the left
            new_x = present.xmin - rectangle.xmin
            new_rect = Present(-1, new_x, rectangle.y, 0, position=rectangle.position)
            new_rects.append(new_rect)

        # Check right
        if rectangle.xmin < present.xmax < rectangle.xmax:
            new_x = rectangle.xmax - present.xmax
            new_x_pos = rectangle.xmax - new_x + 1
            new_rect = Present(-1, new_x, rectangle.y, 0, position=(new_x_pos, rectangle.y1, rectangle.z1))
            new_rects.append(new_rect)

        # Check top
        if rectangle.ymin < present.ymax < rectangle.ymax:
            new_y = rectangle.ymax - present.ymax
            new_y_pos = rectangle.ymax - new_y + 1
            new_rect = Present(-1, rectangle.x, new_y, 0, position=(rectangle.x1, new_y_pos, rectangle.z1))
            new_rects.append(new_rect)

        # Check bottom
        if rectangle.ymax > present.ymin > rectangle.ymin:
            new_y = present.ymin - rectangle.ymin
            new_rect = Present(-1, rectangle.x, new_y, 0, position=rectangle.position)
            new_rects.append(new_rect)

        return new_rects


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
    def score(self):
        # Get a list of the presents from top to bottom
        logger.info("Scoring the Sleigh")
        logger.info("Building list of presents")
        presents_by_z = {}
        all_presents = itertools.chain.from_iterable(l.presents.values() for l in self.layers.values())
        for p in all_presents:
            if p.zmax not in presents_by_z:
                presents_by_z[p.zmax] = set()
            presents_by_z[p.zmax].add(p.pid)

        # Now go from top to bottom, counting each of the presents along the way
        # This is to get the order term of the metric
        logger.info("Scanning list to computer the order term")
        order_term = 0
        n_presents = 0
        for z in sorted(presents_by_z.keys(), reverse=True):
            current_presents = list(presents_by_z[z])
            current_presents.sort()
            for i in xrange(len(current_presents)):
                n_presents += 1
                order_term += math.fabs(n_presents - current_presents[i])

        # Finally, calculate the metric
        height_term = max(presents_by_z.keys())
        metric = 2 * height_term + order_term
        print '{} = 2 * height term: {} + order term: {}'.format(metric, height_term, order_term)
        return metric


class LayerSleigh(Sleigh):
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
        sleigh = LayerSleigh()
        count = 0
        with open(filename, 'rb') as f:
            fcsv = csv.reader(f)
            header = fcsv.next()
            # Check that the header matches
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
        count = len(self.layers)
        if (count % 100) == 0:
            logger.info("Layer # {} with {} presents added to the sleigh. New max z is {}".format(count, layer.n_presents, self.max_z))

    def check_count(self):
        # Check that there are a million presents
        logger.info("Checking that the number of presents is correct")
        return sum([len(x.presents) for x in self.layers.values()]) == NUM_PRESENTS

    def check_presents(self):
        logger.info("Checking that the presents are the correct dimension and in the sleigh")
        all_presents = get_all_presents()
        sleigh_presents = itertools.chain.from_iterable([x.presents.values() for x in self.layers.values()])
        starting_length = len(self._errors)
        for p in sleigh_presents:
            # Check that each of the presents is the right dimension
            actual_present = all_presents[p.pid]
            if p != actual_present:
                self._errors.append('Present {} has dimensions {}, should be {}'.format(p.pid, p.dimensions, actual_present.dimensions))
            # Check that each present is in the sleigh
            vertices = [p.x1, p.x2, p.y1, p.y2]
            if max(vertices) > MAX_Y or min(vertices) < 1:
                self._errors.append('Present {} exceeds boundaries of sleigh'.format(p.pid))
        if starting_length < len(self._errors):
            return False
        else:
            return True

    def check_collisions(self):
        # This needs to be improved since it assumes that presents don't exceed the bounds of the Layer
        # Can use the method in MetricCalculation
        logger.info("Checking for collisions")
        sorted_layers = sorted(self.layers.values(), key=lambda l: l.z)
        a, b = itertools.tee(sorted_layers)
        next(b, None)
        for l1, l2 in itertools.izip(a, b):
            # Check that layers are non-overlapping
            logger.debug("Checking overlap in layers {} and {}".format(l1, l2))
            if not l1.max_z < l2.z:
                self._errors.append('Layers at {} and {} overlap'.format(l1.z, l2.z))
                return False
            # Check that the boxes in each layer don't overlap
            if l1.z == 1:
                # Need to also be sure to check the first layer
                logger.debug("Checking collisions in layer {}".format(l1))
                if not l1.check_collisions():
                    self._errors.append('Overlap in layer at z {}'.format(l1.z))
                    return False
            logger.debug("Checking collisions in layer {}".format(l2))
            if not l2.check_collisions():
                self._errors.append('Overlap in layer at z {}'.format(l1.z))
                return False

        return True

    def check_all(self):
        # Don't check in layer collisions because it's too slow at the moment
        return self.check_count() and self.check_presents()

    def output_presents(self, descending=True):
        """
        Output the contents of the sleigh into a submission file
        """
        all_presents = itertools.chain.from_iterable(l.presents.values() for l in self.layers.values())
        all_presents = sorted(all_presents, key=lambda x: x.pid, reverse=descending)
        for p in all_presents:
            vertices = p.vertices
            yield [p.pid] + vertices

    def write_to_file(self, outfile):
        logger.info("Writing output file")
        count = 0
        with open(outfile, 'wb') as out:
            write = csv.writer(out)
            write.writerow(create_header())
            for row in self.output_presents():
                write.writerow(row)
                count += 1
        logger.info("{} presents written to file".format(count))


class ReverseLayerSleigh(LayerSleigh):
    """
    Same as LayerSleigh, but stacks layers into -z axis
    """
    def __init__(self):
        super(ReverseLayerSleigh, self).__init__()
        self.min_z = 0

    def add_layer(self, layer):
        # The layer currently occupies -1, layer.z
        # Need to push it down
        new_z = self.min_z - layer.height
        layer.reposition_at_z(new_z)
        self.layers[layer.z] = layer
        self.min_z = new_z
        count = len(self.layers)
        if (count % 100) == 0:
            logger.info("Layer # {} with {} presents added to the sleigh. New min z is {}".format(count, layer.n_presents, self.min_z))

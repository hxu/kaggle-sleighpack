from classes import logger
import classes
import os
import csv
import itertools
from libcpp.set cimport set
from libcpp.vector cimport vector

MAX_X = 1000
MAX_Y = 1000
NUM_PRESENTS = 1000000


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
        self.x2 = self.y2 = self.z2 = 0
        self.update_opposite_corner()
        self.update_extents()
        self.dimensions = {self.x, self.y, self.z}

    def __repr__(self):
        return "Present #{}: {}, {}, {}".format(self.pid, self.x, self.y, self.z)

    def __eq__(self, other):
        return (self.pid == other.pid)

    def __ne__(self, other):
        return not (self.pid == other.pid)

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

        def __del__(self):
            pass

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
        cdef int x
        x = self.x
        self.x = self.y
        self.y = x

        self.update_opposite_corner()
        self.update_extents()

    def rotate_shortest_z(self):
        """
        Rotates the present so that the z dimension is the shortest
        """
        cdef int x, y
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
        cdef int diff

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


class MaxRectsLayerCython(Layer):
    """
    Layer that places presents based on the MaxRects algorithm
    """

    def __init__(self):
        super(MaxRectsLayerCython, self).__init__()
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
        cdef int best_y

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
        cdef int new_x, new_y, new_y_pos, new_x_pos
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


class Packing(object):
    sleigh_class = classes.LayerSleigh
    infile = 'presents_revorder.csv'
    outfile = 'foo.csv'

    def __init__(self):
        self.sleigh = self.sleigh_class()

    def check(self):
        if not self.sleigh.check_all():
            logger.error('There is an error in the Sleigh')

    def write(self):
        self.sleigh.write_to_file(self.outfile)

    def score(self):
        return self.sleigh.score()


class LayerPacking(Packing):
    layer_class = classes.Layer
    log_at = 100000

    def run(self, check=True, write=True):
        cdef int counter
        cdef str presents_file, outfile

        layer = self.layer_class()

        presents_file = os.path.join('data', self.infile)
        outfile = os.path.join('data', self.outfile)
        logger.info("Reading and placing presents")
        counter = 0
        with open(presents_file, 'rb') as presents:
            presents.readline()  # skip header
            read = csv.reader(presents)
            for row in read:
                present = Present(*row)
                layer = self.process_present(present, layer)
                counter += 1
                if counter % self.log_at == 0:
                    logger.info("Placed {} presents".format(counter))

            self.process_last_layer(layer)

        logger.info("Finished placing presents")

        if write:
            self.write()

        if check:
            self.check()
        return self


class TopDownLayerPacking(LayerPacking):
    sleigh_class = classes.ReverseLayerSleigh
    layer_class = classes.Layer
    infile = 'presents.csv'
    outfile = 'sub_topdown_2.csv'

    def process_present(self, present, layer):
        if not layer.place_present(present):
            # Flip the layer
            layer.flip_layer()
            self.sleigh.add_layer(layer)
            layer = self.layer_class()
            layer.place_present(present)
        return layer

    def process_last_layer(self, layer):
        cdef int diff

        layer.flip_layer()
        self.sleigh.add_layer(layer)
        # Now need to shift everything up
        diff = -1 * (self.sleigh.min_z - 1)
        layers = self.sleigh.layers.items()
        self.sleigh.layers.clear()
        for z, layer in layers:
            layer.z_shift_by_diff(diff)
            self.sleigh.layers[layer.z] = layer


class TopDownMaxRect(TopDownLayerPacking):
    # Needs about 3G of ram because all of the MaxRects are not destroyed when the layer is added to the sleigh
    sleigh_class = classes.ReverseLayerSleigh
    layer_class = MaxRectsLayerCython
    infile = 'presents.csv'
    outfile = 'sub_topdown_3.csv'
    log_at = 10000

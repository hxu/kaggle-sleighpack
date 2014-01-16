"""
Packing algorithms
"""
import csv
import os
import classes
from classes import create_header, logger


def sample_bottom_up(infile='presents_revorder.csv', outfile='sub_bottomup_1.csv', write=True, check=True):
    """
    Replicate the sample bottom-up approach
    """
    sleigh = classes.LayerSleigh()
    layer = classes.Layer()

    presents_file = os.path.join('data', infile)
    outfile = os.path.join('data', outfile)
    logger.info("Reading and placing presents")
    with open(presents_file, 'rb') as presents:
            presents.readline()  # skip header
            read = csv.reader(presents)
            for row in read:
                present = classes.Present(*row)
                if not layer.place_present(present):
                    # Can't place the present on the layer, so close the layer and start a new one
                    sleigh.add_layer(layer)
                    layer = classes.Layer(z=sleigh.max_z + 1)
                    res = layer.place_present(present)
            # Add the final layer
            sleigh.add_layer(layer)

    if check and not sleigh.check_all():
        logger.error('There is an error in the Sleigh')
        return sleigh

    if write:
        sleigh.write_to_file(outfile)
    return sleigh


def align_presents_to_layer_top(layer):
    """
    Given a Layer object, align all of the presents so that they are flush with the top of the layer
    """
    top = layer.max_z
    presents = layer.presents.items()
    layer.presents.clear()
    for coords, present in presents:
        new_z = top - present.z + 1
        new_coords = (coords[0], coords[1], new_z)
        present.position = new_coords
        layer.presents[new_coords] = present
    return layer


def sample_top_down(infile='presents_revorder.csv', outfile='sub_topdown_1.csv', write=True, check=True):
    """
    Replicate the MatLab top-down approach

    Strategy is basically the same as bottom_up, but before closing each layer,
    align all of the presents to the top of the layer.

    Actually this strategy is not quite the same, since it reads the present in a different order.
    Result is a slightly higher score than the benchmark
    """
    sleigh = classes.LayerSleigh()
    layer = classes.Layer()

    presents_file = os.path.join('data', infile)
    outfile = os.path.join('data', outfile)
    logger.info("Reading and placing presents")
    with open(presents_file, 'rb') as presents:
            presents.readline()  # skip header
            read = csv.reader(presents)
            for row in read:
                present = classes.Present(*row)
                if not layer.place_present(present):
                    # Can't place the present on the layer, so close the layer and start a new one
                    # Before closing, re-align all of the presents in the layer to the top of the layer
                    align_presents_to_layer_top(layer)
                    sleigh.add_layer(layer)
                    layer = classes.Layer(z=sleigh.max_z + 1)
                    res = layer.place_present(present)
            # Add the final layer
            align_presents_to_layer_top(layer)
            sleigh.add_layer(layer)

    if check and not sleigh.check_all():
        logger.error('There is an error in the Sleigh')
        return sleigh

    if write:
        sleigh.write_to_file(outfile)
    return sleigh


class Packing(object):
    sleigh_class = classes.LayerSleigh
    layer_class = classes.Layer
    infile = 'presents_revorder.csv'
    outfile = 'foo.csv'
    log_at = 100000

    def __init__(self):
        self.sleigh = self.sleigh_class()

    def check(self):
        if not self.sleigh.check_all():
            logger.error('There is an error in the Sleigh')

    def write(self):
        self.sleigh.write_to_file(self.outfile)

    def score(self):
        return self.sleigh.score()

    def run(self, check=True, write=True):
        layer = self.layer_class()

        presents_file = os.path.join('data', self.infile)
        outfile = os.path.join('data', self.outfile)
        logger.info("Reading and placing presents")
        counter = 0
        with open(presents_file, 'rb') as presents:
            presents.readline()  # skip header
            read = csv.reader(presents)
            for row in read:
                present = classes.Present(*row)
                layer = self.process_present(present, layer)
                counter += 1
                if counter % self.log_at == 0:
                    logger.info("Placed {} presents".format(counter))

            self.process_last_layer(layer)

        logger.info("Finished placing presents")

        if check:
            self.check()

        if write:
            self.write()
        return self

    def process_last_layer(self, layer):
        align_presents_to_layer_top(layer)
        self.sleigh.add_layer(layer)

    def process_present(self, present, layer):
        if not layer.place_present(present):
            align_presents_to_layer_top(layer)
            self.sleigh.add_layer(layer)
            layer = classes.Layer(z=self.sleigh.max_z + 1)
            layer.place_present(present)
        return layer


class TopDownPacking(Packing):
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
        layer.flip_layer()
        self.sleigh.add_layer(layer)
        # Now need to shift everything up
        diff = -1 * (self.sleigh.min_z - 1)
        layers = self.sleigh.layers.items()
        self.sleigh.layers.clear()
        for z, layer in layers:
            layer.z_shift_by_diff(diff)
            self.sleigh.layers[layer.z] = layer


class TopDownPackingRotateZ(TopDownPacking):
    sleigh_class = classes.ReverseLayerSleigh
    layer_class = classes.Layer
    infile = 'presents.csv'
    outfile = 'sub_topdown_5.csv'

    def process_present(self, present, layer):
        # Rotate the present so that it's z is smallest
        present.rotate_shortest_z()
        if not layer.place_present(present):
            # Flip the layer
            layer.flip_layer()
            self.sleigh.add_layer(layer)
            layer = self.layer_class()
            layer.place_present(present)
        return layer


class TopDownMaxRect(TopDownPacking):
    sleigh_class = classes.ReverseLayerSleigh
    layer_class = classes.MaxRectsLayer
    infile = 'presents.csv'
    outfile = 'sub_topdown_3.csv'
    log_at = 10000


class TopDownMaxRectShortestZ(TopDownPacking):
    """
    TopDownMaxRect, but ensuring that the shortest dimension is the z-dimension before placing into the layer
    """
    sleigh_class = classes.ReverseLayerSleigh
    layer_class = classes.MaxRectsLayer
    infile = 'presents.csv'
    outfile = 'sub_topdown_4.csv'
    log_at = 10000

    def process_present(self, present, layer):
        # Rotate the present so that it's z is smallest
        present.rotate_shortest_z()
        if not layer.place_present(present):
            # Flip the layer
            layer.flip_layer()
            self.sleigh.add_layer(layer)
            layer = self.layer_class()
            layer.place_present(present)
        return layer

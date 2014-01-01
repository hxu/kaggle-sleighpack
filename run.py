"""
Packing algorithms
"""
import csv
import os
import classes
from classes import create_header
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    Actually this strategy is not quite the same, since it reads the presnt in a different order.
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

"""
Packing algorithms
"""
import csv
import os
import classes
import logging

logger = logging.getLogger(__name__)


def create_header():
    header = ['PresentId']
    for i in xrange(1,9):
        header += ['x' + str(i), 'y' + str(i), 'z' + str(i)]
    return header


def sample_bottom_up(outfile='sub_bottomup_1.csv'):
    """
    Replicate the sample bottom-up approach
    """
    sleigh = classes.Sleigh()
    layer = classes.Layer()

    presents_file = './data/presents_revorder.csv'
    outfile = os.path.join('data', outfile)
    logger.info("Reading and placing presents")
    with open(presents_file, 'rb') as presents:
            presents.readline() # skip header
            read = csv.reader(presents)
            for row in read:
                present = classes.Present(*row)
                if not layer.place_present(present):
                    # Can't place the present on the layer, so close the layer and start a new one
                    sleigh.add_layer(layer)
                    layer = classes.Layer(z=sleigh.max_z)
                    res = layer.place_present(present)
                    if not res:
                        import ipdb; ipdb.set_trace()

    logger.info("Writing output file")
    import ipdb; ipdb.set_trace()
    with open(outfile, 'wb') as out:
        write = csv.writer(out)
        write.writerow(create_header())
        for row in sleigh.write():
            write.writerow(row)


def sample_top_down():
    """
    Replicate the MatLab top-down approach
    """
    pass

"""
Packing algorithms
"""
import csv
import os
import classes
import logging


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

    presents_file = './data/presents_revorder.csv'
    outfile = os.path.join('data', outfile)
    with open(presents_file, 'rb') as presents:
        with open(outfile, 'wb') as out:
            presents.readline() # skip header
            read = csv.reader(presents)
            write = csv.writer(out)
            write.writerow(create_header())
            for row in read:
                present = classes.Present(*row)
                pass


def sample_top_down():
    """
    Replicate the MatLab top-down approach
    """
    pass

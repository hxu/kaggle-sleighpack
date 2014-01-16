import os
from classes import logger
import csv
import classes

infile = 'presents_short.csv'

layer = classes.Layer()

presents_file = os.path.join('data', infile)
logger.info("Reading and placing presents")
with open(presents_file, 'rb') as presents:
    presents.readline()  # skip header
    read = csv.reader(presents)
    for row in read:
        present = classes.Present(*row)
        if not layer.place_present(present):
            break


areas = []
presents_file = os.path.join('data', infile)
logger.info("Reading and placing presents")
with open(presents_file, 'rb') as presents:
        presents.readline()  # skip header
        read = csv.reader(presents)
        for row in read:
            present = classes.Present(*row)
            areas.append((present.pid, present.x * present.y))

import math
bucketed_areas = {}
this_bucket = 0
bucket_areas = []
for pid, area in areas:
    bucket = math.trunc(pid / 100000.0) * 100000
    if not bucket == this_bucket:
        bucketed_areas[this_bucket] = bucket_areas
        bucket_areas = []
        this_bucket = bucket
    bucket_areas.append(area)

# Test shortest_z rotation
infile = 'presents_short.csv'
presents_file = os.path.join('data', infile)
logger.info("Reading and placing presents")
with open(presents_file, 'rb') as presents:
        presents.readline()  # skip header
        read = csv.reader(presents)
        for row in read:
            present = classes.Present(*row)
            dims = present.dimensions
            print "Before rotation, shortest dim is {}, z is {}".format(min(present.x, present.y, present.z), present.z)
            present.rotate_shortest_z()
            assert min(present.x, present.y, present.z) == present.z, "After rotation, shortest dimension is not z on present {}".format(present)
            assert dims == present.dimensions, "Dimensions differ before and after rotation"

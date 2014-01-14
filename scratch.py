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

# Pure python implementation

import classes
import run
a = run.TopDownMaxRect()
a.infile = 'presents_short.csv'
%timeit -n1 -r1 a.run(check=False, write=False)

# 2014-01-20 01:48:53 - run - INFO - Reading and placing presents
# 2014-01-20 01:49:14 - run - INFO - Placed 10000 presents
# 2014-01-20 01:49:14 - run - INFO - Finished placing presents
# 1 loops, best of 1: 20.9 s per loop

# Cython
import pyximport; pyximport.install()
import maxrect_cython as run
a = run.TopDownMaxRect()
a.infile = 'presents_short.csv'
%timeit -n1 -r1 a.run(check=False, write=False)

# Just from moving objects into pyx
# 2014-01-20 02:00:13 - <magic-timeit> - INFO - Reading and placing presents
# 2014-01-20 02:00:29 - <magic-timeit> - INFO - Placed 10000 presents
# 2014-01-20 02:00:29 - <magic-timeit> - INFO - Finished placing presents
# 1 loops, best of 1: 16.3 s per loop

# manages to speed things up by 50% just by inserting some cdefs, but can't easily convert the python objects
# 2014-01-20 03:16:08 - <magic-timeit> - INFO - Reading and placing presents
# 2014-01-20 03:16:20 - <magic-timeit> - INFO - Placed 10000 presents
# 2014-01-20 03:16:20 - <magic-timeit> - INFO - Finished placing presents
# 1 loops, best of 1: 11.7 s per loop

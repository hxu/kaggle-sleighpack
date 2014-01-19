from distutils.core import setup
from Cython.Distutils import build_ext
from distutils.extension import Extension

setup(
    name = 'maxrect_cython',
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension("maxrect_cython", ["maxrect_cython.pyx"], language="c++")]
)
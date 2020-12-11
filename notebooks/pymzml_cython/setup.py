from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("read_mzml_cython.pyx")
)
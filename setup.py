from setuptools import setup, find_packages
from setuptools.extension import Extension
from Cython.Build import cythonize
import os

AMPTOOLS_HOME = os.environ["AMPTOOLS_HOME"]
ROOT_HOME = os.environ["ROOTSYS"]

amptools_extension = Extension(
        name="FitResults",
        sources=["src/amppy/fitresults/FitResults.pyx"],
        libraries=["AmpTools", "IUAmpTools", "MinuitInterface", "UpRootMinuit",
            "Physics", "MathCore", "Matrix"],
        library_dirs=["/home/nhoffman/env/gluex_top/AmpTools/AmpTools/lib", ROOT_HOME + "/lib"],
        include_dirs=[AMPTOOLS_HOME + "/AmpTools/IUAmpTools", ROOT_HOME + "/include"],
        language="c++")

setup(
    name="amppy",
    version="0.0.1",
    author="Nathaniel Dene Hoffman",
    author_email="dene@cmu.edu",
    ext_modules=cythonize(amptools_extension),
    packages=find_packages(
        where='src'
    ),
    package_dir={"": "src"},
    scripts=["src/amppy/scripts/sbatch_job.csh",
             "src/amppy/scripts/amppy_fit.py",
             "src/amppy/scripts/amppy"],
    install_requires=[
        'numpy',
        'cython',
        'enlighten',
        'simple_term_menu',
        'colorama',
        'pandas'
    ],
    zip_safe=False
)

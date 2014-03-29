from setuptools import setup

import frexp

setup(
    name='frexp',
    version=frexp.__version__,
    
    author='Jon Brandvein',
    license='MIT License',
    description='A library for running benchmark experiments',
    
    packages=['frexp'],
)

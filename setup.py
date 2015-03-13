from setuptools import setup

setup(
    name = 'frexp',
    version = '0.2.0-dev',
    url = 'https://github.com/brandjon/frexp',
    
    author = 'Jon Brandvein',
    author_email = 'jon.brandvein@gmail.com',
    license = 'MIT License',
    description = 'A framework for writing benchmark experiments',
    
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Benchmark',
    ],
    
    packages = ['frexp', 'frexp.plot'],
)

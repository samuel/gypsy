#!/usr/bin/env python

import os
from distutils.core import setup

from gypsy import __version__

# Borrowed from Django:

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
gypsy_dir = 'gypsy'

for dirpath, dirnames, filenames in os.walk(gypsy_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

setup(
    name = 'gypsy',
    version = __version__,
    description = 'Django extensions by Lefora',
    author = 'Lefora',
    author_email = 'samuel@lefora.com',
    url = 'http://github.com/samuel/gypsy/tree/master',
    packages = packages,
    data_files = data_files,
)

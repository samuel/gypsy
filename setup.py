#!/usr/bin/env python

from distutils.core import setup

setup(
    name = 'gypsy',
    version = '1.0.1',
    description = 'Django extensions by Lefora',
    author = 'Lefora',
    author_email = 'samuel@lefora.com',
    url = 'http://github.com/samuel/gypsy/tree/master',
    packages = [
        'gypsy',
        'gypsy.auth',
        'gypsy.sessions',
        'gypsy.storage',
        'gypsy.storage.backends',
        'gypsy.utils',
    ],
)

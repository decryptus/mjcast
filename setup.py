#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
from setuptools import find_packages, setup

requirements = [line.strip() for line in open('requirements.txt', 'r').readlines()]
version      = '0.1.2'

if os.path.isfile('VERSION'):
    version = open('VERSION', 'r').readline().strip() or version

setup(
    name                = 'mjcast',
    version             = version,
    description         = 'Streaming MJPEG screenshots',
    author              = 'doowan',
    author_email        = 'pypi@doowan.net',
    license             = 'License GPL-2',
    url                 = 'https://github.com/decryptus/mjcast',
    scripts             = ['bin/mjcast'],
    packages		= find_packages(),
    install_requires    = requirements,
    python_requires     = '<3',
)

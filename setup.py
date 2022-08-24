#!/usr/bin/env python
# coding: utf-8
import sys
from setuptools import setup, find_packages


requirements = [
    'Django>=3.2,<3.3',
    'djangorestframework>=3.13,<4',
    'redis'
]

dep_links = []


setup(
    name='kobo-system-account',
    version='1.0',
    description='Provide an authenticated user with superuser privileges across KoboToolbox Python apps',
    author='the kobo-system-account contributors (https://github.com/kobotoolbox/kobo-system-account/graphs/contributors)',
    url='https://github.com/kobotoolbox/kobo-system-account/',
    packages=[str(pkg) for pkg in find_packages('src')],
    package_dir={'': 'src'},
    install_requires=requirements,
    dependency_links=dep_links,
    include_package_data=True,
    zip_safe=False,
)

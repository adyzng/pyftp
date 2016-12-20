# -*- coding: utf-8 -*-

from distutils.core import setup


def get_version(relpath):
    """read version info from file without importing it"""
    from os.path import dirname, join
    for line in open(join(dirname(__file__), relpath)):
        if '__version__' in line:
            if '"' in line:
                # __version__ = "0.9"
                return line.split('"')[1]
            elif "'" in line:
                return line.split("'")[1]


setup(
	name = 'pyftp',
	version = get_version('pyftp.py'),
	author = 'huan.zhang',
	author_email = 'adyzng@gmail.com',

	py_modules = ['pyftp'],
	url = 'http://github.com/adyzng/pyftp/',
	
	keywords = 'pyftp, python ftp',
	description = 'High level ftp client wrapper based on python ftplib',

	license="Public Domain",
	classifiers=[
        'Environment :: Console',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: Utilities',
    ],
)

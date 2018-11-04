# coding=utf-8
from setuptools import setup, find_packages

from peewee_cache import __version__

setup(
    name="peewee_cache",
    version=__version__,
    description="peewee cache",
    author="purepy",
    author_email="jeova.sanctus.unus@gmail.com",
    packages=find_packages(),
    url="https://github.com/eleme/puck",
    install_requires=["gevent==1.0.2", "peewee==2.8.1", "redis==2.10.5"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
    ],
    keywords="peewee cache",
)

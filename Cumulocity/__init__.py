"""Cumulocity library for Robot Framework"""
from importlib.metadata import version, PackageNotFoundError
from .Cumulocity import Cumulocity

try:
    __version__ = version("Cumulocity")
except PackageNotFoundError:
    __version__ = "0.0.0"

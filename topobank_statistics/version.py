from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("topobank-statistics")
except PackageNotFoundError:
    __version__ = "unknown"

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("topobank-statistics")
except PackageNotFoundError:
    __version__ = "unknown"

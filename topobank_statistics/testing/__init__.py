"""Test utilities for topobank_statistics workflows.

Provides LocalTopobankContext for testing workflows without Django.

Example
-------
>>> import numpy as np
>>> from SurfaceTopography import Topography
>>> from topobank_statistics.testing import LocalTopobankContext
>>> from topobank_statistics.workflows import HeightDistribution
>>>
>>> # Create a test topography
>>> heights = np.random.randn(100, 100)
>>> topo = Topography(heights, (1.0, 1.0), unit="nm")
>>>
>>> # Create context with pre-resolved topography
>>> ctx = LocalTopobankContext(
...     path="/tmp/test-output",
...     kwargs={"bins": 50},
...     topography=topo,
... )
>>>
>>> # Execute workflow
>>> workflow = HeightDistribution()
>>> result = workflow.execute(ctx)
>>> assert "Mean Height" in result["scalars"]
"""

from pathlib import Path
from typing import Any, Union

from muflow import LocalFolderContext


class LocalTopobankContext(LocalFolderContext):
    """Local filesystem context with topography support.

    Extends LocalFolderContext with topography, topography_name, and
    topography_url properties expected by sds-workflows.
    Use this for testing workflows without Django.

    Parameters
    ----------
    path : str or Path
        Local directory path for storing files.
    kwargs : dict
        Workflow parameters.
    topography : Any
        The resolved topography data (SurfaceTopography object or surface
        container).
    topography_name : str, optional
        Display name of the topography. Default is "test-topography".
    topography_url : str, optional
        URL of the topography. Default is empty string.
    dependency_paths : dict[str, str], optional
        Mapping from dependency key to local path.
    """

    def __init__(
        self,
        path: Union[str, Path],
        kwargs: dict,
        topography: Any,
        topography_name: str = "test-topography",
        topography_url: str = "",
        dependency_paths: dict[str, str] = None,
    ):
        super().__init__(path, kwargs, dependency_paths)
        self._topography = topography
        self._topography_name = topography_name
        self._topography_url = topography_url

    @property
    def topography(self) -> Any:
        """The resolved topography data."""
        return self._topography

    @property
    def topography_name(self) -> str:
        """Display name of the topography."""
        return self._topography_name

    @property
    def topography_url(self) -> str:
        """URL of the topography."""
        return self._topography_url

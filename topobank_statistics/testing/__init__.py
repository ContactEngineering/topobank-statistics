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
>>> # Create context with pre-resolved subject
>>> ctx = LocalTopobankContext(
...     path="/tmp/test-output",
...     kwargs={"bins": 50},
...     subject=topo,
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
    """Local filesystem context with subject support.

    Extends LocalFolderContext to implement TopobankWorkflowContext protocol.
    Use this for testing workflows without Django.

    Parameters
    ----------
    path : str or Path
        Local directory path for storing files.
    kwargs : dict
        Workflow parameters.
    subject : Any
        The resolved subject data (e.g., SurfaceTopography object).
    subject_name : str, optional
        Display name of the subject. Default is "test-subject".
    subject_url : str, optional
        URL of the subject. Default is empty string.
    dependency_paths : dict[str, str], optional
        Mapping from dependency key to local path.
    """

    def __init__(
        self,
        path: Union[str, Path],
        kwargs: dict,
        subject: Any,
        subject_name: str = "test-subject",
        subject_url: str = "",
        dependency_paths: dict[str, str] = None,
    ):
        super().__init__(path, kwargs, dependency_paths)
        self._subject = subject
        self._subject_name = subject_name
        self._subject_url = subject_url

    @property
    def subject(self) -> Any:
        """The resolved subject data."""
        return self._subject

    @property
    def subject_name(self) -> str:
        """Display name of the subject."""
        return self._subject_name

    @property
    def subject_url(self) -> str:
        """URL of the subject."""
        return self._subject_url

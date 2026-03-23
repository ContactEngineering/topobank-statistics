"""Tests for TopobankWorkflowContext and LocalTopobankContext.

These tests are Django-free and test the context protocol.
"""

import numpy as np
import pytest
from topobank.analysis.context import TopobankWorkflowContext

from topobank_statistics.testing import LocalTopobankContext


class MockTopography:
    """Mock SurfaceTopography for testing without the full library."""

    def __init__(self, heights, physical_sizes, unit="m"):
        self._heights = heights
        self._physical_sizes = physical_sizes
        self.unit = unit
        self.dim = len(physical_sizes)

    def heights(self):
        return self._heights

    def rms_height_from_profile(self):
        return np.std(self._heights)

    def rms_height_from_area(self):
        return np.std(self._heights)


class TestLocalTopobankContext:
    """Tests for LocalTopobankContext."""

    def test_implements_protocol(self, tmp_path):
        """Test that LocalTopobankContext implements TopobankWorkflowContext."""
        subject = MockTopography(np.random.randn(10, 10), (1.0, 1.0))
        context = LocalTopobankContext(
            path=tmp_path,
            kwargs={"param": "value"},
            subject=subject,
        )

        # Check it's recognized as implementing the protocol
        assert isinstance(context, TopobankWorkflowContext)

    def test_subject_property(self, tmp_path):
        """Test subject property returns the provided subject."""
        subject = MockTopography(np.random.randn(10, 10), (1.0, 1.0))
        context = LocalTopobankContext(
            path=tmp_path,
            kwargs={},
            subject=subject,
        )

        assert context.subject is subject

    def test_subject_name_default(self, tmp_path):
        """Test default subject_name."""
        context = LocalTopobankContext(
            path=tmp_path,
            kwargs={},
            subject=None,
        )

        assert context.subject_name == "test-subject"

    def test_subject_name_custom(self, tmp_path):
        """Test custom subject_name."""
        context = LocalTopobankContext(
            path=tmp_path,
            kwargs={},
            subject=None,
            subject_name="My Topography",
        )

        assert context.subject_name == "My Topography"

    def test_subject_url_default(self, tmp_path):
        """Test default subject_url is empty."""
        context = LocalTopobankContext(
            path=tmp_path,
            kwargs={},
            subject=None,
        )

        assert context.subject_url == ""

    def test_subject_url_custom(self, tmp_path):
        """Test custom subject_url."""
        context = LocalTopobankContext(
            path=tmp_path,
            kwargs={},
            subject=None,
            subject_url="/topographies/123/",
        )

        assert context.subject_url == "/topographies/123/"

    def test_inherits_file_io(self, tmp_path):
        """Test that file I/O methods from LocalFolderContext work."""
        context = LocalTopobankContext(
            path=tmp_path,
            kwargs={},
            subject=None,
        )

        # Save and read JSON
        context.save_json("test.json", {"key": "value"})
        data = context.read_json("test.json")
        assert data == {"key": "value"}

    def test_inherits_kwargs(self, tmp_path):
        """Test that kwargs property from LocalFolderContext works."""
        context = LocalTopobankContext(
            path=tmp_path,
            kwargs={"bins": 50, "wfac": 5},
            subject=None,
        )

        assert context.kwargs == {"bins": 50, "wfac": 5}

    def test_inherits_storage_prefix(self, tmp_path):
        """Test that storage_prefix property works."""
        context = LocalTopobankContext(
            path=tmp_path,
            kwargs={},
            subject=None,
        )

        assert context.storage_prefix == str(tmp_path)

    def test_inherits_dependencies(self, tmp_path):
        """Test that dependency access works."""
        # Create dependency output
        dep_path = tmp_path / "dep"
        dep_path.mkdir()
        (dep_path / "data.json").write_text('{"value": 42}')

        context = LocalTopobankContext(
            path=tmp_path / "main",
            kwargs={},
            subject=None,
            dependency_paths={"my_dep": str(dep_path)},
        )

        dep_context = context.dependency("my_dep")
        data = dep_context.read_json("data.json")
        assert data == {"value": 42}


class TestWorkflowWithContext:
    """Test using LocalTopobankContext with a workflow."""

    def test_workflow_accesses_subject(self, tmp_path):
        """Test that a workflow can access the subject through context."""
        from muflows import WorkflowImplementation

        class TestWorkflow(WorkflowImplementation):
            class Meta:
                name = "test.workflow"
                display_name = "Test"

            def execute(self, context):
                topography = context.subject
                rms = topography.rms_height_from_profile()
                return {"rms_height": float(rms)}

        # Create mock topography
        heights = np.array([[1, 2], [3, 4]], dtype=float)
        subject = MockTopography(heights, (1.0, 1.0), unit="nm")

        context = LocalTopobankContext(
            path=tmp_path,
            kwargs={},
            subject=subject,
        )

        workflow = TestWorkflow()
        result = workflow.execute(context)

        assert "rms_height" in result
        assert result["rms_height"] == pytest.approx(np.std(heights))

    def test_height_distribution_execute(self, tmp_path):
        """Test HeightDistribution.execute() with LocalTopobankContext."""
        from SurfaceTopography import Topography

        from topobank_statistics.workflows import HeightDistribution

        # Create a real SurfaceTopography object
        heights = np.random.randn(64, 64)
        topography = Topography(heights, (1.0, 1.0), unit="nm")

        context = LocalTopobankContext(
            path=tmp_path,
            kwargs={"bins": 50, "wfac": 5},
            subject=topography,
            subject_name="Test Topography",
        )

        workflow = HeightDistribution()
        result = workflow.execute(context)

        # Verify result structure
        assert result["name"] == "Height distribution"
        assert "Mean Height" in result["scalars"]
        assert "RMS Height" in result["scalars"]
        assert result["xlabel"] == "Height"
        assert result["ylabel"] == "Probability density"
        assert result["xunit"] == "nm"
        assert len(result["series"]) == 2  # Distribution + Gaussian fit

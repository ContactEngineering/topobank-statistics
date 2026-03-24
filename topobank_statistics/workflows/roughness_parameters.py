"""Roughness parameters workflow."""

from muflow import WorkflowImplementation
from topobank.analysis.registry import register_implementation
from topobank.manager.models import Topography


class RoughnessParameters(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.roughness_parameters"
        display_name = "Roughness parameters"

        implementations = {
            Topography: "topography_implementation",
        }

    def topography_implementation(self, analysis, progress_recorder=None):
        """Calculate roughness parameters for given topography.

        Parameters
        ----------
        topography : topobank.manager.models.Topography
        progress_recorder : ProgressRecorder or None
        folder : str or None

        Returns
        -------
        list of dicts where each dict has keys

         quantity, e.g. 'RMS height' or 'RMS gradient'
         direction, e.g. 'x' or None
         from, e.g. 'profile (1D)' or 'area (2D)' or ''
         symbol, e.g. 'Sq' or ''
         value, a number or NaN
         unit, e.g. 'nm'
        """

        # Get low level topography from SurfaceTopography model
        topography = analysis.subject.topography()

        # noinspection PyBroadException
        try:
            unit = topography.unit
            inverse_unit = "{}⁻¹".format(unit)
        except KeyError:
            unit = None
            inverse_unit = None

        is_2D = topography.dim == 2
        if not is_2D and not (topography.dim == 1):
            raise ValueError(
                "This analysis function can only handle 1D or 2D topographies."
            )

        FROM_1D = "profile (1D)"
        FROM_2D = "area (2D)"

        #
        # RMS height
        #
        result = [
            {
                "quantity": "RMS height",
                "from": FROM_1D,
                "symbol": "Rq",
                "direction": "x",
                "value": topography.rms_height_from_profile(),
                "unit": unit,
            }
        ]
        if is_2D:
            result.extend(
                [
                    {
                        "quantity": "RMS height",
                        "from": FROM_1D,
                        "symbol": "Rq",
                        "direction": "y",
                        "value": topography.transpose().rms_height_from_profile(),
                        "unit": unit,
                    },
                    {
                        "quantity": "RMS height",
                        "from": FROM_2D,
                        "symbol": "Sq",
                        "direction": None,
                        "value": topography.rms_height_from_area(),
                        "unit": unit,
                    },
                ]
            )
        #
        # RMS curvature
        #
        if is_2D:
            result.extend(
                [
                    {
                        "quantity": "RMS curvature",
                        "from": FROM_1D,
                        "symbol": "",
                        "direction": "y",
                        "value": topography.transpose().rms_curvature_from_profile(),
                        "unit": inverse_unit,
                    },
                    {
                        "quantity": "RMS curvature",
                        "from": FROM_2D,
                        "symbol": "",
                        "direction": None,
                        "value": topography.rms_curvature_from_area(),
                        "unit": inverse_unit,
                    },
                ]
            )

        # RMS curvature in x direction is needed for 1D and 2D
        result.append(
            {
                "quantity": "RMS curvature",
                "from": FROM_1D,
                "symbol": "",
                "direction": "x",
                "value": topography.rms_curvature_from_profile(),
                "unit": inverse_unit,
            }
        )

        #
        # RMS gradient/slope
        #
        result.extend(
            [
                {
                    "quantity": "RMS slope",
                    "from": FROM_1D,
                    "symbol": "R&Delta;q",
                    "direction": "x",
                    "value": topography.rms_slope_from_profile(),  # x direction
                    "unit": 1,
                }
            ]
        )
        if is_2D:
            result.extend(
                [
                    {
                        "quantity": "RMS slope",
                        "from": FROM_1D,
                        "symbol": "R&Delta;q",  # HTML
                        "direction": "y",
                        "value": topography.transpose().rms_slope_from_profile(),  # y direction
                        "unit": 1,
                    },
                    {
                        "quantity": "RMS gradient",
                        "from": FROM_2D,
                        "symbol": "",
                        "direction": None,
                        "value": topography.rms_gradient(),
                        "unit": 1,
                    },
                ]
            )

        #
        # Bandwidth (pixel_size, scan_size), see GH #677
        #
        lower_bound, upper_bound = topography.bandwidth()
        result.extend(
            [
                {
                    "quantity": "Bandwidth: lower bound",
                    "from": FROM_2D if is_2D else FROM_1D,
                    "symbol": "",
                    "direction": None,
                    "value": lower_bound,
                    "unit": unit,
                },
                {
                    "quantity": "Bandwidth: upper bound",
                    "from": FROM_2D if is_2D else FROM_1D,
                    "symbol": "",
                    "direction": None,
                    "value": upper_bound,
                    "unit": unit,
                },
            ]
        )

        return result


register_implementation(RoughnessParameters)

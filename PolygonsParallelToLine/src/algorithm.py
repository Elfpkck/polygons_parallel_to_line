from __future__ import annotations

from typing import Any, TYPE_CHECKING

from qgis.core import (
    QgsField,
    QgsFields,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
)
from qgis.PyQt.QtCore import QMetaType  # type: ignore[import-not-found]

from .const import COLUMN_NAME
from .pptl import Params, PolygonsParallelToLine

if TYPE_CHECKING:
    from qgis.core import (
        QgsProcessingContext,
        QgsProcessingFeatureSource,
        QgsProcessingFeedback,
    )


class Algorithm(QgsProcessingAlgorithm):
    """
    Class for rotating polygons to align with lines in a vector layer.

    This class provides an implementation for a QGIS processing algorithm that rotates polygon features in a given
    vector layer to be parallel to features in another line vector layer. It includes functionality to customize
    the rotation parameters such as angle limits, distance thresholds, and handling of multipolygons.

    :ivar OUTPUT_LAYER: Output ID for the sink layer where rotated polygons will be stored.
    :type OUTPUT_LAYER: str
    :ivar LINE_LAYER: Input ID for the line vector layer used for alignment.
    :type LINE_LAYER: str
    :ivar POLYGON_LAYER: Input ID for the polygon vector layer to rotate.
    :type POLYGON_LAYER: str
    :ivar LONGEST: Parameter ID for specifying whether to use the longest polygon segment for rotation.
    :type LONGEST: str
    :ivar NO_MULTI: Parameter ID for specifying whether to exclude multipolygons from rotation.
    :type NO_MULTI: str
    :ivar DISTANCE: Parameter ID for specifying the distance threshold from the line.
    :type DISTANCE: str
    :ivar ANGLE: Parameter ID for specifying the maximum angle for rotation.
    :type ANGLE: str
    """

    OUTPUT_LAYER = "OUTPUT"
    LINE_LAYER = "LINE_LAYER"
    POLYGON_LAYER = "POLYGON_LAYER"
    LONGEST = "LONGEST"
    NO_MULTI = "NO_MULTI"
    DISTANCE = "DISTANCE"
    ANGLE = "ANGLE"

    def createInstance(self) -> Algorithm:  # noqa: N802
        return self.__class__()

    def name(self) -> str:
        return "pptl_algo"

    def displayName(self) -> str:  # noqa: N802
        return "Polygons parallel to lines"

    def group(self) -> str:
        return "Algorithms for vector layers"

    def groupId(self) -> str:  # noqa: N802
        return "pptl_group"

    def shortHelpString(self) -> str:  # noqa: N802
        return "This plugin rotates polygons parallel to the lines"

    def helpUrl(self) -> str:  # noqa: N802
        return "https://elfpkck.github.io/polygons_parallel_to_line/"

    def initAlgorithm(self, config: dict | None = None) -> None:  # noqa: N802
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LAYER,
                "Output layer with rotated polygons",
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.LINE_LAYER, "Line layer", [QgsProcessing.TypeVectorLine])
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.POLYGON_LAYER, "Polygon layer", [QgsProcessing.TypeVectorPolygon])
        )
        self.addParameter(
            QgsProcessingParameterBoolean(self.LONGEST, "Rotate by the longest segment", defaultValue=False)
        )
        self.addParameter(QgsProcessingParameterBoolean(self.NO_MULTI, "Skip multipolygons", defaultValue=False))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DISTANCE,
                "Max distance from line (in units of line layer CRS) (optional)",
                type=QgsProcessingParameterNumber.Double,
                minValue=0.0,
                defaultValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ANGLE,
                "Max angle (in degrees) for rotation (optional)",
                type=QgsProcessingParameterNumber.Double,
                minValue=0.0,
                maxValue=89.9,
                defaultValue=89.9,
            )
        )

    def _create_output_fields(self, source_layer: QgsProcessingFeatureSource) -> QgsFields:
        """
        Creates output fields by appending a specific field if it does not already exist.

        This function retrieves the fields from the input source layer, checks if a field with the specified name
        exists, and appends it if missing. The new field has a Boolean type. The resulting set of fields is then
        returned.

        :param source_layer: The input source layer from which fields are retrieved.
        :type source_layer: QgsProcessingFeatureSource
        :return: The updated fields containing the original fields and the new field, if added.
        :rtype: QgsFields
        """
        fields = source_layer.fields()
        field_idx = fields.indexFromName(COLUMN_NAME)
        if field_idx == -1:
            fields.append(QgsField(COLUMN_NAME, QMetaType.Bool))

        return fields

    def processAlgorithm(  # noqa: N802
        self, parameters: dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> dict[str, str]:
        """
        Executes the algorithm logic for processing geospatial data to create polygons parallel
        to a given line based on specified parameters.

        This function processes input geospatial layers, extracts relevant parameters, and applies
        algorithms to produce new geometries. The result is saved as a new output layer.

        :param parameters: A dictionary containing input parameters required to run the algorithm.
                           It includes input layers, boolean flags, and numerical values.
        :param context: An instance of QgsProcessingContext representing the execution context of the algorithm.
                        It provides details such as layer sources and environment settings.
        :param feedback: An instance of QgsProcessingFeedback used for logging progress, status, and errors
                         encountered during processing.
        :return: A dictionary containing the identifier of the created output layer.
        """
        polygon_layer = self.parameterAsSource(parameters, self.POLYGON_LAYER, context)
        output_fields = self._create_output_fields(polygon_layer)
        sink, dest_id = self.parameterAsSink(
            parameters=parameters,
            name=self.OUTPUT_LAYER,
            context=context,
            fields=output_fields,
            geometryType=polygon_layer.wkbType(),
            crs=polygon_layer.sourceCrs(),
        )
        params = Params(
            line_layer=self.parameterAsSource(parameters, self.LINE_LAYER, context),
            polygon_layer=polygon_layer,
            by_longest=self.parameterAsBool(parameters, self.LONGEST, context),
            no_multi=self.parameterAsBool(parameters, self.NO_MULTI, context),
            distance=self.parameterAsDouble(parameters, self.DISTANCE, context),
            angle=self.parameterAsDouble(parameters, self.ANGLE, context),
            fields=output_fields,
            sink=sink,
        )
        PolygonsParallelToLine(feedback, params).run()
        return {self.OUTPUT_LAYER: dest_id}

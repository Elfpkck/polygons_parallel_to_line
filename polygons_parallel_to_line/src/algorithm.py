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
from qgis.PyQt.QtCore import QMetaType  # type: ignore

from .pptl import Params, PolygonsParallelToLine

if TYPE_CHECKING:
    from qgis.core import (
        QgsProcessingContext,
        QgsProcessingFeatureSource,
        QgsProcessingFeedback,
    )


class Algorithm(QgsProcessingAlgorithm):
    OUTPUT_LAYER = "OUTPUT"
    LINE_LAYER = "LINE_LAYER"
    POLYGON_LAYER = "POLYGON_LAYER"
    LONGEST = "LONGEST"
    NO_MULTI = "NO_MULTI"
    DISTANCE = "DISTANCE"
    ANGLE = "ANGLE"
    COLUMN_NAME = "_rotated"

    def createInstance(self) -> Algorithm:  # noqa: N802
        return self.__class__()

    def name(self) -> str:
        return "pptl_algo"

    def displayName(self) -> str:  # noqa: N802
        return "Polygons parallel to the lines"

    def group(self) -> str:
        return "Algorithms for vector layers"

    def groupId(self) -> str:  # noqa: N802
        return "pptl_group"

    def shortHelpString(self) -> str:  # noqa: N802
        return "This plugin rotates polygons parallel to the lines"

    def initAlgorithm(self, config: dict | None = None) -> None:  # noqa: N802
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LAYER,
                "Output layer with rotated polygons",
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.LINE_LAYER, "Select line layer", [QgsProcessing.TypeVectorLine])
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POLYGON_LAYER, "Select polygon layer", [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.LONGEST,
                "Rotate by the longest segment if both angles between polygon segments and line segment <="
                " 'Angle value'",
                defaultValue=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(self.NO_MULTI, "Do not rotate multipolygons", defaultValue=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DISTANCE,
                "Distance from line",
                type=QgsProcessingParameterNumber.Double,
                minValue=0.0,
                defaultValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ANGLE,
                "Angle value",
                type=QgsProcessingParameterNumber.Double,
                minValue=0.0,
                maxValue=89.9,
                defaultValue=89.9,
            )
        )

    def _create_output_fields(self, source_layer: QgsProcessingFeatureSource) -> QgsFields:
        """
        Create output fields for the sink layer.

        Copies all fields from the source layer except the rotation field if it exists,
        then adds the rotation field to store rotation status.

        Args:
            source_layer: The source layer to copy fields from

        Returns:
            QgsFields object containing the fields for the output layer
        """
        output_fields = QgsFields()

        for field in source_layer.fields():
            if self.COLUMN_NAME == field.name():
                continue
            output_fields.append(field)

        output_fields.append(QgsField(self.COLUMN_NAME, QMetaType.Int))
        return output_fields

    def processAlgorithm(  # noqa: N802
        self, parameters: dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> dict[str, str]:
        polygon_layer = self.parameterAsSource(parameters, self.POLYGON_LAYER, context)
        output_fields = self._create_output_fields(polygon_layer)
        sink, dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_LAYER,
            context,
            output_fields,
            polygon_layer.wkbType(),
            polygon_layer.sourceCrs(),
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

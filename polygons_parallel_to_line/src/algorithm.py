from __future__ import annotations

import os
from typing import Any, Optional, TYPE_CHECKING

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
from qgis.PyQt.QtCore import QVariant  # type: ignore

from .pptl import Params, PolygonsParallelToLine

if TYPE_CHECKING:
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback


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

    def initAlgorithm(self, config: Optional[dict] = None) -> None:  # noqa: N802
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
                "Rotate by longest edge if both angles between polygon edges and line segment <= 'Angle value'",
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

    def processAlgorithm(  # noqa: N802
        self, parameters: dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> dict[str, str]:
        new_fields = QgsFields()
        polygon_layer = self.parameterAsSource(parameters, self.POLYGON_LAYER, context)
        for field in polygon_layer.fields():
            if self.COLUMN_NAME == field.name():
                continue
            new_fields.append(field)
        new_fields.append(QgsField(self.COLUMN_NAME, QVariant.Int))
        sink, dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_LAYER,
            context,
            new_fields,
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
            fields=new_fields,
            sink=sink,
        )
        PolygonsParallelToLine(feedback, params).run()

        ret = {self.OUTPUT_LAYER: dest_id}
        if os.getenv("PPTL_TEST"):  # for testing purposes
            output_layer = context.getMapLayer(dest_id)  # type: ignore
            ret["result_wkt"] = [x.geometry().asWkt() for x in output_layer.getFeatures()]  # type: ignore
            ret["_rotated"] = [1 if x[self.COLUMN_NAME] == 1 else 0 for x in output_layer.getFeatures()]  # type: ignore

        return ret

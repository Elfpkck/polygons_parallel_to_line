from __future__ import annotations

import os
from typing import Any, Optional, TYPE_CHECKING

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsFields,
    QgsField,
)

import pydevd_pycharm

from .pptl import PolygonsParallelToLine, Params
from .helpers import tr

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

    def createInstance(self):
        return self.__class__()

    def name(self):
        return "pptl_algo"

    def displayName(self):
        return tr("Polygons parallel to line")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        # TODO: add to existing group if possible
        return tr("Algorithms for vector layers")

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "examplescripts"  # TODO:

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return tr("Example algorithm short description")  # TODO:

    def initAlgorithm(self, config: Optional[dict] = None):
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LAYER,
                "Output layer with rotated polygons",
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINE_LAYER, tr("Select line layer"), [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POLYGON_LAYER, tr("Select polygon layer"), [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.LONGEST,
                tr("Rotate by longest edge if both angles between " "polygon edges and line segment <= 'Angle value'"),
                defaultValue=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(self.NO_MULTI, tr("Do not rotate multipolygons"), defaultValue=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DISTANCE,
                tr("Distance from line"),
                type=QgsProcessingParameterNumber.Double,
                minValue=0.0,
                defaultValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ANGLE,
                tr("Angle value"),
                type=QgsProcessingParameterNumber.Double,
                minValue=0.0,
                maxValue=89.9,
                defaultValue=89.9,
            )
        )

    def processAlgorithm(
        self, parameters: dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ):
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
            output_layer = context.getMapLayer(dest_id)
            ret["result_wkt"] = [x.geometry().asWkt() for x in output_layer.getFeatures()]
            ret["_rotated"] = [1 if x[self.COLUMN_NAME] == 1 else 0 for x in output_layer.getFeatures()]

        return ret


# TODO: possible to show icon in processing toolbox?

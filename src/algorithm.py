from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
)

from .pptl import Cfg, PolygonsParallelToLine

if TYPE_CHECKING:
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback


class Algorithm(QgsProcessingAlgorithm):
    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return self.__class__()

    def name(self):
        return "pptl_algo"

    def displayName(self):
        return self.tr("Polygons parallel to line")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        # TODO: add to existing group if possible
        return self.tr("Algorithms for vector layers")

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
        return self.tr("Example algorithm short description")  # TODO:

    def initAlgorithm(self, config: Optional[dict] = None):
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                Cfg.OUTPUT_LAYER,
                "Output layer with rotated polygons",
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                Cfg.LINE_LAYER, self.tr("Select line layer"), [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                Cfg.POLYGON_LAYER, self.tr("Select polygon layer"), [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                Cfg.LONGEST,
                self.tr(
                    "Rotate by longest edge if both angles between " "polygon edges and line segment <= 'Angle value'"
                ),
                defaultValue=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(Cfg.MULTI, self.tr("Do not rotate multipolygons"), defaultValue=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                Cfg.DISTANCE,
                self.tr("Distance from line"),
                type=QgsProcessingParameterNumber.Double,
                minValue=0.0,
                defaultValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                Cfg.ANGLE,
                self.tr("Angle value"),
                type=QgsProcessingParameterNumber.Double,
                minValue=0.0,
                maxValue=89.9,
                defaultValue=89.9,
            )
        )

    def processAlgorithm(
        self, parameters: dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ):
        return PolygonsParallelToLine(self, parameters, context, feedback).run()


# TODO: possible to show icon in processing toolbox?

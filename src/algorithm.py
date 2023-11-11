"""
/***************************************************************************
 PolygonsParallelToLine
                                 A QGIS plugin
 This plugin rotates polygons parallel to line
                              -------------------
        begin                : 2016-03-10
        copyright            : (C) 2016-2023 by Andrii Liekariev
        email                : elfpkck@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


__author__ = "Andrii Liekariev"
__date__ = "2016-03-10"
__copyright__ = "(C) 2016-2023 by Andrii Liekariev"

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = "$Format:%H$"


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


class Algorithm(QgsProcessingAlgorithm):
    OUTPUT_LAYER = "OUTPUT_LAYER"
    LINE_LAYER = "LINE_LAYER"
    POLYGON_LAYER = "POLYGON_LAYER"
    SELECTED = "SELECTED"
    WRITE_SELECTED = "WRITE_SELECTED"
    LONGEST = "LONGEST"
    MULTI = "MULTI"
    DISTANCE = "DISTANCE"
    ANGLE = "ANGLE"
    COLUMN_NAME = "_rotated"

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return Algorithm()

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

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                Cfg.OUTPUT_LAYER,
                "Output layer with rotated polygons",
            )
        )
        self.addParameter(  # TODO: polyline doesn't work with poly and multipoly. Check multipolyline
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
            QgsProcessingParameterBoolean(Cfg.SELECTED, self.tr("Rotate only selected polygons"), defaultValue=False)
        )
        self.addParameter(  # TODO: allow to check only when "Rotate only selected polygons" is checked
            QgsProcessingParameterBoolean(Cfg.WRITE_SELECTED, self.tr("Save only selected"), defaultValue=False)
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
        self.addParameter(  # TODO: doesn't work
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

    def processAlgorithm(self, parameters, context, feedback):
        return PolygonsParallelToLine(self, parameters, context, feedback).run()

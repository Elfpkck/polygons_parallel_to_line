# -*- coding: utf-8 -*-

"""
/***************************************************************************
 PolygonsParallelToLine
                                 A QGIS plugin
 This plugin rotates polygons parallel to line
                              -------------------
        begin                : 2017-03-16
        copyright            : (C) 2017 by Andrey Lekarev
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

__author__ = 'Andrey Lekarev'
__date__ = '2016-03-10'
__copyright__ = '(C) 2016-2017 by Andrey Lekarev'


from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QProgressBar

from qgis.core import QgsVectorFileWriter, QgsSpatialIndex, QgsGeometry
from qgis.gui import QgsMessageBar

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import (ParameterVector, ParameterBoolean,
                                        ParameterNumber)
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector



class ShowProgress():

    def __init__(self, iface, title, message, items):
        """
        Informs user about progress via progress bar at QGIS messageBar

        :param iface: a QGIS interface instance
        :param title: str bar title
        :param message: str bar message
        :param items: int number of items in bar
        """

        iface.messageBar().clearWidgets()
        progressMessageBar = iface.messageBar().createMessage(title, message)
        self.progress = QProgressBar(progressMessageBar)
        self.progress.setMaximum(items)
        progressMessageBar.layout().addWidget(self.progress)
        iface.messageBar().pushWidget(progressMessageBar)
        self.pr = 0
        self.progress.setValue(self.pr)

    def update(self, value):
        self.pr += value
        self.progress.setValue(self.pr)


class PolygonsParallelToLineAlgorithm(GeoAlgorithm):
    """This is an example algorithm that takes a vector layer and
    creates a new one just with just those features of the input
    layer that are selected.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT_LAYER = 'OUTPUT_LAYER'
    LINE_LAYER = 'LINE_LAYER'
    POLYGON_LAYER = 'POLYGON_LAYER'
    SELECTED = 'SELECTED'
    LONGEST = "LONGEST"
    DISTANCE = 'DISTANCE'
    ANGLE = 'ANGLE'

    def __init__(self, iface):
        GeoAlgorithm.__init__(self)
        self.iface = iface

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name = 'Polygons parallel to line'

        # The branch of the toolbox under which the algorithm will appear
        self.group = 'Algorithms for vector layers'

        self.addParameter(
            ParameterVector(
                self.LINE_LAYER,
                self.tr('Input line layer')
            )
        )
        self.addParameter(
            ParameterVector(
                self.POLYGON_LAYER,
                self.tr('Input polygon layer'),
                [ParameterVector.VECTOR_TYPE_POLYGON]
            )
        )
        self.addParameter(
            ParameterBoolean(
                self.SELECTED,
                self.tr('Rotate only selected polygons')
            )
        )
        self.addParameter(
            ParameterBoolean(
                self.LONGEST,
                self.tr("Rotate by longest edge if both angles between "
                        "polygon edges and line segment <= 'Angle value'")
            )
        )
        self.addParameter(
            ParameterNumber(
                self.DISTANCE,
                self.tr("Distance from line")
            )
        )
        self.addParameter(
            ParameterNumber(
                self.ANGLE,
                self.tr("Angle value"),
                maxValue=89.9
            )
        )

        # We add a vector layer as output
        self.addOutput(OutputVector(self.OUTPUT_LAYER,
            self.tr('Output layer with rotated polygons')))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        self._getInputValues()

        # Input layers vales are always a string with its location.
        # That string can be converted into a QGIS object (a
        # QgsVectorLayer in this case) using the
        # processing.getObjectFromUri() method.
        self.lineLayer = dataobjects.getObjectFromUri(self.lineLayerName)
        self.polygonLayer = dataobjects.getObjectFromUri(self.polygonLayerName)

        self._createLineSpatialIndex()
        polygons = self._getSelected() if self.isSelected else self._getAll()
        if polygons:
            for polygon in polygons:
                # if not polygon.geometry().isMultipart():
                self._rotate(polygon)

        # And now we can process

        # First we create the output layer. The output value entered by
        # the user is a string containing a filename, so we can use it
        # directly

        # settings = QSettings()
        # systemEncoding = settings.value('/UI/encoding', 'System')
        # provider = self.lineLayer.dataProvider()
        # writer = QgsVectorFileWriter(self.outputLayer, systemEncoding,
        #                              provider.fields(),
        #                              provider.geometryType(), provider.crs())

        # Now we take the features from input layer and add them to the
        # output. Method features() returns an iterator, considering the
        # selection that might exist in layer and the configuration that
        # indicates should algorithm use only selected features or all
        # of them

        # features = vector.features(self.lineLayer)
        # for f in features:
        #     writer.addFeature(f)

        # There is nothing more to do here. We do not have to open the
        # layer that we have created. The framework will take care of
        # that, or will handle it if this algorithm is executed within
        # a complex model

    def _getInputValues(self):
        self.lineLayerName = self.getParameterValue(self.LINE_LAYER)
        self.polygonLayerName = self.getParameterValue(self.POLYGON_LAYER)
        self.isSelected = self.getParameterValue(self.SELECTED)
        self.byLongest = self.getParameterValue(self.LONGEST)
        self.distance = self.getParameterValue(self.DISTANCE)
        self.angle = self.getParameterValue(self.ANGLE)
        self.outputLayer = self.getOutputValue(self.OUTPUT_LAYER)

    def _createLineSpatialIndex(self):
        self.index = QgsSpatialIndex()
        for line in self.lineLayer.getFeatures():
            self.index.insertFeature(line)

    def _getSelected(self):
        polygonsNumber = self.polygonLayer.selectedFeatureCount()
        if polygonsNumber:
            self._createProgressBar(polygonsNumber)
            return self.polygonLayer.selectedFeatures()
        else:
            self._showMsg(self.tr('You have chosen "Rotate only selected '
                                  'polygons" but there are no selected'))

    def _showMsg(self, message):
        self.iface.messageBar().pushMessage("Error", message,
                                            level=QgsMessageBar.CRITICAL)

    def _getAll(self):
        polygonsNumber = self.polygonLayer.featureCount()
        if polygonsNumber:
            self._createProgressBar(polygonsNumber)
            return self.polygonLayer.getFeatures()
        else:
            self._showMsg(self.tr("Layer does not have any polygons"))

    def _createProgressBar(self, items):
        self.progressBar = ShowProgress(self.iface, 'PolygonsParallelToLine',
                                        self.tr('Data processing...'), items)

    def _rotate(self, polygon):
        self.near_line = self._getNearestLine(polygon)

        dist = self.near_line.geometry().distance(polygon.geometry())
        if not self.distance or dist <= self.distance:
            self._simpleOrMultiGeom(polygon)


    def _getNearestLine(self, polygon):
        centroid = polygon.geometry().centroid()
        near_id = self.index.nearestNeighbor(centroid.asPoint(), 1)
        for line in self.lineLayer.getFeatures():
            if line.id() == near_id[0]:
                return line

    def _simpleOrMultiGeom(self, polygon):
        if polygon.geometry().isMultipart():
            for part in polygon.geometry().asMultiPolygon():
                self._nearestVertex(part[0])
        else:
            self._nearestVertex(polygon.geometry().asPolygon()[0])

    def _nearestVertex(self, polygonVertexes):
        vertex_to_segment_dict = {}
        for vertex in polygonVertexes[:-1]:
            vertex_geom = QgsGeometry.fromPoint(vertex)
            vertex_to_segment = vertex_geom.distance(self.near_line.geometry())
            vertex_to_segment_dict[vertex_to_segment] = vertex

        minDistance = min(vertex_to_segment_dict.keys())
        self.nearestVertex = vertex_to_segment_dict[minDistance]
        vertexIndex = polygonVertexes.index(self.nearestVertex)

        self._nearestEdges(polygonVertexes, vertexIndex)

    def _nearestEdges(self, polygonVertexes, vertexIndex):
        # if vertex is first
        if vertexIndex == 0:
            line1 = QgsGeometry.fromPolyline(
                [polygonVertexes[0], polygonVertexes[1]])
            line2 = QgsGeometry.fromPolyline(
                [polygonVertexes[0], polygonVertexes[-1]])

        # if vertex is last
        elif vertexIndex == len(polygonVertexes) - 1:
            line1 = QgsGeometry.fromPolyline(
                [polygonVertexes[-1], polygonVertexes[0]])
            line2 = QgsGeometry.fromPolyline(
                [polygonVertexes[-1], polygonVertexes[-2]])
        else:
            line1 = QgsGeometry.fromPolyline(
                [polygonVertexes[vertexIndex],
                 polygonVertexes[vertexIndex + 1]]
            )
            line2 = QgsGeometry.fromPolyline(
                [polygonVertexes[vertexIndex],
                 polygonVertexes[vertexIndex - 1]]
            )

        line1Azimuth = line1.asPolyline()[0].azimuth(line1.asPolyline()[1])
        line2Azimuth = line2.asPolyline()[0].azimuth(line2.asPolyline()[1])
        self._segmentAzimuth(line1Azimuth, line2Azimuth)

    def _segmentAzimuth(self, line1Azimuth, line2Azimuth):
        closestSegment = self.near_line.geometry().closestSegmentWithContext(
            self.nearestVertex
        )
        indexSegmEnd = closestSegment[-1]
        indexSegmStart = indexSegmEnd - 1

        for i, node in enumerate(self.near_line.geometry().asPolyline()):
            if indexSegmStart == i:
                segmStart = node
            elif indexSegmEnd == i:
                segmEnd = node
        segmentAzimuth = segmStart.azimuth(segmEnd)

        deltaAzimuth1 = self._preRotation(segmentAzimuth, line1Azimuth)
        deltaAzimuth2 = self._preRotation(segmentAzimuth, line2Azimuth)

    def _preRotation(self, segment, line):
        if (segment >= 0 and line >= 0) or (segment <= 0 and line <= 0):
            delta = segment - line
            if segment > line and abs(delta) > 90:
                delta = delta - 180
            elif segment < line and abs(delta) > 90:
                delta = delta + 180

        if 90 >= segment >= 0 and line <= 0:
            delta = segment + abs(line)
            if delta > 90:
                delta = delta - 180
        elif 90 < segment and line <= 0:
            delta = segment - line - 180
            if abs(delta) > 90:
                delta = delta - 180

        if -90 <= segment <= 0 and line >= 0:
            delta = segment - line
            if abs(delta) > 90:
                delta = delta + 180
        elif -90 > segment and line >= 0:
            delta = segment - line + 180
            if abs(delta) > 90:
                delta = delta + 180

        return delta

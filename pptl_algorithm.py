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
from processing.tools import dataobjects


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

    OUTPUT_LAYER = 'OUTPUT_LAYER'
    LINE_LAYER = 'LINE_LAYER'
    POLYGON_LAYER = 'POLYGON_LAYER'
    SELECTED = 'SELECTED'
    WRITE_SELECTED = 'WRITE_SELECTED'
    LONGEST = 'LONGEST'
    DISTANCE = 'DISTANCE'
    ANGLE = 'ANGLE'

    def __init__(self, iface):
        GeoAlgorithm.__init__(self)
        self._iface = iface

    def defineCharacteristics(self):
        # The name that the user will see in the toolbox
        self.name = 'Polygons parallel to line'

        # The branch of the toolbox under which the algorithm will appear
        self.group = 'Algorithms for vector layers'

        self.addOutput(
            OutputVector(
                self.OUTPUT_LAYER,
                self.tr('Output layer with rotated polygons')
            )
        )
        self.addParameter(
            ParameterVector(
                self.LINE_LAYER,
                self.tr('Input line layer')
            )
        )
        self.addParameter(
            ParameterVector(
                self.POLYGON_LAYER,
                self.tr('Input _polygon layer'),
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
                self.WRITE_SELECTED,
                self.tr('Write only selected'),
            )
        )
        self.addParameter(
            ParameterBoolean(
                self.LONGEST,
                self.tr("Rotate by longest edge if both angles between "
                        "_polygon edges and line segment <= 'Angle value'")
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

    def processAlgorithm(self, progress):
        self._getInputValues()
        self._lineLayer = dataobjects.getObjectFromUri(self._lineLayerName)
        self._polygonLayer = dataobjects.getObjectFromUri(
            self._polygonLayerName
        )
        self._createLineSpatialIndex()
        if self._validatePolygonLayer():
            self._rotateAndWriteSelectedOrAll(self._getWriter())


    def _getInputValues(self):
        self._lineLayerName = self.getParameterValue(self.LINE_LAYER)
        self._polygonLayerName = self.getParameterValue(self.POLYGON_LAYER)
        self._isSelected = self.getParameterValue(self.SELECTED)
        self._isWriteSelected = self.getParameterValue(self.WRITE_SELECTED)
        self._byLongest = self.getParameterValue(self.LONGEST)
        self._distance = self.getParameterValue(self.DISTANCE)
        self._angle = self.getParameterValue(self.ANGLE)
        self._outputLayer = self.getOutputValue(self.OUTPUT_LAYER)

    def _createLineSpatialIndex(self):
        self.index = QgsSpatialIndex()
        for line in self._lineLayer.getFeatures():
            self.index.insertFeature(line)

    def _validatePolygonLayer(self):
        output = False
        if self._polygonLayer.featureCount():
            output = True
        else:
            self._showMsg(self.tr("Layer does not have any polygons"))

        if self._isSelected:
            if self._polygonLayer.selectedFeatureCount():
                output = True
            else:
                self._showMsg(self.tr(
                    'You have chosen "Rotate only selected polygons" but '
                    'there are no selected'
                ))
                output = False
        return output

    def _showMsg(self, message):
        self._iface.messageBar().pushMessage("Error", message,
                                             level=QgsMessageBar.CRITICAL)

    def _getWriter(self):
        settings = QSettings()
        systemEncoding = settings.value('/UI/encoding', 'System')
        provider = self._polygonLayer.dataProvider()
        return QgsVectorFileWriter(
            self._outputLayer, systemEncoding, provider.fields(),
            provider.geometryType(), provider.crs()
        )

    def _rotateAndWriteSelectedOrAll(self, writer):
        if self._isSelected:
            self._rotateAndWriteSeleced(writer)
        else:
            self._createProgressBar(self._polygonLayer.featureCount())
            polygons = self._polygonLayer.getFeatures()
            for polygon in polygons:
                self._rotateAndWritePolygon(polygon, writer)

    def _rotateAndWriteSeleced(self, writer):
        self._createProgressBar(self._polygonLayer.selectedFeatureCount())
        if self._isWriteSelected:
            polygons = self._polygonLayer.selectedFeatures()
            for polygon in polygons:
                self._rotateAndWritePolygon(polygon, writer)
        else:
            for p in self._polygonLayer.getFeatures():
                if p.id() in self._polygonLayer.selectedFeaturesIds():
                    self._rotateAndWritePolygon(p, writer)
                else:
                    writer.addFeature(p)

    def _createProgressBar(self, items):
        self._progressBar = ShowProgress(self._iface, 'PolygonsParallelToLine',
                                         self.tr('Data processing...'), items)

    def _rotateAndWritePolygon(self, polygon, writer):
        self._polygon = polygon
        self._initiateRotation()
        writer.addFeature(self._polygon)
        self._progressBar.update(1)

    def _initiateRotation(self):
        self._getNearestLine()
        dist = self.near_line.geometry().distance(self._polygon.geometry())
        if not self._distance or dist <= self._distance:
            self._simpleOrMultiGeometry()

    def _getNearestLine(self):
        self.centroid = self._polygon.geometry().centroid()
        near_id = self.index.nearestNeighbor(self.centroid.asPoint(), 1)
        for line in self._lineLayer.getFeatures():
            if line.id() == near_id[0]:
                self.near_line = line

    def _simpleOrMultiGeometry(self):
        if self._polygon.geometry().isMultipart():
            for part in self._polygon.geometry().asMultiPolygon():
                self._nearestVertex(part[0])
        else:
            self._nearestVertex(self._polygon.geometry().asPolygon()[0])

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
            self.line1 = QgsGeometry.fromPolyline(
                [polygonVertexes[0], polygonVertexes[1]])
            self.line2 = QgsGeometry.fromPolyline(
                [polygonVertexes[0], polygonVertexes[-1]])

        # if vertex is last
        elif vertexIndex == len(polygonVertexes) - 1:
            self.line1 = QgsGeometry.fromPolyline(
                [polygonVertexes[-1], polygonVertexes[0]])
            self.line2 = QgsGeometry.fromPolyline(
                [polygonVertexes[-1], polygonVertexes[-2]])
        else:
            self.line1 = QgsGeometry.fromPolyline(
                [polygonVertexes[vertexIndex],
                 polygonVertexes[vertexIndex + 1]]
            )
            self.line2 = QgsGeometry.fromPolyline(
                [polygonVertexes[vertexIndex],
                 polygonVertexes[vertexIndex - 1]]
            )

        line1Azimuth = self.line1.asPolyline()[0].azimuth(
            self.line1.asPolyline()[1]
        )
        line2Azimuth = self.line2.asPolyline()[0].azimuth(
            self.line2.asPolyline()[1]
        )
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

        self._azimuth(deltaAzimuth1, deltaAzimuth2)

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

    def _azimuth(self, deltaAzimuth1, deltaAzimuth2):
        delta1 = abs(deltaAzimuth1)
        delta2 = abs(deltaAzimuth2)

        if abs(deltaAzimuth1) > 90:
            delta1 = 180 - abs(deltaAzimuth1)
        if abs(deltaAzimuth2) > 90:
            delta2 = 180 - abs(deltaAzimuth2)

        self._needRefactor(deltaAzimuth1, deltaAzimuth2, delta1, delta2)

    def _needRefactor(self, deltaAzimuth1, deltaAzimuth2, delta1, delta2):
        if self._byLongest:
            if delta1 <= self._angle and delta2 <= self._angle:
                if self.line1.geometry().length() >= self.line2.geometry().length():
                    self._polygon.geometry().rotate(deltaAzimuth1,
                                                    self.centroid.asPoint())
                elif self.line1.geometry().length() < self.line2.geometry().length():
                    self._polygon.geometry().rotate(deltaAzimuth2,
                                                    self.centroid.asPoint())
                elif self.line1.geometry().length() == self.line2.geometry().length():
                    if delta1 > delta2:
                        self._polygon.geometry().rotate(deltaAzimuth2,
                                                        self.centroid.asPoint())
                    elif delta1 < delta2:
                        self._polygon.geometry().rotate(deltaAzimuth1,
                                                        self.centroid.asPoint())
                    elif delta1 == delta2:
                        self._polygon.geometry().rotate(deltaAzimuth1,
                                                        self.centroid.asPoint())
            elif delta1 <= self._angle:
                self._polygon.geometry().rotate(deltaAzimuth1, self.centroid.asPoint())
            elif delta2 <= self._angle:
                self._polygon.geometry().rotate(deltaAzimuth2, self.centroid.asPoint())
        else:
            if delta1 <= self._angle and delta2 <= self._angle:
                if delta1 > delta2:
                    self._polygon.geometry().rotate(deltaAzimuth2,
                                                    self.centroid.asPoint())
                elif delta1 < delta2:
                    self._polygon.geometry().rotate(deltaAzimuth1,
                                                    self.centroid.asPoint())
                elif delta1 == delta2:
                    self._polygon.geometry().rotate(deltaAzimuth1,
                                                    self.centroid.asPoint())
            elif delta1 <= self._angle:
                self._polygon.geometry().rotate(deltaAzimuth1, self.centroid.asPoint())
            elif delta2 <= self._angle:
                self._polygon.geometry().rotate(deltaAzimuth2, self.centroid.asPoint())
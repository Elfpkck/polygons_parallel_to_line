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

from __future__ import division


__author__ = 'Andrey Lekarev'
__date__ = '2016-03-10'
__copyright__ = '(C) 2016-2017 by Andrey Lekarev'


from PyQt4.QtCore import QSettings

from qgis.core import QgsVectorFileWriter, QgsSpatialIndex, QgsGeometry

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import (
    GeoAlgorithmExecutionException)
from processing.core.parameters import (ParameterVector, ParameterBoolean,
                                        ParameterNumber)
from processing.core.outputs import OutputVector
from processing.tools import dataobjects


class PolygonsParallelToLineAlgorithm(GeoAlgorithm):

    OUTPUT_LAYER = 'OUTPUT_LAYER'
    LINE_LAYER = 'LINE_LAYER'
    POLYGON_LAYER = 'POLYGON_LAYER'
    SELECTED = 'SELECTED'
    WRITE_SELECTED = 'WRITE_SELECTED'
    LONGEST = 'LONGEST'
    DISTANCE = 'DISTANCE'
    ANGLE = 'ANGLE'

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
        self._operationCounter = 0
        self._progress = progress
        self._getInputValues()
        self._lineLayer = dataobjects.getObjectFromUri(self._lineLayerName)
        self._polygonLayer = dataobjects.getObjectFromUri(
            self._polygonLayerName
        )
        self._createLineSpatialIndex()
        self._validatePolygonLayer()
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
        self._index = QgsSpatialIndex()
        for line in self._lineLayer.getFeatures():
            self._index.insertFeature(line)

    def _validatePolygonLayer(self):
        self._totalNumber = self._polygonLayer.featureCount()
        if not self._totalNumber:
            raise GeoAlgorithmExecutionException(
                self.tr("Layer does not have any polygons")
            )
        if self._isSelected:
            self._totalNumber = self._polygonLayer.selectedFeatureCount()
            if not self._totalNumber:
                raise GeoAlgorithmExecutionException(
                    self.tr('You have chosen "Rotate only selected polygons" '
                            'but there are no selected')
                )

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
            polygons = self._polygonLayer.getFeatures()
            for polygon in polygons:
                self._rotateAndWritePolygon(polygon, writer)

    def _rotateAndWriteSeleced(self, writer):
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

    def _rotateAndWritePolygon(self, polygon, writer):
        self._polygon = polygon
        self._initiateRotation()
        writer.addFeature(self._polygon)

        self._operationCounter += 1
        currentPercentage = self._operationCounter / self._totalNumber * 100
        self._progress.setPercentage(round(currentPercentage))

    def _initiateRotation(self):
        self._getNearestLine()
        dist = self._nearLine.geometry().distance(self._polygon.geometry())
        if not self._distance or dist <= self._distance:
            self._simpleOrMultiGeometry()

    def _getNearestLine(self):
        self._centroid = self._polygon.geometry().centroid()
        nearId = self._index.nearestNeighbor(self._centroid.asPoint(), 1)
        for line in self._lineLayer.getFeatures():
            if line.id() == nearId[0]:
                self._nearLine = line

    def _simpleOrMultiGeometry(self):
        if self._polygon.geometry().isMultipart():
            dct = {}
            mPolygonVertexes = self._polygon.geometry().asMultiPolygon()
            for i, part in enumerate(mPolygonVertexes):
                minDistance, vertexIndex = self._getNearestVertex(part[0])
                dct[(i, vertexIndex)] = minDistance
            i, vertexIndex = min(dct, key=dct.get)
            self._nearestEdges(mPolygonVertexes[i][0], vertexIndex)
        else:
            polygonVertexes = self._polygon.geometry().asPolygon()[0]
            vertexIndex = self._getNearestVertex(polygonVertexes)[1]
            self._nearestEdges(polygonVertexes, vertexIndex)

    def _getNearestVertex(self, polygonVertexes):
        vertexToSegmentDict = {}
        for vertex in polygonVertexes[:-1]:
            vertexGeom = QgsGeometry.fromPoint(vertex)
            vertexToSegment = vertexGeom.distance(self._nearLine.geometry())
            vertexToSegmentDict[vertexToSegment] = vertex

        minDistance = min(vertexToSegmentDict.keys())
        self._nearestVertex = vertexToSegmentDict[minDistance]
        vertexIndex = polygonVertexes.index(self._nearestVertex)
        return minDistance, vertexIndex

    def _nearestEdges(self, polygonVertexes, vertexIndex):
        # if vertex is first
        if vertexIndex == 0:
            self._line1 = QgsGeometry.fromPolyline(
                [polygonVertexes[0], polygonVertexes[1]])
            self._line2 = QgsGeometry.fromPolyline(
                [polygonVertexes[0], polygonVertexes[-1]])

        # if vertex is last
        elif vertexIndex == len(polygonVertexes) - 1:
            self._line1 = QgsGeometry.fromPolyline(
                [polygonVertexes[-1], polygonVertexes[0]])
            self._line2 = QgsGeometry.fromPolyline(
                [polygonVertexes[-1], polygonVertexes[-2]])
        else:
            self._line1 = QgsGeometry.fromPolyline(
                [polygonVertexes[vertexIndex],
                 polygonVertexes[vertexIndex + 1]]
            )
            self._line2 = QgsGeometry.fromPolyline(
                [polygonVertexes[vertexIndex],
                 polygonVertexes[vertexIndex - 1]]
            )

        line1Azimuth = self._line1.asPolyline()[0].azimuth(
            self._line1.asPolyline()[1]
        )
        line2Azimuth = self._line2.asPolyline()[0].azimuth(
            self._line2.asPolyline()[1]
        )
        self._segmentAzimuth(line1Azimuth, line2Azimuth)

    def _segmentAzimuth(self, line1Azimuth, line2Azimuth):
        closestSegment = self._nearLine.geometry().closestSegmentWithContext(
            self._nearestVertex
        )
        indexSegmEnd = closestSegment[-1]
        segmEnd = self._nearLine.geometry().asPolyline()[indexSegmEnd]
        segmStart = self._nearLine.geometry().asPolyline()[indexSegmEnd - 1]
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
                if self._line1.geometry().length() >= self._line2.geometry().length():
                    self._polygon.geometry().rotate(deltaAzimuth1,
                                                    self._centroid.asPoint())
                elif self._line1.geometry().length() < self._line2.geometry().length():
                    self._polygon.geometry().rotate(deltaAzimuth2,
                                                    self._centroid.asPoint())
                elif self._line1.geometry().length() == self._line2.geometry().length():
                    if delta1 > delta2:
                        self._polygon.geometry().rotate(deltaAzimuth2,
                                                        self._centroid.asPoint())
                    elif delta1 < delta2:
                        self._polygon.geometry().rotate(deltaAzimuth1,
                                                        self._centroid.asPoint())
                    elif delta1 == delta2:
                        self._polygon.geometry().rotate(deltaAzimuth1,
                                                        self._centroid.asPoint())
            elif delta1 <= self._angle:
                self._polygon.geometry().rotate(deltaAzimuth1, self._centroid.asPoint())
            elif delta2 <= self._angle:
                self._polygon.geometry().rotate(deltaAzimuth2, self._centroid.asPoint())
        else:
            if delta1 <= self._angle and delta2 <= self._angle:
                if delta1 > delta2:
                    self._polygon.geometry().rotate(deltaAzimuth2,
                                                    self._centroid.asPoint())
                elif delta1 < delta2:
                    self._polygon.geometry().rotate(deltaAzimuth1,
                                                    self._centroid.asPoint())
                elif delta1 == delta2:
                    self._polygon.geometry().rotate(deltaAzimuth1,
                                                    self._centroid.asPoint())
            elif delta1 <= self._angle:
                self._polygon.geometry().rotate(deltaAzimuth1, self._centroid.asPoint())
            elif delta2 <= self._angle:
                self._polygon.geometry().rotate(deltaAzimuth2, self._centroid.asPoint())
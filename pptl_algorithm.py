# -*- coding: utf-8 -*-

"""
/***************************************************************************
 PolygonsParallelToLine
                                 A QGIS plugin
 This plugin rotates polygons parallel to line
                              -------------------
        begin                : 2016-03-10
        copyright            : (C) 2016-2017 by Andrey Lekarev
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

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import os

from PyQt4.QtCore import (QSettings, QVariant, QTranslator, qVersion,
                          QCoreApplication)

from qgis.core import (QgsVectorFileWriter, QgsSpatialIndex, QgsGeometry,
                       QgsField)

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
    COLUMN_NAME = '_rotated'

    def __init__(self):
        self._translateUi()
        GeoAlgorithm.__init__(self)

    def _translateUi(self):
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            os.path.dirname(__file__),
            'i18n',
            'pptl_{}.qm'.format(locale)
        )
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

    def tr(self, message):
        className = self.__class__.__name__
        return QCoreApplication.translate(className, message)

    def defineCharacteristics(self):
        # The name that the user will see in the toolbox
        self.name = self.tr('Polygons parallel to line')

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.tr('Algorithms for vector layers')

        self.addOutput(
            OutputVector(
                self.OUTPUT_LAYER,
                self.tr('Select output layer with rotated polygons')
            )
        )
        self.addParameter(
            ParameterVector(
                self.LINE_LAYER,
                self.tr('Select line layer')
            )
        )
        self.addParameter(
            ParameterVector(
                self.POLYGON_LAYER,
                self.tr('Select polygon layer'),
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
                self.tr('Save only selected'),
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
        self._addAttribute()
        self._rotateAndWriteSelectedOrAll(self._getWriter())
        self._deleteAttribute()

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

    def _addAttribute(self):
        for attr in self._polygonLayer.pendingFields():
            if self.COLUMN_NAME == attr.name():
                if attr.isNumeric():
                    break
                else:
                    self._deleteAttribute()
        else:
            self._polygonLayer.dataProvider().addAttributes(
                [QgsField(self.COLUMN_NAME, QVariant.Int)]
            )
            self._polygonLayer.updateFields()

    def _deleteAttribute(self):
        for i, attr in enumerate(self._polygonLayer.pendingFields()):
            if attr.name() == self.COLUMN_NAME:
                self._polygonLayer.dataProvider().deleteAttributes([i])
                self._polygonLayer.updateFields()

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
        self._progressBar()
        self._p = polygon
        self._initiateRotation()
        writer.addFeature(self._p)

    def _progressBar(self):
        self._operationCounter += 1
        currentPercentage = self._operationCounter / self._totalNumber * 100
        self._progress.setPercentage(round(currentPercentage))

    def _initiateRotation(self):
        self._getNearestLine()
        dist = self._nearLine.geometry().distance(self._p.geometry())
        if not self._distance or dist <= self._distance:
            self._simpleOrMultiGeometry()

    def _getNearestLine(self):
        self._center = self._p.geometry().centroid()
        nearId = self._index.nearestNeighbor(self._center.asPoint(), 1)
        for line in self._lineLayer.getFeatures():
            if line.id() == nearId[0]:
                self._nearLine = line

    def _simpleOrMultiGeometry(self):
        if self._p.geometry().isMultipart():
            dct = {}
            mPolygonVertexes = self._p.geometry().asMultiPolygon()
            for i, part in enumerate(mPolygonVertexes):
                minDistance, vertexIndex = self._getNearestVertex(part[0])
                dct[(i, vertexIndex)] = minDistance
            i, vertexIndex = min(dct, key=dct.get)
            self._nearestEdges(mPolygonVertexes[i][0], vertexIndex)
        else:
            polygonVertexes = self._p.geometry().asPolygon()[0][:-1]
            vertexIndex = self._getNearestVertex(polygonVertexes)[1]
            self._nearestEdges(polygonVertexes, vertexIndex)

    def _getNearestVertex(self, polygonVertexes):
        vertexToSegmentDict = {}
        for vertex in polygonVertexes:
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

        self._dltAz1 = self._getDeltaAzimuth(segmentAzimuth, line1Azimuth)
        self._dltAz2 = self._getDeltaAzimuth(segmentAzimuth, line2Azimuth)

        self._azimuth()

    def _getDeltaAzimuth(self, segment, line):
        if (segment >= 0 and line >= 0) or (segment <= 0 and line <= 0):
            delta = segment - line
            if segment > line and abs(delta) > 90:
                delta -= 180
            elif segment < line and abs(delta) > 90:
                delta += 180

        if 90 >= segment >= 0 and line <= 0:
            delta = segment + abs(line)
            if delta > 90:
                delta -= 180
        elif 90 < segment and line <= 0:
            delta = segment - line - 180
            if abs(delta) > 90:
                delta -= 180

        if -90 <= segment <= 0 and line >= 0:
            delta = segment - line
            if abs(delta) > 90:
                delta += 180
        elif -90 > segment and line >= 0:
            delta = segment - line + 180
            if abs(delta) > 90:
                delta += 180

        return delta

    def _azimuth(self):
        delta1 = abs(self._dltAz1)
        delta2 = abs(self._dltAz2)

        if abs(self._dltAz1) > 90:
            delta1 = 180 - delta1
        if abs(self._dltAz2) > 90:
            delta2 = 180 - delta2

        self._rotate(delta1, delta2)

    def _rotate(self, delta1, delta2):
        self._rotationCheck = True
        if delta1 <= self._angle and delta2 <= self._angle:
            if self._byLongest:
                self._rotateByLongest(delta1, delta2)
            else:
                self._rotateNotByLongest(delta1, delta2)
        else:
            self._othersRotations(delta1, delta2)

        self._markAsRotated()

    def _rotateByLongest(self, delta1, delta2):
        if delta1 <= self._angle and delta2 <= self._angle:
            length1 = self._line1.geometry().length()
            length2 = self._line2.geometry().length()

            if length1 >= length2:
                self._p.geometry().rotate(self._dltAz1, self._center.asPoint())
            elif length1 < length2:
                self._p.geometry().rotate(self._dltAz2, self._center.asPoint())
            elif length1 == length2:
                self._rotateNotByLongest(delta1, delta2)
            else:
                self._rotationCheck = False

    def _rotateNotByLongest(self, delta1, delta2):
        if delta1 > delta2:
            self._p.geometry().rotate(self._dltAz2, self._center.asPoint())
        elif delta1 <= delta2:
            self._p.geometry().rotate(self._dltAz1, self._center.asPoint())
        else:
            self._rotationCheck = False

    def _othersRotations(self, delta1, delta2):
        if delta1 <= self._angle:
            self._p.geometry().rotate(self._dltAz1, self._center.asPoint())
        elif delta2 <= self._angle:
            self._p.geometry().rotate(self._dltAz2, self._center.asPoint())
        else:
            self._rotationCheck = False

    def _markAsRotated(self):
        if self._rotationCheck:
            self._p[self.COLUMN_NAME] = 1

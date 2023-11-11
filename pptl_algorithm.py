# -*- coding: utf-8 -*-

"""
/***************************************************************************
 PolygonsParallelToLine
                                 A QGIS plugin
 This plugin rotates polygons parallel to line
                              -------------------
        begin                : 2016-03-10
        copyright            : (C) 2016-2017 by Andrii Liekariev
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


__author__ = "Andrii Liekariev"
__date__ = "2016-03-10"
__copyright__ = "(C) 2016-2017 by Andrii Liekariev"

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = "$Format:%H$"

import pydevd_pycharm


from qgis.PyQt.QtCore import QCoreApplication, QSettings, QVariant
from qgis.core import (
    QgsField,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSource,
    QgsSpatialIndex,
    QgsProcessingParameterNumber,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
    QgsPoint,
    QgsFeatureSink,
)


class PolygonsParallelToLineAlgorithm(QgsProcessingAlgorithm):
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
        return PolygonsParallelToLineAlgorithm()

    def name(self):
        return "pptl_algo"

    def displayName(self):
        return self.tr("Polygons parallel to line")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr("Algorithms for vector layers")

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "examplescripts"

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Example algorithm short description")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LAYER,
                "Output layer with rotated polygons",
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINE_LAYER, self.tr("Select line layer"), [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POLYGON_LAYER, self.tr("Select polygon layer"), [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(self.SELECTED, self.tr("Rotate only selected polygons"), defaultValue=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(self.WRITE_SELECTED, self.tr("Save only selected"), defaultValue=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.LONGEST,
                self.tr(
                    "Rotate by longest edge if both angles between " "polygon edges and line segment <= 'Angle value'"
                ),
                defaultValue=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(self.MULTI, self.tr("Do not rotate multipolygons"), defaultValue=False)
        )
        self.addParameter(  # TODO: doesn't work
            QgsProcessingParameterNumber(
                self.DISTANCE,
                self.tr("Distance from line"),
                type=QgsProcessingParameterNumber.Double,
                minValue=0.0,
                defaultValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ANGLE,
                self.tr("Angle value"),
                type=QgsProcessingParameterNumber.Double,
                minValue=0.0,
                maxValue=89.9,
                defaultValue=89.9,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        # pydevd_pycharm.settrace("127.0.0.1", port=53100, stdoutToServer=True, stderrToServer=True)
        self._operationCounter = 0
        # self._progress = progress
        self._getInputValues(parameters, context)

        self._createLineSpatialIndex()
        self._validatePolygonLayer()
        self._addAttribute()
        self._linesDict = {x.id(): x for x in self._lineLayer.getFeatures()}
        self._rotateAndWriteSelectedOrAll()
        self._deleteAttribute()
        vlyr = context.getMapLayer(self.dest_id)  # TODO: for testing only
        line = [x.geometry() for x in self._lineLayer.getFeatures()][0].asWkt()
        poly = [x.geometry() for x in self._polygonLayer.getFeatures()][0].asWkt()
        result = [x.geometry() for x in vlyr.getFeatures()][0].asWkt()
        return {self.OUTPUT_LAYER: self.dest_id, "result": result}

    def _getInputValues(self, parameters, context):
        self._lineLayer = self.parameterAsVectorLayer(parameters, self.LINE_LAYER, context)
        self._polygonLayer = self.parameterAsVectorLayer(parameters, self.POLYGON_LAYER, context)
        self._isSelected = self.parameterAsBool(
            parameters, self.SELECTED, context
        )  # TODO use "Selected features only" checkbox instead
        self._isWriteSelected = self.parameterAsBool(parameters, self.WRITE_SELECTED, context)
        self._byLongest = self.parameterAsBool(parameters, self.LONGEST, context)
        self._multi = self.parameterAsBool(parameters, self.MULTI, context)
        self._distance = self.parameterAsInt(parameters, self.DISTANCE, context)
        self._angle = self.parameterAsInt(parameters, self.ANGLE, context)
        (self.sink, self.dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LAYER,
            context,
            self._polygonLayer.fields(),
            self._polygonLayer.wkbType(),
            self._polygonLayer.sourceCrs(),
        )

    def _createLineSpatialIndex(self):
        self._index = QgsSpatialIndex()
        for line in self._lineLayer.getFeatures():
            self._index.insertFeature(line)

    def _validatePolygonLayer(self):
        self._totalNumber = self._polygonLayer.featureCount()
        if not self._totalNumber:
            raise QgsProcessingException(self.tr("Layer does not have any polygons"))
        if self._isWriteSelected and not self._isSelected:
            raise QgsProcessingException(
                self.tr('You have chosen "Save only selected" without ' '"Rotate only selected polygons"')
            )
        if self._isSelected:
            self._totalNumber = self._polygonLayer.selectedFeatureCount()
            if not self._totalNumber:
                raise QgsProcessingException(
                    self.tr('You have chosen "Rotate only selected polygons" ' "but there are no selected")
                )

    def _addAttribute(self):
        for attr in self._polygonLayer.fields():
            if self.COLUMN_NAME == attr.name():
                if attr.isNumeric():
                    break
                else:
                    self._deleteAttribute()
        else:
            self._polygonLayer.dataProvider().addAttributes([QgsField(self.COLUMN_NAME, QVariant.Int)])
            self._polygonLayer.updateFields()

    def _deleteAttribute(self):
        for i, attr in enumerate(self._polygonLayer.fields()):
            if attr.name() == self.COLUMN_NAME:
                self._polygonLayer.dataProvider().deleteAttributes([i])
                self._polygonLayer.updateFields()

    def _rotateAndWriteSelectedOrAll(self):
        if self._isSelected:
            self._rotateAndWriteSeleced()
        else:
            polygons = self._polygonLayer.getFeatures()
            for polygon in polygons:
                self._rotateAndWritePolygon(polygon)

    def _rotateAndWriteSeleced(self):
        if self._isWriteSelected:
            for polygon in self._polygonLayer.selectedFeatures():
                self._rotateAndWritePolygon(polygon)
        else:
            selectedPolygonsIds = self._polygonLayer.selectedFeaturesIds()
            for p in self._polygonLayer.getFeatures():
                if p.id() in selectedPolygonsIds:
                    self._rotateAndWritePolygon(p)
                else:
                    self.sink.addFeature(p, QgsFeatureSink.FastInsert)  # TODO: addFeatures

    def _rotateAndWritePolygon(self, polygon):
        self._progressBar()
        self._p = polygon
        self._initiateRotation()
        self.sink.addFeature(self._p, QgsFeatureSink.FastInsert)  # TODO: addFeatures

    def _progressBar(self):
        self._operationCounter += 1
        currentPercentage = self._operationCounter / self._totalNumber * 100
        # self._progress.setPercentage(round(currentPercentage))

    def _initiateRotation(self):
        self._getNearestLine()
        dist = self._nearLine.geometry().distance(self._p.geometry())
        if not self._distance or dist <= self._distance:
            self._simpleOrMultiGeometry()

    def _getNearestLine(self):
        self._center = self._p.geometry().centroid()
        nearId = self._index.nearestNeighbor(self._center.asPoint(), 1)
        self._nearLine = self._linesDict.get(nearId[0])

    def _simpleOrMultiGeometry(self):
        isMulti = self._p.geometry().isMultipart()
        if isMulti and not self._multi:
            dct = {}
            mPolygonVertexes = self._p.geometry().asMultiPolygon()
            for i, part in enumerate(mPolygonVertexes):
                minDistance, vertexIndex = self._getNearestVertex(part[0])
                dct[(i, vertexIndex)] = minDistance
            i, vertexIndex = min(dct, key=dct.get)
            self._nearestEdges(mPolygonVertexes[i][0], vertexIndex)
        elif not isMulti:
            polygonVertexes = self._p.geometry().asPolygon()[0][:-1]
            vertexIndex = self._getNearestVertex(polygonVertexes)[1]
            self._nearestEdges(polygonVertexes, vertexIndex)

    def _getNearestVertex(self, polygonVertexes):
        vertexToSegmentDict = {}
        for vertex in polygonVertexes:
            vertexGeom = QgsGeometry.fromPointXY(vertex)
            vertexToSegment = vertexGeom.distance(self._nearLine.geometry())
            vertexToSegmentDict[vertexToSegment] = vertex

        minDistance = min(vertexToSegmentDict.keys())
        self._nearestVertex = vertexToSegmentDict[minDistance]
        vertexIndex = polygonVertexes.index(self._nearestVertex)
        return minDistance, vertexIndex

    def _nearestEdges(self, polygonVertexes, vertexIndex):
        # if vertex is first
        if vertexIndex == 0:
            self._line1 = QgsGeometry.fromPolyline([QgsPoint(polygonVertexes[0]), QgsPoint(polygonVertexes[1])])
            self._line2 = QgsGeometry.fromPolyline([QgsPoint(polygonVertexes[0]), QgsPoint(polygonVertexes[-1])])

        # if vertex is last
        elif vertexIndex == len(polygonVertexes) - 1:
            self._line1 = QgsGeometry.fromPolyline([QgsPoint(polygonVertexes[-1]), QgsPoint(polygonVertexes[0])])
            self._line2 = QgsGeometry.fromPolyline([QgsPoint(polygonVertexes[-1]), QgsPoint(polygonVertexes[-2])])
        else:
            self._line1 = QgsGeometry.fromPolyline(
                [QgsPoint(polygonVertexes[vertexIndex]), QgsPoint(polygonVertexes[vertexIndex + 1])]
            )
            self._line2 = QgsGeometry.fromPolyline(
                [QgsPoint(polygonVertexes[vertexIndex]), QgsPoint(polygonVertexes[vertexIndex - 1])]
            )

        line1Azimuth = self._line1.asPolyline()[0].azimuth(self._line1.asPolyline()[1])
        line2Azimuth = self._line2.asPolyline()[0].azimuth(self._line2.asPolyline()[1])
        self._segmentAzimuth(line1Azimuth, line2Azimuth)

    def _segmentAzimuth(self, line1Azimuth, line2Azimuth):
        nearLineGeom = self._nearLine.geometry()
        if nearLineGeom.isMultipart():
            dct = {}
            minDists = []

            for line in nearLineGeom.asMultiPolyline():
                l = QgsGeometry.fromPolyline([QgsPoint(x) for x in line])
                closestSegmContext = l.closestSegmentWithContext(self._nearestVertex)
                minDists.append(closestSegmContext[0])
                dct[closestSegmContext[0]] = [line, closestSegmContext[-1]]

            minDistance = min(minDists)
            closestSegment = dct[minDistance][0]
            indexSegmEnd = dct[minDistance][1]
            segmEnd = closestSegment[indexSegmEnd]
            segmStart = closestSegment[indexSegmEnd - 1]
        else:
            closestSegmContext = nearLineGeom.closestSegmentWithContext(self._nearestVertex)
            indexSegmEnd = closestSegmContext[-1]
            segmEnd = nearLineGeom.asPolyline()[indexSegmEnd]
            segmStart = nearLineGeom.asPolyline()[indexSegmEnd - 1]

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
            length1 = self._line1.length()
            length2 = self._line2.length()

            if length1 >= length2:
                geom = self._p.geometry()
                geom.rotate(self._dltAz1, self._center.asPoint())
                self._p.setGeometry(geom)
            elif length1 < length2:
                geom = self._p.geometry()
                geom.rotate(self._dltAz2, self._center.asPoint())
                self._p.setGeometry(geom)
            elif length1 == length2:
                self._rotateNotByLongest(delta1, delta2)
            else:
                self._rotationCheck = False

    def _rotateNotByLongest(self, delta1, delta2):
        if delta1 > delta2:
            geom = self._p.geometry()
            geom.rotate(self._dltAz2, self._center.asPoint())
            self._p.setGeometry(geom)
        elif delta1 <= delta2:
            geom = self._p.geometry()
            geom.rotate(self._dltAz1, self._center.asPoint())
            self._p.setGeometry(geom)
        else:
            self._rotationCheck = False

    def _othersRotations(self, delta1, delta2):
        if delta1 <= self._angle:
            geom = self._p.geometry()
            geom.rotate(self._dltAz1, self._center.asPoint())
            self._p.setGeometry(geom)
        elif delta2 <= self._angle:
            geom = self._p.geometry()
            self._p.geometry().rotate(self._dltAz2, self._center.asPoint())
            self._p.setGeometry(geom)
        else:
            self._rotationCheck = False

    def _markAsRotated(self):
        if self._rotationCheck:
            self._p[self.COLUMN_NAME] = 1


# TODO: for the future: a method to make 2 objects (lines, polygons) parallel

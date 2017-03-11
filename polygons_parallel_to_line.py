# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PolygonsParallelToLine
                                 A QGIS plugin
 This plugin rotates polygons parallel to line
                              -------------------
        begin                : 2016-03-10
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Andrey Lekarev
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
from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.utils import *

import resources
from polygons_parallel_to_line_dialog import PolygonsParallelToLineDialog


class PolygonsParallelToLine:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PolygonsParallelToLine_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = PolygonsParallelToLineDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Polygons Parallel to Line')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'PolygonsParallelToLine')
        self.toolbar.setObjectName(u'PolygonsParallelToLine')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PolygonsParallelToLine', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/PolygonsParallelToLine/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Polygons parallel to line'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Polygons Parallel to Line'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer and layer.wkbType() == QGis.WKBLineString:
                self.dlg.comboBox.addItem(layer.name(), layer)            
            if layer.type() == QgsMapLayer.VectorLayer and layer.wkbType() == QGis.WKBPolygon:
                self.dlg.comboBox_2.addItem(layer.name(), layer)
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop       
        result = self.dlg.exec_()
        # if OK was pressed

        if result:
            
            # assignment to the variable distance value entered in the dialog box
            distance = self.dlg.distance.value()

            # assignment to the variable angle value entered in the dialog box
            angle = self.dlg.angle.value()

            # actions with linear layer, which was chosed in dialog window
            selectedLayerIndex = self.dlg.comboBox.currentIndex()
            linearLayer = self.dlg.comboBox.itemData(selectedLayerIndex)

            # Get all the features to start
            linefeatures = {feature.id(): feature for (feature) in linearLayer.getFeatures()}
            
            # creating spatial index for line layer features
            index = QgsSpatialIndex()
            for line in linearLayer.getFeatures():
                index.insertFeature(line)
            
            # actions with linear layer, which was chosed in dialog window
            selectedLayerIndex_2 = self.dlg.comboBox_2.currentIndex()
            polygonalLayer = self.dlg.comboBox_2.itemData(selectedLayerIndex_2)
            
            # creating progressbar
            if self.dlg.selectedCheck.checkState() == 2:
                progressBar = ShowProgress('PolygonsParallelToLine', 'Обработка данных...', len(polygonalLayer.selectedFeatures()))
            elif self.dlg.selectedCheck.checkState() == 0:           
                progressBar = ShowProgress('PolygonsParallelToLine', 'Обработка данных...', polygonalLayer.featureCount())

            polygonalLayer.dataProvider().addAttributes([QgsField("rotated", QVariant.Int)])
            
            polygonalLayer.startEditing() 
            
            def mainAction(pFeatures):

                for polygon in pFeatures:
                
                    if not polygon.geometry().isMultipart():
                        # search nearest neighbor to polygon (from centroid) between lines
                        centroid = polygon.geometry().centroid()
                        near_id = index.nearestNeighbor(centroid.asPoint(),1)
                        near_line = linefeatures[near_id[0]]
                        dist = near_line.geometry().distance(polygon.geometry())
                        
                        # check if polygon closer then distance, chosen in dialog window
                        if dist <= distance:
                            polygonVertexes = polygon.geometry().asPolygon()[0][:-1]
                            vertex_to_segment_dict = {}
                            
                            for vertex in polygonVertexes:
                                vertex_geom = QgsGeometry.fromPoint(vertex)
                                vertex_to_segment = vertex_geom.distance(near_line.geometry())
                                vertex_to_segment_dict[vertex_to_segment] = vertex
                                
                            # min distance from vertex to segment in current polygon
                            minDistance = min(vertex_to_segment_dict.keys())                    
                            nearestVertex = vertex_to_segment_dict[minDistance]
                            vertexIndex = polygonVertexes.index(nearestVertex)

                            # search for two polygon edges from nearest vertex
                            # if node is first
                            if vertexIndex == 0:
                                line1 = QgsGeometry.fromPolyline([polygonVertexes[0], polygonVertexes[1]])
                                line2 = QgsGeometry.fromPolyline([polygonVertexes[0], polygonVertexes[-1]])
                            
                            # if node is last
                            elif vertexIndex == len(polygonVertexes) - 1:
                                line1 = QgsGeometry.fromPolyline([polygonVertexes[-1], polygonVertexes[0]])
                                line2 = QgsGeometry.fromPolyline([polygonVertexes[-1], polygonVertexes[-2]])
                            else:
                                line1 = QgsGeometry.fromPolyline([polygonVertexes[vertexIndex], polygonVertexes[vertexIndex+1]])
                                line2 = QgsGeometry.fromPolyline([polygonVertexes[vertexIndex], polygonVertexes[vertexIndex-1]])
                            
                            line1Azimuth = line1.asPolyline()[0].azimuth(line1.asPolyline()[1])
                            line2Azimuth = line2.asPolyline()[0].azimuth(line2.asPolyline()[1])    
                                                           
                            closestSegment = near_line.geometry().closestSegmentWithContext(nearestVertex)
                            indexSegmEnd = closestSegment[-1]

                            indexSegmStart = indexSegmEnd - 1

                            i = 0
                            for node in near_line.geometry().asPolyline():
                                if indexSegmStart == i:
                                    segmStart = node
                                elif indexSegmEnd == i:
                                    segmEnd = node
                                i += 1
                            segmentAzimuth = segmStart.azimuth(segmEnd)
                           
                            def preRotation(segment, line):
                                
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
                           
                            deltaAzimuth1 = preRotation(segmentAzimuth, line1Azimuth)
                            deltaAzimuth2 = preRotation(segmentAzimuth, line2Azimuth)

                            # 'Delta' is entered to compare values 'deltaAzimuth' with the 'angle', which the user inputs,
                            # but the rotation of polygon actes by 'deltaAzimuth'
                            delta1 = abs(deltaAzimuth1)
                            delta2 = abs(deltaAzimuth2)
                            
                            if abs(deltaAzimuth1) > 90:
                                delta1 = 180 - abs(deltaAzimuth1)
                            if abs(deltaAzimuth2) > 90:
                                delta2 = 180 - abs(deltaAzimuth2)
                            
                            # create variable to check if polygon will rotate
                            rotationCheck = 0                                  
                            check = self.dlg.checkBox.checkState()
                            
                            if check == 2:
                                if delta1 <= angle and delta2 <= angle:
                                    if line1.geometry().length() >= line2.geometry().length():
                                        polygon.geometry().rotate(deltaAzimuth1,centroid.asPoint())
                                        rotationCheck = 1
                                    elif line1.geometry().length() < line2.geometry().length():
                                        polygon.geometry().rotate(deltaAzimuth2,centroid.asPoint())
                                        rotationCheck = 1                                
                                    elif line1.geometry().length() == line2.geometry().length():
                                        if delta1 > delta2:
                                            polygon.geometry().rotate(deltaAzimuth2,centroid.asPoint())
                                            rotationCheck = 1
                                        elif delta1 < delta2:
                                            polygon.geometry().rotate(deltaAzimuth1,centroid.asPoint())
                                            rotationCheck = 1
                                        elif delta1 == delta2:
                                            polygon.geometry().rotate(deltaAzimuth1,centroid.asPoint())
                                            rotationCheck = 1
                                elif delta1 <= angle:
                                    polygon.geometry().rotate(deltaAzimuth1,centroid.asPoint())
                                    rotationCheck = 1
                                elif delta2 <= angle:
                                    polygon.geometry().rotate(deltaAzimuth2,centroid.asPoint())
                                    rotationCheck = 1
                            elif check == 0:
                                if delta1 <= angle and delta2 <= angle:
                                    if delta1 > delta2:
                                        polygon.geometry().rotate(deltaAzimuth2,centroid.asPoint())
                                        rotationCheck = 1
                                    elif delta1 < delta2:
                                        polygon.geometry().rotate(deltaAzimuth1,centroid.asPoint())
                                        rotationCheck = 1
                                    elif delta1 == delta2:
                                        polygon.geometry().rotate(deltaAzimuth1,centroid.asPoint())
                                        rotationCheck = 1
                                elif delta1 <= angle:
                                    polygon.geometry().rotate(deltaAzimuth1,centroid.asPoint())
                                    rotationCheck = 1
                                elif delta2 <= angle:
                                    polygon.geometry().rotate(deltaAzimuth2,centroid.asPoint())
                                    rotationCheck = 1
                        
                            if rotationCheck != 0:
                                polygon['rotated'] = 1
                                polygonalLayer.updateFeature(polygon)
                    progressBar.update(1)
                polygonalLayer.changeGeometry(polygon.id(),polygon.geometry())
                
                

            #rotate all polygons or only selected    
            if self.dlg.selectedCheck.checkState() == 2:
                mainAction(polygonalLayer.selectedFeatures())

            elif self.dlg.selectedCheck.checkState() == 0:
                mainAction(polygonalLayer.getFeatures())


            polygonalLayer.triggerRepaint()

        
        self.dlg.comboBox.clear()
        self.dlg.comboBox_2.clear()
        
class ShowProgress():

    def __init__(self, title, message, items):
        '''
        Informs user about progress via progress bar at QGIS messageBar

        Parameters
        —--------

        title: string,
        bar title

        message: string,
        bar message

        items: int,
        number of items in bar
        '''
        # Set up progress bar
        iface.messageBar().clearWidgets()
        progressMessageBar = iface.messageBar().createMessage(title, message)
        self.progress = QProgressBar(progressMessageBar)
        self.progress.setMaximum(items) # Maximum 100%
        progressMessageBar.layout().addWidget(self.progress)
        iface.messageBar().pushWidget(progressMessageBar)
        self.pr = 0
        self.progress.setValue(self.pr)

    def update(self, value):
        self.pr += value
        self.progress.setValue(self.pr)

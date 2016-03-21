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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import os.path

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
        # See if OK was pressed

        if result:
            # присвоение переменной значения расстояния, введеного в диалоговом окне
            distance = self.dlg.distance.value()

            # присвоение переменной значения угла, введеного в диалоговом окне
            angle = self.dlg.angle.value()

            # работа с линейным слоем, выбранным в диалоговом окне
            selectedLayerIndex = self.dlg.comboBox.currentIndex()
            selectedLayer = self.dlg.comboBox.itemData(selectedLayerIndex)
            
            # создание списка с координатами узлов линий
            line_segments = []   
            for line in selectedLayer.getFeatures():
                temp = []
                for node in line.geometry().asPolyline():             
                    temp.append(node)
                line_segments.append(temp)

            # работа с полигональным слоем, выбранным в диалоговом окне
            selectedLayerIndex_2 = self.dlg.comboBox_2.currentIndex()
            selectedLayer_2 = self.dlg.comboBox_2.itemData(selectedLayerIndex_2)
            
            def poly_nodes():
                global centroid, polygon_nodes, node_to_segments_dict
                centroid = QgsGeometry.centroid(polygon.geometry())
                polygon_nodes = polygon.geometry().asPolygon()[0]
                # remove last node, because it's same to first
                polygon_nodes.pop()
                # словарь вида 
                #{к-ты узла1: {к-ты сегм-та1: расст-е от узла п-на до сегм1, кс2: расст-е2}, к-ты узла2{-||-}}
                node_to_segments_dict = {}
            
            def empty_dict_node_to_segment():
                # сегменты линии
                # словарь вида {координаты сегмента: расстояние от узла полигона до сегмента}
                global node_to_segment_dict
                node_to_segment_dict = {}                
            
            def min_dist():
                global node_to_segment_lst, line_start, line_end, line_segment, u
                node_to_segment_lst = []
                line_start = QgsPoint(segment[x])
                line_end = QgsPoint(segment[x+1])
                line_segment = (line_start, line_end)
                # sqrDist of the line
                magnitude = line_end.sqrDist(line_start)
                # minimum distance
                try:
                    u = ((node.x() - line_start.x()) * (line_end.x() - line_start.x()) + 
                    (node.y() - line_start.y()) * (line_end.y() - line_start.y()))/(magnitude)
                except ZeroDivisionError:
                    print 'Корректировка u, т.к. возникло деление на ноль'
                    u = u - 0.000000000001                
            
            def if_not_perpendicular():
                global node_to_segment
                # condition (if u > 1 or u < 0) was taken from http://paulbourke.net/geometry/pointlineplane/
                # choose the shortest segment between distance of polygon's node to each node of line's segment
                segment_start = QgsGeometry.fromPolyline([line_start, node])
                segment_end = QgsGeometry.fromPolyline([node, line_end])
                length_start = segment_start.geometry().length()
                length_end = segment_end.geometry().length()

                if length_start > length_end:
                    node_to_segment = QgsGeometry.fromPolyline([node, line_end])
                    node_to_segment_lst.append(node_to_segment.length())

                else:
                    node_to_segment = QgsGeometry.fromPolyline([node, line_start])
                    node_to_segment_lst.append(node_to_segment.length())
                
            def if_perpendicular():
                global node_to_segment
                # intersection point on the line
                ix = line_start.x() + u * (line_end.x() - line_start.x())
                iy = line_start.y() + u * (line_end.y() - line_start.y())
                # перпендикуляр от точки до линии
                node_to_segment = QgsGeometry.fromPolyline([node, QgsPoint(ix,iy)])
                node_to_segment_lst.append(node_to_segment.length())
                
            for polygon in selectedLayer_2.getFeatures():
                poly_nodes()
                
                for node in polygon_nodes:
                    empty_dict_node_to_segment()

                    for segment in line_segments:
                        x = 0
                        # расстояние между узлом полигона и ближайшим узлом линии
                        
                        while x < len(segment) - 1:
                            min_dist()
                            
                            if u > 1 or u < 0:   
                                if_not_perpendicular()
                            else:
                                if_perpendicular()
                            x += 1
                            node_to_segment_dict.update({line_segment: node_to_segment_lst})

                        node_to_segments_dict.update({node: node_to_segment_dict})

                # минимальное расстояние от узла до отрезка в данном полигоне
                min_distance = min([min(x.values()) for x in node_to_segments_dict.values()])

                # если полигон находится не дальше, чем указано в диалоговом окне
                if min_distance[0] <= distance:
                    # присвоить переменным отрезок, азимут отрезка и узел
                    y = 0
                    for node in node_to_segments_dict.values():
                        i = 0
                        for node_to_segments in node.values():
                            if min_distance == node_to_segments:
                                segment = node.keys()[i]
                                cord = node_to_segments_dict.keys()[y]
                            i += 1
                        y += 1

                    segment_azimuth = segment[0].azimuth(segment[1])
                    print '\n', 'segment_azimuth', segment_azimuth

                    # Поиск двух ребер полигона, примыкающих у узлу, от которого минимальное...
                    # ...расстояние до отрезка линии.
                    i = 0
                    while i < len(polygon_nodes):
                        if polygon_nodes[i] == cord:
                            # if node is first
                            if i == 0:
                                line1 = QgsGeometry.fromPolyline([polygon_nodes[i], polygon_nodes[i+1]])
                                line2 = QgsGeometry.fromPolyline([polygon_nodes[i], polygon_nodes[-1]])
                            # if node is last
                            elif i == len(polygon_nodes) - 1:
                                line1 = QgsGeometry.fromPolyline([polygon_nodes[i], polygon_nodes[0]])
                                line2 = QgsGeometry.fromPolyline([polygon_nodes[i], polygon_nodes[i-1]])
                            else:
                                line1 = QgsGeometry.fromPolyline([polygon_nodes[i], polygon_nodes[i+1]])
                                line2 = QgsGeometry.fromPolyline([polygon_nodes[i], polygon_nodes[i-1]])
                        i += 1

                    line1_azimuth = line1.asPolyline()[0].azimuth(line1.asPolyline()[1])
                    line2_azimuth = line2.asPolyline()[0].azimuth(line2.asPolyline()[1])
                    

                    
                    selectedLayer_2.startEditing()
                    def rotator(segment, line):
                        
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
                    
                    delta_azimuth1 = rotator(segment_azimuth, line1_azimuth)
                    delta_azimuth2 = rotator(segment_azimuth, line2_azimuth)
                    
                    print 'line1_azimuth', line1_azimuth
                    print 'delta_azimuth', delta_azimuth1
                    print 'line2_azimuth', line2_azimuth
                    print 'delta_azimuth2', delta_azimuth2

                    # 'delta' вводится, чтобы сопоставить программные значения 'delta_azimuth' с 'angle', 
                    # который вводит пользователь, но вращение полигона производится по 'delta_azimuth'
                    delta1 = abs(delta_azimuth1)
                    delta2 = abs(delta_azimuth2)
                    if abs(delta_azimuth1) > 90:
                        delta1 = 180 - abs(delta_azimuth1)
                    if abs(delta_azimuth2) > 90:
                        delta2 = 180 - abs(delta_azimuth2)

                    check = self.dlg.checkBox.checkState()
                    if check == 2:
                        if delta1 <= angle and delta2 <= angle:
                            if line1.geometry().length() >= line2.geometry().length():
                                polygon.geometry().rotate(delta_azimuth1,centroid.asPoint())
                            elif line1.geometry().length() < line2.geometry().length():
                                polygon.geometry().rotate(delta_azimuth2,centroid.asPoint())
                            elif line1.geometry().length() == line2.geometry().length():
                                if delta1 > delta2:
                                    polygon.geometry().rotate(delta_azimuth2,centroid.asPoint())
                                elif delta1 < delta2:
                                    polygon.geometry().rotate(delta_azimuth1,centroid.asPoint())
                                elif delta1 == delta2:
                                    polygon.geometry().rotate(delta_azimuth1,centroid.asPoint())
                        elif delta1 <= angle:
                            polygon.geometry().rotate(delta_azimuth1,centroid.asPoint())
                        elif delta2 <= angle:
                            polygon.geometry().rotate(delta_azimuth2,centroid.asPoint())
                    elif check == 0:
                        if delta1 <= angle and delta2 <= angle:
                            if delta1 > delta2:
                                polygon.geometry().rotate(delta_azimuth2,centroid.asPoint())
                            elif delta1 < delta2:
                                polygon.geometry().rotate(delta_azimuth1,centroid.asPoint())
                            elif delta1 == delta2:
                                polygon.geometry().rotate(delta_azimuth1,centroid.asPoint())
                        elif delta1 <= angle:
                            polygon.geometry().rotate(delta_azimuth1,centroid.asPoint())
                        elif delta2 <= angle:
                            polygon.geometry().rotate(delta_azimuth2,centroid.asPoint())
                selectedLayer_2.changeGeometry(polygon.id(),polygon.geometry())

            selectedLayer_2.triggerRepaint()
     
        self.dlg.comboBox.clear()
        self.dlg.comboBox_2.clear()
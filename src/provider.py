# -*- coding: utf-8 -*-

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


from qgis.core import QgsProcessingProvider
from .algorithm import PolygonsParallelToLineAlgorithm


class PolygonsParallelToLineProvider(QgsProcessingProvider):
    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(PolygonsParallelToLineAlgorithm())

    def id(self, *args, **kwargs):
        return "pptl"

    def name(self, *args, **kwargs):
        return self.tr("Polygons parallel to line")

    def icon(self):
        return QgsProcessingProvider.icon(self)

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


import os.path
import sys
import inspect

from qgis.core import QgsApplication
from .provider import PolygonsParallelToLineProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class PolygonsParallelToLinePlugin:
    def __init__(self):
        self.provider = None

    def initProcessing(self):
        self.provider = PolygonsParallelToLineProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)

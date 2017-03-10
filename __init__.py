# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PolygonsParallelToLine
                                 A QGIS plugin
 This plugin rotates polygons parallel to line
                             -------------------
        begin                : 2016-03-10
        copyright            : (C) 2016 by Andrey Lekarev
        email                : elfpkck@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PolygonsParallelToLine class from file PolygonsParallelToLine.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .polygons_parallel_to_line import PolygonsParallelToLine
    return PolygonsParallelToLine(iface)

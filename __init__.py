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

__author__ = 'Andrey Lekarev'
__date__ = '2016-03-10'
__copyright__ = '(C) 2016-2017 by Andrey Lekarev'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PolygonsParallelToLine class from file PolygonsParallelToLine.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .pptl import PolygonsParallelToLinePlugin
    return PolygonsParallelToLinePlugin(iface)

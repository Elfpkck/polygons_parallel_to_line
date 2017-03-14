# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PolygonsParallelToLineDialog
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

import os

from PyQt4 import QtGui, uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'polygons_parallel_to_line_dialog_base.ui'))


class PolygonsParallelToLineDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(PolygonsParallelToLineDialog, self).__init__(parent)

        self.setupUi(self)

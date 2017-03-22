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

__author__ = 'Andrey Lekarev'
__date__ = '2016-03-10'
__copyright__ = '(C) 2016-2017 by Andrey Lekarev'


from PyQt4.QtCore import QSettings

from qgis.core import QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import (ParameterVector, ParameterBoolean,
                                        ParameterNumber)
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector


class PolygonsParallelToLineAlgorithm(GeoAlgorithm):
    """This is an example algorithm that takes a vector layer and
    creates a new one just with just those features of the input
    layer that are selected.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT_LAYER = 'OUTPUT_LAYER'
    LINE_LAYER = 'LINE_LAYER'
    POLYGON_LAYER = 'POLYGON_LAYER'
    SELECTED = 'SELECTED'
    LONGEST = "LONGEST"
    DISTANCE = 'DISTANCE'
    ANGLE = 'ANGLE'


    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name = 'Polygons parallel to line'

        # The branch of the toolbox under which the algorithm will appear
        self.group = 'Algorithms for vector layers'

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterVector(self.LINE_LAYER,
                                          self.tr('Input line layer')))
        self.addParameter(
            ParameterVector(self.POLYGON_LAYER,
                            self.tr('Input polygon layer'),
                            [ParameterVector.VECTOR_TYPE_POLYGON])
        )
        self.addParameter(
            ParameterBoolean(self.SELECTED,
                             self.tr('Rotate only selected polygons'))
        )
        txt = "Rotate by longest edge if both angles between polygon edges " \
              "and line segment <= 'Angle value'"
        self.addParameter(ParameterBoolean(self.LONGEST, self.tr(txt)))
        self.addParameter(ParameterNumber(self.DISTANCE,
                                         self.tr("Distance from line")))
        self.addParameter(ParameterNumber(self.ANGLE,
                                          self.tr("Angle value"),
                                          maxValue=89.9))

        # We add a vector layer as output
        self.addOutput(OutputVector(self.OUTPUT_LAYER,
            self.tr('Output layer with rotated polygons')))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        inputFilename = self.getParameterValue(self.LINE_LAYER)

        output = self.getOutputValue(self.OUTPUT_LAYER)

        # Input layers vales are always a string with its location.
        # That string can be converted into a QGIS object (a
        # QgsVectorLayer in this case) using the
        # processing.getObjectFromUri() method.
        vectorLayer = dataobjects.getObjectFromUri(inputFilename)

        # And now we can process

        # First we create the output layer. The output value entered by
        # the user is a string containing a filename, so we can use it
        # directly
        settings = QSettings()
        systemEncoding = settings.value('/UI/encoding', 'System')
        provider = vectorLayer.dataProvider()
        writer = QgsVectorFileWriter(output, systemEncoding,
                                     provider.fields(),
                                     provider.geometryType(), provider.crs())

        # Now we take the features from input layer and add them to the
        # output. Method features() returns an iterator, considering the
        # selection that might exist in layer and the configuration that
        # indicates should algorithm use only selected features or all
        # of them
        features = vector.features(vectorLayer)
        for f in features:
            writer.addFeature(f)

        # There is nothing more to do here. We do not have to open the
        # layer that we have created. The framework will take care of
        # that, or will handle it if this algorithm is executed within
        # a complex model

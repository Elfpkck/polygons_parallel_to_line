from qgis._core import (
    QgsFeature,
    QgsGeometry,
    QgsLineString,
    QgsPoint,
    QgsPointXY,
    QgsProcessingOutputLayerDefinition,
    QgsVectorLayer,
    QgsMultiLineString,
)

from pptl_algorithm import PolygonsParallelToLineAlgorithm
from qgis import processing

import pydevd_pycharm


def test_pptl(qgis_processing):
    # pydevd_pycharm.settrace("host.docker.internal", port=53100, stdoutToServer=True, stderrToServer=True)

    v1 = QgsVectorLayer("linestring", "temp_line", "memory")
    pr = v1.dataProvider()
    f = QgsFeature()
    lines = [[-0.35567010309278346, 0.72422680412371132], [-0.36082474226804129, 0.00257731958762886]]
    f.setGeometry(QgsGeometry.fromPolyline(QgsLineString([QgsPoint(x, y) for x, y in lines])))
    pr.addFeature(f)
    v1.updateExtents()

    v2 = QgsVectorLayer("polygon", "temp_poly", "memory")
    pr = v2.dataProvider()
    f = QgsFeature()
    poly1 = [
        QgsPointXY(-0.10309278350515461, 0.33247422680412364),
        QgsPointXY(0.08762886597938135, 0.48711340206185572),
        QgsPointXY(0.35051546391752564, 0.05927835051546393),
        QgsPointXY(0.13917525773195871, -0.05412371134020622),
        QgsPointXY(-0.10309278350515461, 0.33247422680412364),
    ]

    f.setGeometry(QgsGeometry.fromPolygonXY([poly1]))
    pr.addFeature(f)
    v2.updateExtents()
    params = {
        "LINE_LAYER": v1,
        "POLYGON_LAYER": v2,
        "SELECTED": False,
        "WRITE_SELECTED": False,
        "LONGEST": False,
        "MULTI": False,
        "DISTANCE": 0,
        "ANGLE": 89,
        "OUTPUT_LAYER": QgsProcessingOutputLayerDefinition("TEMPORARY_OUTPUT"),
    }
    result = processing.run(PolygonsParallelToLineAlgorithm(), params)
    print(result)
    return result

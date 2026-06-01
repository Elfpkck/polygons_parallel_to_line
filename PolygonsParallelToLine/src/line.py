from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from qgis.core import QgsProcessingException, QgsSpatialIndex

if TYPE_CHECKING:
    from qgis.core import (
        QgsFeature,
        QgsGeometry,
        QgsPoint,
        QgsPointXY,
        QgsProcessingFeatureSource,
    )


class Line:
    def __init__(self, line_feature: QgsFeature):
        self.geom: QgsGeometry = line_feature.geometry()

    def get_closest_segment(self, point_xy: QgsPointXY) -> Segment:
        _, _, next_vertex_idx, _ = self.geom.closestSegmentWithContext(point_xy)
        start, end = self.geom.vertexAt(next_vertex_idx - 1), self.geom.vertexAt(next_vertex_idx)
        return Segment(start=start, end=end)


class LineLayer:
    def __init__(self, line_layer: QgsProcessingFeatureSource):
        self.id_line_map: dict[int, QgsFeature] = {x.id(): x for x in line_layer.getFeatures()}
        self.spatial_index = QgsSpatialIndex(flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        self.spatial_index.addFeatures(self.id_line_map.values())

    def get_closest_line(self, point: QgsPointXY) -> Line:
        closest_line_id = self.spatial_index.nearestNeighbor(point, 1)

        if not closest_line_id:
            msg = f"No lines found near point {point}"
            raise QgsProcessingException(msg)

        return Line(self.id_line_map[closest_line_id[0]])


class Segment:
    def __init__(self, start: QgsPoint, end: QgsPoint):
        self.start = start
        self.end = end

    @cached_property
    def length(self) -> float:
        return self.start.distance(self.end)

    @cached_property
    def azimuth(self) -> float:
        # QgsPoint.azimuth returns -180..180
        return self.start.azimuth(self.end)

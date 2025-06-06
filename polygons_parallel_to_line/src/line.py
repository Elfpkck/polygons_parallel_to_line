from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from qgis.core import QgsSpatialIndex

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
        self.feature: QgsFeature = line_feature
        self.geom: QgsGeometry = line_feature.geometry()

    def get_closest_segment(self, point_xy: QgsPointXY) -> Segment:
        _, _, next_vertex_idx, _ = self.geom.closestSegmentWithContext(point_xy)
        start, end = self.geom.vertexAt(next_vertex_idx - 1), self.geom.vertexAt(next_vertex_idx)
        return Segment(start, end)

    def calc_distance(self, geom: QgsGeometry) -> float:
        return self.geom.distance(geom)


class LineLayer:
    def __init__(self, line_layer: QgsProcessingFeatureSource):
        self.line_layer: QgsProcessingFeatureSource = line_layer
        self.id_line_map: dict[int, QgsFeature] = {x.id(): x for x in line_layer.getFeatures()}
        self.spatial_index: QgsSpatialIndex = QgsSpatialIndex(flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        self.spatial_index.addFeatures(line_layer.getFeatures())

    def get_closest_line(self, point: QgsPointXY) -> Line:
        closest_line_id = self.spatial_index.nearestNeighbor(point, 1)
        if not closest_line_id:
            raise ValueError(f"No lines found near point {point}")
        return Line(self.id_line_map[closest_line_id[0]])


class Segment:
    def __init__(self, start: QgsPoint, end: QgsPoint):
        self.start: QgsPoint = start
        self.end: QgsPoint = end

    @cached_property
    def length(self) -> float:
        # Not a regular attribute, because it may not be called at all  # TODO: docs
        return self.start.distance(self.end)

    @cached_property
    def azimuth(self) -> float:
        # Not a regular attribute, because it may not be called at all  # TODO: docs
        return self.start.azimuth(self.end)

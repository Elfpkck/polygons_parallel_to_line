from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING

from qgis.core import QgsGeometry, QgsSpatialIndex

if TYPE_CHECKING:
    from qgis.core import QgsFeature, QgsPointXY, QgsProcessingFeatureSource


class Line:
    def __init__(self, line: QgsFeature):
        self.line = line
        self.geom = line.geometry()
        self.is_multi = self.geom.isMultipart()
        self._strategy: LineStrategy = MultiLine() if self.is_multi else SingleLine()

    def get_closest_segment_azimuth(self, point: QgsPointXY) -> float:
        """azimuth() returns 0-180 and 0-(-180) values. 0 - north, 90 - east, 180 - south, -90 - west."""
        start, end = self._strategy.get_closest_segment(point, self.geom)
        return start.azimuth(end)

    def calc_distance(self, geom: QgsGeometry) -> float:
        return self.geom.distance(geom)


# TODO: as 2 functions?
class LineStrategy(ABC):
    @abstractmethod
    def get_closest_segment(self, point_xy: QgsPointXY, geom: QgsGeometry) -> tuple[QgsPointXY, QgsPointXY]:
        pass


class SingleLine(LineStrategy):
    def get_closest_segment(self, point_xy: QgsPointXY, geom: QgsGeometry) -> tuple[QgsPointXY, QgsPointXY]:
        _, _, next_vertex_idx, _ = geom.closestSegmentWithContext(point_xy)
        return geom.vertexAt(next_vertex_idx - 1), geom.vertexAt(next_vertex_idx)


class MultiLine(LineStrategy):
    def get_closest_segment(self, point_xy: QgsPointXY, geom: QgsGeometry) -> tuple[QgsPointXY, QgsPointXY]:
        closest_line_geom, next_vertex_idx = None, None
        min_distance = float("inf")

        for line_geom in geom.asGeometryCollection():
            distance, _, temp_next_vertex_idx, _ = line_geom.closestSegmentWithContext(point_xy)

            if distance < min_distance:
                closest_line_geom = line_geom
                next_vertex_idx = temp_next_vertex_idx
                min_distance = distance

        if closest_line_geom is None or next_vertex_idx is None:
            raise ValueError(f"No lines found near point {point_xy}")

        return closest_line_geom.vertexAt(next_vertex_idx - 1), closest_line_geom.vertexAt(next_vertex_idx)


class LineLayer:
    def __init__(self, line_layer: QgsProcessingFeatureSource):
        self.line_layer = line_layer
        self.id_line_map = {x.id(): x for x in line_layer.getFeatures()}
        self.spatial_index = QgsSpatialIndex(flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        self.spatial_index.addFeatures(line_layer.getFeatures())

    def get_closest_line(self, point: QgsPointXY) -> Line:
        closest_line_id = self.spatial_index.nearestNeighbor(point, 1)
        if not closest_line_id:
            raise ValueError(f"No lines found near point {point}")
        return Line(self.id_line_map[closest_line_id[0]])


# TODO: this is the same as what get_closest_segment() returns? unite
class Edge:
    def __init__(self, start_xy: QgsPointXY, end_xy: QgsPointXY):
        self.start_xy = start_xy
        self.end_xy = end_xy

    @cached_property
    def length(self) -> float:
        # Not a regular attribute, because it may not be called at all  # TODO: docs
        return self.start_xy.distance(self.end_xy)

    @cached_property
    def azimuth(self) -> float:
        # Not a regular attribute, because it may not be called at all  # TODO: docs
        return self.start_xy.azimuth(self.end_xy)

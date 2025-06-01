from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING

from qgis.core import QgsGeometry, QgsPoint, QgsSpatialIndex

if TYPE_CHECKING:
    from qgis.core import QgsFeature, QgsPointXY, QgsProcessingFeatureSource


class Line(ABC):
    def __init__(self, geometry: QgsGeometry):
        self.geom = geometry
        self.polyline = self.get_polyline_xy()

    @abstractmethod
    def get_polyline_xy(self) -> list[list[QgsPointXY]]:
        pass

    @abstractmethod
    def get_closest_segment(self, point: QgsPointXY) -> tuple[QgsPointXY, QgsPointXY]:
        pass

    @cached_property
    def length(self) -> float:
        return self.geom.length()

    def get_closest_segment_azimuth(self, point: QgsPointXY) -> float:
        """azimuth() returns 0-180 and 0-(-180) values. 0 - north, 90 - east, 180 - south, -90 - west."""
        start, end = self.get_closest_segment(point)
        return start.azimuth(end)

    def calc_distance(self, geom: QgsGeometry) -> float:
        return self.geom.distance(geom)


class SingleLine(Line):
    def get_polyline_xy(self) -> list[list[QgsPointXY]]:
        return [self.geom.asPolyline()]

    def get_closest_segment(self, point: QgsPointXY) -> tuple[QgsPointXY, QgsPointXY]:
        _, _, next_vertex_idx, _ = self.geom.closestSegmentWithContext(point)
        return self.polyline[0][next_vertex_idx - 1], self.polyline[0][next_vertex_idx]

    def get_line_azimuth(self) -> float:
        return self.polyline[0][0].azimuth(self.polyline[0][1])


class MultiLine(Line):
    def get_polyline_xy(self) -> list[list[QgsPointXY]]:
        return self.geom.asMultiPolyline()

    def get_closest_segment(self, point: QgsPointXY) -> tuple[QgsPointXY, QgsPointXY]:
        closest_line, next_vertex_idx = None, None
        min_distance = float("inf")

        for line in self.polyline:
            line_geom = QgsGeometry.fromPolyline([QgsPoint(x) for x in line])
            distance, _, current_next_vertex_idx, _ = line_geom.closestSegmentWithContext(point)

            if distance < min_distance:
                closest_line = line
                next_vertex_idx = current_next_vertex_idx
                min_distance = distance

        if closest_line is None or next_vertex_idx is None:
            raise ValueError(f"No lines found near point {point}")

        return closest_line[next_vertex_idx - 1], closest_line[next_vertex_idx]


def line_factory(line_geometry: QgsGeometry) -> Line:
    return MultiLine(line_geometry) if line_geometry.isMultipart() else SingleLine(line_geometry)


class LineLayer:
    def __init__(self, line_layer: QgsProcessingFeatureSource):
        self.line_layer = line_layer
        self.id_line_map = {x.id(): x for x in line_layer.getFeatures()}
        self.spatial_index = QgsSpatialIndex(flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        self.spatial_index.addFeatures(line_layer.getFeatures())

    def get_closest_line(self, point: QgsPointXY) -> QgsFeature:
        closest_line_id = self.spatial_index.nearestNeighbor(point, 1)
        if not closest_line_id:
            raise ValueError(f"No lines found near point {point}")
        return self.id_line_map[closest_line_id[0]]

    def get_closest_line_geom(self, point: QgsPointXY) -> Line:
        return line_factory(self.get_closest_line(point).geometry())

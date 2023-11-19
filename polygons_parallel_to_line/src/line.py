from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING

from qgis.core import QgsGeometry, QgsPoint, QgsSpatialIndex

if TYPE_CHECKING:
    from qgis.core import QgsFeature, QgsPointXY, QgsProcessingFeatureSource


class Line(ABC):
    def __init__(self, geometry: QgsGeometry, is_multi: bool):
        self.geom = geometry
        self.is_multi = is_multi
        self.polyline = self.get_polyline_xy()

    @abstractmethod
    def get_polyline_xy(self) -> list[list[QgsPointXY]]:
        pass

    @abstractmethod
    def get_closest_segment(self, point: QgsPointXY) -> tuple[QgsPointXY, QgsPointXY]:
        pass

    @abstractmethod
    def get_line_azimuth(self) -> float:
        pass

    @cached_property
    def length(self) -> float:
        return self.geom.length()

    def get_closest_segment_azimuth(self, point: QgsPointXY) -> float:
        """azimuth() returns 0-180 and 0-(-180) values. 0 - north, 90 - east, 180 - south, -90 - west."""
        start, end = self.get_closest_segment(point)
        return start.azimuth(end)

    def get_distance(self, geom: QgsGeometry) -> float:
        return self.geom.distance(geom)


class SimpleLine(Line):
    def get_polyline_xy(self) -> list[list[QgsPointXY]]:
        return [self.geom.asPolyline()]

    def get_closest_segment(self, point: QgsPointXY) -> tuple[QgsPointXY, QgsPointXY]:
        _, _, greater_point_index, _ = self.geom.closestSegmentWithContext(point)
        return self.polyline[0][greater_point_index - 1], self.polyline[0][greater_point_index]

    def get_line_azimuth(self) -> float:
        return self.polyline[0][0].azimuth(self.polyline[0][1])


class MultiLine(Line):
    def get_polyline_xy(self) -> list[list[QgsPointXY]]:
        return self.geom.asMultiPolyline()

    def get_closest_segment(self, point: QgsPointXY) -> tuple[QgsPointXY, QgsPointXY]:
        line_distances = {}

        for item in self.polyline:
            line = QgsGeometry.fromPolyline([QgsPoint(x) for x in item])
            min_dist, _, greater_point_index, _ = line.closestSegmentWithContext(point)
            line_distances[min_dist] = (item, greater_point_index)

        min_distance = min(line_distances)
        line_, end_index = line_distances[min_distance]
        return line_[end_index - 1], line_[end_index]

    def get_line_azimuth(self) -> float:
        """Not supposed to be used."""
        raise NotImplementedError("MultiLine.get_line_azimuth() is not implemented")


def line_factory(line_geometry: QgsGeometry) -> Line:
    if line_geometry.isMultipart():
        return MultiLine(line_geometry, is_multi=True)
    return SimpleLine(line_geometry, is_multi=False)


class LineLayer:
    def __init__(self, line_layer: QgsProcessingFeatureSource):
        self.line_layer = line_layer
        self.id_line_map = {x.id(): x for x in line_layer.getFeatures()}
        self.spatial_index = QgsSpatialIndex(flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        self.spatial_index.addFeatures(line_layer.getFeatures())

    def get_closest_line(self, point: QgsPointXY) -> QgsFeature:
        closest_line_id = self.spatial_index.nearestNeighbor(point, 1)
        return self.id_line_map[closest_line_id[0]]

    def get_closest_line_geom(self, point: QgsPointXY) -> Line:
        return line_factory(self.get_closest_line(point).geometry())

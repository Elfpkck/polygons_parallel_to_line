from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING

from qgis.core import QgsGeometry, QgsPoint, QgsSpatialIndex

if TYPE_CHECKING:
    from qgis.core import QgsFeature, QgsPointXY, QgsProcessingFeatureSource


class Line:
    def __init__(self, line: QgsFeature):
        self.line = line
        self.geom = line.geometry()
        self.is_multi = self.geom.isMultipart()
        self._strategy: LineStrategy = MultiLine(self) if self.is_multi else SingleLine(self)

    def get_closest_segment_azimuth(self, point: QgsPointXY) -> float:
        """azimuth() returns 0-180 and 0-(-180) values. 0 - north, 90 - east, 180 - south, -90 - west."""
        start, end = self._strategy.get_closest_segment(point)
        return start.azimuth(end)

    def calc_distance(self, geom: QgsGeometry) -> float:
        return self.geom.distance(geom)


class LineStrategy(ABC):
    def __init__(self, context: Line):
        self.context = context

    @property
    @abstractmethod
    def polyline_xy(self) -> list[list[QgsPointXY]]:
        pass

    @abstractmethod
    def get_closest_segment(self, point: QgsPointXY) -> tuple[QgsPointXY, QgsPointXY]:
        pass


class SingleLine(LineStrategy):
    @cached_property
    def polyline_xy(self) -> list[list[QgsPointXY]]:
        # not a regular instance variable as may not be called at all?  #TODO: docs
        return [self.context.geom.asPolyline()]

    def get_closest_segment(self, point: QgsPointXY) -> tuple[QgsPointXY, QgsPointXY]:
        _, _, next_vertex_idx, _ = self.context.geom.closestSegmentWithContext(point)
        return self.polyline_xy[0][next_vertex_idx - 1], self.polyline_xy[0][next_vertex_idx]


class MultiLine(LineStrategy):
    # TODO: do I need polyline_xy at all? maybe, possible to use self.context.geom only?
    @cached_property
    def polyline_xy(self) -> list[list[QgsPointXY]]:
        return self.context.geom.asMultiPolyline()

    def get_closest_segment(self, point: QgsPointXY) -> tuple[QgsPointXY, QgsPointXY]:
        closest_line_xy, next_vertex_idx = None, None
        min_distance = float("inf")

        for line_xy in self.polyline_xy:
            # TODO: cache? and look for similar
            line_geom = QgsGeometry.fromPolylineXY(line_xy)
            distance, _, current_next_vertex_idx, _ = line_geom.closestSegmentWithContext(point)

            if distance < min_distance:
                closest_line_xy = line_xy
                next_vertex_idx = current_next_vertex_idx
                min_distance = distance

        if closest_line_xy is None or next_vertex_idx is None:
            raise ValueError(f"No lines found near point {point}")

        return closest_line_xy[next_vertex_idx - 1], closest_line_xy[next_vertex_idx]


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
        self.geom = QgsGeometry.fromPolyline([QgsPoint(start_xy), QgsPoint(end_xy)])

    @cached_property
    def length(self) -> float:
        # Not a regular attribute, because it may not be called at all  # TODO: docs
        return self.geom.length()

    @cached_property
    def polyline(self):  # TODO: name
        # Not a regular attribute, because it may not be called at all  # TODO: docs
        return self.geom.asPolyline()

    def get_line_azimuth(self) -> float:
        # TODO: possible to use self.geom only?
        return self.polyline[0].azimuth(self.polyline[1])

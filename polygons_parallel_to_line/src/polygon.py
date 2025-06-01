from __future__ import annotations

import abc
from functools import cached_property
from typing import TYPE_CHECKING

from qgis.core import QgsGeometry, QgsPoint

from .line import SimpleLine

if TYPE_CHECKING:
    from qgis.core import QgsFeature, QgsPointXY


# TODO: a dataclasss/class for vertex?


class ClosestPolygonPart:
    def __init__(self, vertexes: list[QgsPointXY], closest_line_geom: QgsGeometry):
        self.vertexes = vertexes
        self.closest_line_geom = closest_line_geom
        self.min_distance, self.closest_vertex_index = self._calc_closest_vertex_info()
        self.closest_vertex = vertexes[self.closest_vertex_index]

    def _calc_closest_vertex_info(self) -> tuple[float, int]:
        min_distance = float("inf")
        closest_vertex_index = None

        for i, vertex in enumerate(self.vertexes):
            distance_to_line = QgsGeometry.fromPointXY(vertex).distance(self.closest_line_geom)

            if distance_to_line < min_distance:
                min_distance = distance_to_line
                closest_vertex_index = i

        if closest_vertex_index is None:
            raise ValueError("No vertex found in the polygon")

        return min_distance, closest_vertex_index

    @cached_property
    def closest_edges_pair(self) -> tuple[SimpleLine, SimpleLine]:
        if self.closest_vertex_index == len(self.vertexes) - 1:  # if vertex is last
            edge_1_end_idx, edge_2_end_idx = 0, -2
        else:
            edge_1_end_idx, edge_2_end_idx = self.closest_vertex_index + 1, self.closest_vertex_index - 1

        start = QgsPoint(self.closest_vertex)
        edge_1 = QgsGeometry.fromPolyline([start, QgsPoint(self.vertexes[edge_1_end_idx])])
        edge_2 = QgsGeometry.fromPolyline([start, QgsPoint(self.vertexes[edge_2_end_idx])])
        return SimpleLine(edge_1), SimpleLine(edge_2)


class Polygon(abc.ABC):
    def __init__(self, polygon: QgsFeature):
        self.poly = polygon
        self.is_multi = self._initialize_is_multi()
        self.geom = polygon.geometry()
        self.center = self.geom.centroid().asPoint()
        self.vertexes = self.get_vertexes()  # TODO: rename. It's parts' vertexes
        self.is_rotated = False

    @abc.abstractmethod
    def _initialize_is_multi(self) -> bool:
        """Return the value for is_multi"""

    @abc.abstractmethod
    def get_vertexes(self) -> list[list[QgsPointXY]]:
        """Without the last vertex, which is the same as the first one."""

    def get_closest_part(self, closest_line_geom: QgsGeometry) -> ClosestPolygonPart:
        """If the polygon is multipart, return the closest vertex from all parts."""  # TODO: docs
        closest_part = None
        min_distance = float("inf")

        for part in self.vertexes:
            polygon_part = ClosestPolygonPart(part, closest_line_geom)

            if polygon_part.min_distance < min_distance:
                closest_part = polygon_part
                min_distance = polygon_part.min_distance

        if closest_part is None:  # TODO
            raise ValueError("No parts found in the polygon")

        return closest_part


class SimplePolygon(Polygon):
    def _initialize_is_multi(self) -> bool:
        return False

    def get_vertexes(self) -> list[list[QgsPointXY]]:
        return [self.geom.asPolygon()[0][:-1]]


class MultiPolygon(Polygon):
    def _initialize_is_multi(self) -> bool:
        return True

    def get_vertexes(self) -> list[list[QgsPointXY]]:
        return [part[0][:-1] for part in self.geom.asMultiPolygon()]


def polygon_factory(polygon: QgsFeature) -> Polygon:
    return MultiPolygon(polygon) if polygon.geometry().isMultipart() else SimplePolygon(polygon)

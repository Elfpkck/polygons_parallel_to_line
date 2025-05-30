from __future__ import annotations

import abc
from typing import TYPE_CHECKING

from qgis.core import QgsGeometry, QgsPoint

from .line import SimpleLine

if TYPE_CHECKING:
    from qgis.core import QgsFeature, QgsPointXY


class ClosestPolygonPart:
    def __init__(self, vertexes: list[QgsPointXY], closest_line_geom: QgsGeometry):
        self.vertexes = vertexes
        self.closest_line_geom = closest_line_geom
        self.distance, self.closest_vertex_index, self.closest_vertex = self._get_closest_vertex()

    def _get_closest_vertex(self) -> tuple[float, int, QgsPointXY]:
        vertexes: dict[float, tuple[int, QgsPointXY]] = {}
        for i, vertex in enumerate(self.vertexes):
            vertex_geom = QgsGeometry.fromPointXY(vertex)
            distance_to_line = vertex_geom.distance(self.closest_line_geom)
            vertexes[distance_to_line] = (i, vertex)

        if not vertexes:  # TODO: check all new raises
            raise ValueError("No vertices found in polygon part")

        min_distance = min(vertexes)
        closest_vertex_index, closest_vertex = vertexes[min_distance]
        return min_distance, closest_vertex_index, closest_vertex

    def get_closest_edges(self) -> tuple[SimpleLine, SimpleLine]:
        if self.closest_vertex_index == 0:  # if vertex is first
            edge_1_end_idx, edge_2_end_idx = 1, -1
        elif self.closest_vertex_index == len(self.vertexes) - 1:  # if vertex is last
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
        self.vertexes = self.get_vertexes()

    @abc.abstractmethod
    def _initialize_is_multi(self) -> bool:
        """Return the value for is_multi"""

    @abc.abstractmethod
    def get_vertexes(self) -> list[list[QgsPointXY]]:
        """Without the last vertex, which is the same as the first one."""

    def get_closest_part(self, closest_line_geom: QgsGeometry) -> ClosestPolygonPart:
        """If the polygon is multipart, return the closest vertex from all parts."""
        polygon_parts = {}
        for part in self.vertexes:
            polygon_part = ClosestPolygonPart(part, closest_line_geom)
            polygon_parts[polygon_part.distance] = polygon_part

        if not polygon_parts:
            raise ValueError("No polygon parts found")

        return polygon_parts[min(polygon_parts)]


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

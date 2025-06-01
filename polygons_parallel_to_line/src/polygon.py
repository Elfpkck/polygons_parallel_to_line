from __future__ import annotations

import abc
from functools import cached_property
from typing import TYPE_CHECKING

from qgis.core import QgsGeometry, QgsPoint

from .line import SingleLine

if TYPE_CHECKING:
    from qgis.core import QgsFeature, QgsPointXY


class ClosestSinglePolygon:
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
    def closest_edges_pair(self) -> tuple[SingleLine, SingleLine]:
        if self.closest_vertex_index == len(self.vertexes) - 1:  # if vertex is last
            edge_1_end_idx, edge_2_end_idx = 0, -2
        else:
            edge_1_end_idx, edge_2_end_idx = self.closest_vertex_index + 1, self.closest_vertex_index - 1

        start = QgsPoint(self.closest_vertex)
        edge_1 = QgsGeometry.fromPolyline([start, QgsPoint(self.vertexes[edge_1_end_idx])])
        edge_2 = QgsGeometry.fromPolyline([start, QgsPoint(self.vertexes[edge_2_end_idx])])
        return SingleLine(edge_1), SingleLine(edge_2)


class Polygon(abc.ABC):
    def __init__(self, polygon: QgsFeature):
        self.poly = polygon
        self.is_multi = self._initialize_is_multi()
        self.geom = polygon.geometry()
        self.center = self.geom.centroid().asPoint()
        self.single_polygons_vertexes = self.as_single_polygons_vertexes()
        self.is_rotated = False

    @abc.abstractmethod
    def _initialize_is_multi(self) -> bool:
        """Return the value for is_multi"""

    @abc.abstractmethod
    def as_single_polygons_vertexes(self) -> list[list[QgsPointXY]]:
        """Without the last vertex, which is the same as the first one."""

    def get_closest_part(self, closest_line_geom: QgsGeometry) -> ClosestSinglePolygon:
        """If the polygon is multipart, return the closest vertex from all parts."""  # TODO: docs
        closest_single_poly = None
        min_distance = float("inf")

        for single_poly_vertexes in self.single_polygons_vertexes:
            single_poly = ClosestSinglePolygon(single_poly_vertexes, closest_line_geom)

            if single_poly.min_distance < min_distance:
                closest_single_poly = single_poly
                min_distance = single_poly.min_distance

        if closest_single_poly is None:  # TODO
            raise ValueError("No parts found in the polygon")

        return closest_single_poly


class SinglePolygon(Polygon):
    def _initialize_is_multi(self) -> bool:
        return False

    def as_single_polygons_vertexes(self) -> list[list[QgsPointXY]]:
        return [self.geom.asPolygon()[0][:-1]]


class MultiPolygon(Polygon):
    def _initialize_is_multi(self) -> bool:
        return True

    def as_single_polygons_vertexes(self) -> list[list[QgsPointXY]]:
        return [part[0][:-1] for part in self.geom.asMultiPolygon()]


def polygon_factory(polygon: QgsFeature) -> Polygon:
    return MultiPolygon(polygon) if polygon.geometry().isMultipart() else SinglePolygon(polygon)

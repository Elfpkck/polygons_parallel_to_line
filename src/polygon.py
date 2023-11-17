from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.core import QgsGeometry, QgsPoint
import abc
from .line import line_factory


if TYPE_CHECKING:
    from qgis.core import QgsFeature
    from .line import Line


class ClosestPolygonPart:
    def __init__(self, vertexes, closest_line_geom):
        self.vertexes = vertexes
        self.closest_line_geom = closest_line_geom
        self.distance, self.closest_vertex_index, self.closest_vertex = self._get_closest_vertex()

    def _get_closest_vertex(self) -> tuple:
        vertexes = {}
        for i, vertex in enumerate(self.vertexes):
            vertex_geom = QgsGeometry.fromPointXY(vertex)
            distance_to_line = vertex_geom.distance(self.closest_line_geom)
            vertexes[distance_to_line] = (i, vertex)

        min_distance = min(vertexes)
        return min_distance, *vertexes[min_distance]

    def get_closest_edges(self) -> tuple[Line, Line]:
        start = QgsPoint(self.closest_vertex)

        if self.closest_vertex_index == 0:  # if vertex is first
            edge1 = QgsGeometry.fromPolyline([start, QgsPoint(self.vertexes[1])])
            edge2 = QgsGeometry.fromPolyline([start, QgsPoint(self.vertexes[-1])])
        elif self.closest_vertex_index == len(self.vertexes) - 1:  # if vertex is last
            edge1 = QgsGeometry.fromPolyline([start, QgsPoint(self.vertexes[0])])
            edge2 = QgsGeometry.fromPolyline([start, QgsPoint(self.vertexes[-2])])
        else:
            edge1 = QgsGeometry.fromPolyline([start, QgsPoint(self.vertexes[self.closest_vertex_index + 1])])
            edge2 = QgsGeometry.fromPolyline([start, QgsPoint(self.vertexes[self.closest_vertex_index - 1])])
        return line_factory(edge1), line_factory(edge2)


class Polygon(abc.ABC):
    def __init__(self, polygon: QgsFeature, *, is_multi: bool):
        self.poly = polygon
        self.is_multi = is_multi
        self.geom = polygon.geometry()
        self.center = self.geom.centroid().asPoint()
        self.vertexes = self.get_vertexes()

    @abc.abstractmethod
    def get_vertexes(self) -> list:
        """Without the last vertex which is the same as the first one."""
        pass

    def get_closest_part(self, closest_line_geom) -> ClosestPolygonPart:
        """If polygon is multipart, return the closest vertex from all parts."""
        polygon_parts = {}
        for part in self.vertexes:
            polygon_part = ClosestPolygonPart(part, closest_line_geom)
            polygon_parts[polygon_part.distance] = polygon_part

        return polygon_parts[min(polygon_parts)]


class SimplePolygone(Polygon):
    def get_vertexes(self) -> list:
        return [self.geom.asPolygon()[0][:-1]]


class MultiPolygon(Polygon):
    def get_vertexes(self) -> list:
        return [part[0][:-1] for part in self.geom.asMultiPolygon()]


def polygon_factory(polygon) -> Polygon:
    if polygon.geometry().isMultipart():
        return MultiPolygon(polygon, is_multi=True)
    else:
        return SimplePolygone(polygon, is_multi=False)

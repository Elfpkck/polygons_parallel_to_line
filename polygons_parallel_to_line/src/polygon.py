from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from qgis.core import QgsGeometry

from .line import Edge

if TYPE_CHECKING:
    from qgis.core import QgsFeature

    from .line import Line


class ClosestSinglePolygon:
    def __init__(self, single_poly_geom: QgsGeometry, closest_line: Line):
        self.single_poly_geom = single_poly_geom
        self.closest_line = closest_line
        self.min_distance, self.closest_vertex_index = self._calc_closest_vertex_info()
        self.closest_vertex = single_poly_geom.vertexAt(self.closest_vertex_index)

    def _calc_closest_vertex_info(self) -> tuple[float, int]:
        min_distance = float("inf")
        closest_vertex_index = None

        # TODO: deal with first and the last vertex are the same but different indexes
        for i, vertex_poly in enumerate(self.single_poly_geom.vertices()):
            distance_to_line = QgsGeometry.fromPoint(vertex_poly).distance(self.closest_line.geom)

            if distance_to_line < min_distance:
                min_distance = distance_to_line
                closest_vertex_index = i

        if closest_vertex_index is None:
            raise ValueError("No vertex found in the polygon")

        return min_distance, closest_vertex_index

    @cached_property
    def closest_edges_pair(self) -> tuple[Edge, Edge]:
        end_1, end_2 = self.single_poly_geom.adjacentVertices(self.closest_vertex_index)
        return (
            Edge(self.closest_vertex, self.single_poly_geom.vertexAt(end_1)),
            Edge(self.closest_vertex, self.single_poly_geom.vertexAt(end_2)),
        )


class Polygon:
    def __init__(self, polygon: QgsFeature):
        self.poly = polygon
        self.geom = polygon.geometry()
        self.is_multi = self.geom.isMultipart()
        self.center = self.geom.centroid().asPoint()
        self.is_rotated = False

    def get_closest_single_poly(self, closest_line: Line) -> ClosestSinglePolygon:
        """If the polygon is multipart, return the closest vertex from all parts."""  # TODO: docs
        closest_single_poly = None
        min_distance = float("inf")

        for single_poly_geom in self.geom.asGeometryCollection():
            single_poly = ClosestSinglePolygon(single_poly_geom, closest_line)

            if single_poly.min_distance < min_distance:
                closest_single_poly = single_poly
                min_distance = single_poly.min_distance

        if closest_single_poly is None:  # TODO
            raise ValueError("No parts found in the polygon")

        return closest_single_poly

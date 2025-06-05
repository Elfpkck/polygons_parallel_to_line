from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.core import Qgis

from .line import Segment

if TYPE_CHECKING:
    from qgis.core import QgsFeature, QgsPoint

    from .line import Line


class Polygon:
    def __init__(self, polygon_feature: QgsFeature):
        self.feature = polygon_feature
        self.geom = polygon_feature.geometry()
        self.is_multi = self.geom.isMultipart()
        self.center = self.geom.centroid().asPoint()
        self.is_rotated = False

    def find_closest_vertex(self, closest_line: Line) -> QgsPoint:
        nearest_point_on_line = closest_line.geom.nearestPoint(self.geom)
        _, closest_vertex_idx = self.geom.closestVertexWithContext(nearest_point_on_line.asPoint())
        return self.geom.vertexAt(closest_vertex_idx)

    def get_adjacent_segments(self, target_vertex: QgsPoint) -> tuple[Segment, Segment]:
        for geometry_part in self.geom.asGeometryCollection():
            for i, current_vertex in enumerate(geometry_part.vertices()):
                if current_vertex == target_vertex:
                    prev_vertex_idx, next_vertex_idx = geometry_part.adjacentVertices(i)
                    return (
                        Segment(target_vertex, geometry_part.vertexAt(prev_vertex_idx)),
                        Segment(target_vertex, geometry_part.vertexAt(next_vertex_idx)),
                    )

        raise ValueError(f"Vertex {target_vertex} not found in polygon {self.feature.id()}")

    def rotate(self, angle: float) -> Qgis.GeometryOperationResult:
        """QgsGeometry.rotate() takes any positive and negative values. Positive - rotate clockwise,
        negative - counterclockwise.
        """
        result = self.geom.rotate(angle, self.center)
        if result == Qgis.GeometryOperationResult.Success:
            self.feature.setGeometry(self.geom)
            self.is_rotated = True

        return result

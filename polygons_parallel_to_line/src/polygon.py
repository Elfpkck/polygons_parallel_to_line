from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.core import Qgis

from .line import Segment

if TYPE_CHECKING:
    from qgis.core import QgsFeature, QgsGeometry, QgsPoint, QgsPointXY

    from .line import Line


class Polygon:
    def __init__(self, polygon_feature: QgsFeature):
        self.feature: QgsFeature = polygon_feature
        self.geom: QgsGeometry = polygon_feature.geometry()
        self.is_multi: bool = self.geom.isMultipart()
        self.center_xy: QgsPointXY = self.geom.centroid().asPoint()
        self.is_rotated: bool = False

    def get_closest_vertex(self, closest_line: Line) -> QgsPoint:
        nearest_point_on_line_geom = closest_line.geom.nearestPoint(self.geom)
        _, closest_vertex_idx = self.geom.closestVertexWithContext(nearest_point_on_line_geom.asPoint())
        return self.geom.vertexAt(closest_vertex_idx)

    def get_adjacent_segments(self, target_vertex: QgsPoint) -> tuple[Segment, Segment]:
        for part_geom in self.geom.asGeometryCollection():
            for i, current_vertex in enumerate(part_geom.vertices()):
                if current_vertex == target_vertex:
                    prev_vertex_idx, next_vertex_idx = part_geom.adjacentVertices(i)
                    return (
                        Segment(target_vertex, part_geom.vertexAt(prev_vertex_idx)),
                        Segment(target_vertex, part_geom.vertexAt(next_vertex_idx)),
                    )

        raise ValueError(f"Vertex {target_vertex} not found in polygon {self.feature.id()}")

    def rotate(self, angle: float) -> Qgis.GeometryOperationResult:
        """QgsGeometry.rotate() takes any positive and negative values. Positive - rotate clockwise,
        negative - counterclockwise.
        """
        result = self.geom.rotate(angle, self.center_xy)
        if result == Qgis.GeometryOperationResult.Success:
            self.feature.setGeometry(self.geom)
            self.is_rotated = True

        return result

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from qgis.core import Qgis, QgsGeometry, QgsProcessingException

from .reference import Segment

if TYPE_CHECKING:
    from qgis.core import QgsFeature, QgsPoint, QgsPointXY

    from .reference import ReferenceFeature


class Polygon:
    def __init__(self, polygon_feature: QgsFeature):
        self.feature = polygon_feature
        self.geom: QgsGeometry = polygon_feature.geometry()
        self.is_multi: bool = self.geom.isMultipart()
        self.is_rotated: bool = False

    @cached_property
    def center_xy(self) -> QgsPointXY:
        return self.geom.centroid().asPoint()

    def get_closest_vertex(self, closest_reference: ReferenceFeature) -> QgsPoint:
        nearest_point_on_ref = closest_reference.geom.nearestPoint(self.geom)
        _, closest_vertex_idx = self.geom.closestVertexWithContext(nearest_point_on_ref.asPoint())
        return self.geom.vertexAt(closest_vertex_idx)

    def get_adjacent_segments(self, target_vertex: QgsPoint) -> tuple[Segment, Segment]:
        # Strip interior rings and duplicate nodes on a copy so they don't influence the
        # rotation pivot; the original geom is preserved for the actual rotate.
        temp_geom = QgsGeometry(self.geom)
        temp_geom.removeInteriorRings()
        temp_geom.removeDuplicateNodes()

        for part_geom in temp_geom.asGeometryCollection():
            for i, current_vertex in enumerate(part_geom.vertices()):
                if current_vertex == target_vertex:
                    prev_vertex_idx, next_vertex_idx = part_geom.adjacentVertices(i)
                    return (
                        Segment(start=target_vertex, end=part_geom.vertexAt(prev_vertex_idx)),
                        Segment(start=target_vertex, end=part_geom.vertexAt(next_vertex_idx)),
                    )

        msg = f"Vertex {target_vertex} not found in polygon {self.feature.id()}"
        raise QgsProcessingException(msg)

    def rotate(self, angle: float) -> None:
        # QgsGeometry.rotate: positive angle = clockwise, negative = counterclockwise.
        result = self.geom.rotate(angle, self.center_xy)
        if result == Qgis.GeometryOperationResult.Success:
            self.feature.setGeometry(self.geom)
            self.is_rotated = True

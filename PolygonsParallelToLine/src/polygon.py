from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.core import Qgis, QgsGeometry, QgsProcessingException

from .line import Segment

if TYPE_CHECKING:
    from qgis.core import QgsFeature, QgsPoint, QgsPointXY

    from .line import Line


class Polygon:
    """
    Represents a polygon geometry and provides methods to perform various geometric operations such as
    retrieving vertices, adjacent segments, and applying rotations.

    This class encapsulates a polygon feature from a geographic dataset using the `QgsFeature` and `QgsGeometry`
    structures provided by QGIS. It exposes information about the polygon, such as its geometric representation,
    whether it is multipart, its centroid, and its rotation status.

    :ivar feature: The underlying QGIS feature representing the polygon.
    :type feature: QgsFeature
    :ivar geom: The geometry of the polygon derived from the feature.
    :type geom: QgsGeometry
    :ivar is_multi: Boolean indicating whether the polygon is multipart.
    :type is_multi: bool
    :ivar center_xy: The centroid of the polygon in x-y coordinates.
    :type center_xy: QgsPointXY
    :ivar is_rotated: Boolean indicating if the polygon has been rotated.
    :type is_rotated: bool
    """

    def __init__(self, polygon_feature: QgsFeature):
        self.feature = polygon_feature
        self.geom: QgsGeometry = polygon_feature.geometry()
        self.is_multi: bool = self.geom.isMultipart()
        self.center_xy: QgsPointXY = self.geom.centroid().asPoint()
        self.is_rotated: bool = False

    def get_closest_vertex(self, closest_line: Line) -> QgsPoint:
        """
        Computes the closest vertex on the geometry associated with the calling object to a specified line geometry.
        The computation identifies the point on the line geometry nearest to the geometry of the calling object, and
        subsequently retrieves the closest vertex on the calling object's geometry to that point.

        :param closest_line: The line geometry which shall be used to determine the closest vertex on the geometry of
            the calling object.
        :return: A QgsPoint object representing the closest vertex on the geometry of the calling object to
            the nearest point on the specified line geometry.
        """
        nearest_point_on_line_geom = closest_line.geom.nearestPoint(self.geom)
        _, closest_vertex_idx = self.geom.closestVertexWithContext(nearest_point_on_line_geom.asPoint())
        return self.geom.vertexAt(closest_vertex_idx)

    def get_adjacent_segments(self, target_vertex: QgsPoint) -> tuple[Segment, Segment]:
        """
        Finds and retrieves the two segments adjacent to a given vertex within a geometry.

        The method processes the geometry associated with a feature by cleaning it up, removing interior rings as
        well as duplicate nodes, and then checking each geometry part for adjacency to the provided target vertex.
        It identifies the indices of the vertices adjacent to the target vertex and constructs the corresponding
        segments.

        :param target_vertex: The vertex for which the adjacent segments need to be determined, represented as a
            QgsPoint.
        :return: A tuple containing two Segment objects. Each Segment represents a start and end vertex adjacent to
            the passed target_vertex.
        :rtype: tuple[Segment, Segment]
        :raises QgsProcessingException: If the target_vertex is not found within the geometry of the feature.
        """
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

    def rotate(self, angle: float) -> Qgis.GeometryOperationResult:
        """
        Rotates the geometry of the feature around a specified center point.

        The method performs a rotation operation on the geometry of the associated feature by the specified angle. If
        the rotation is successfully completed, the geometry of the feature is updated, and the rotation status is set.

        QgsGeometry.rotate() takes any positive and negative values. Positive - rotate clockwise,
        negative - counterclockwise.

        :param angle: The angle, in degrees, by which the geometry will be rotated.
        :type angle: float
        :return: The result of the geometry rotation operation, indicating success or failure.
        :rtype: Qgis.GeometryOperationResult
        """
        result = self.geom.rotate(angle, self.center_xy)
        if result == Qgis.GeometryOperationResult.Success:
            self.feature.setGeometry(self.geom)
            self.is_rotated = True

        return result

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from qgis.core import QgsProcessingException, QgsSpatialIndex

if TYPE_CHECKING:
    from qgis.core import (
        QgsFeature,
        QgsGeometry,
        QgsPoint,
        QgsPointXY,
        QgsProcessingFeatureSource,
    )


class Line:
    """
    Represents a line object with associated geometry and feature.

    This class is a utility for working with line geometries, particularly for calculating distances and finding the
    closest segment to a given point. It is initialized with a QgsFeature object that contains the geometry of the line.

    :ivar feature: The QgsFeature object representing the line.
    :type feature: QgsFeature
    :ivar geom: The QgsGeometry object derived from the feature.
    :type geom: QgsGeometry
    """

    def __init__(self, line_feature: QgsFeature):
        self.feature: QgsFeature = line_feature
        self.geom: QgsGeometry = line_feature.geometry()

    def get_closest_segment(self, point_xy: QgsPointXY) -> Segment:
        """
        Finds and returns the closest line segment to a given point within a geometry.

        :param point_xy: The point for which the closest segment is to be determined.
        :type point_xy: QgsPointXY
        :return: A segment object defining the closest line segment with its start and end points.
        :rtype: Segment
        """
        _, _, next_vertex_idx, _ = self.geom.closestSegmentWithContext(point_xy)
        start, end = self.geom.vertexAt(next_vertex_idx - 1), self.geom.vertexAt(next_vertex_idx)
        return Segment(start=start, end=end)

    def calc_distance(self, geom: QgsGeometry) -> float:
        """
        Calculates the distance between the geometry of the current object and another geometry.

        The function computes the shortest distance between the two geometries and returns it as a floating-point value.

        :param geom: The geometry object to compute the distance to.
        :type geom: QgsGeometry
        :return: The shortest distance between the current object's geometry and the given geometry.
        :rtype: float
        """
        return self.geom.distance(geom)


class LineLayer:
    """
    Represents a handler for processing line layers and performing efficient spatial queries. It manages a mapping of
    line feature IDs to their corresponding features and a spatial index to facilitate quick geometric operations.

    This class is particularly useful for operations requiring proximity-based queries
    or access to specific line features by ID.

    :ivar line_layer: The input line layer provided during initialization.
    :type line_layer: QgsProcessingFeatureSource
    :ivar id_line_map: A dictionary that maps each feature's ID to its corresponding QgsFeature for quick lookup.
    :type id_line_map: dict[int, QgsFeature]
    :ivar spatial_index: A spatial index initialized with the line features to enable efficient spatial queries.
    :type spatial_index: QgsSpatialIndex
    """

    def __init__(self, line_layer: QgsProcessingFeatureSource):
        self.line_layer = line_layer
        self.id_line_map: dict[int, QgsFeature] = {x.id(): x for x in line_layer.getFeatures()}
        self.spatial_index = QgsSpatialIndex(flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        self.spatial_index.addFeatures(line_layer.getFeatures())

    def get_closest_line(self, point: QgsPointXY) -> Line:
        """
        Find the closest line to a given point using a spatial index.

        This function identifies the nearest line to a specified point using a spatial index. The function will raise
        an exception if no lines are found near the provided point. Once the nearest line is detected, it is retrieved
        from the ID-line mapping and returned.

        :param point: The geographical point for which the closest line is to be determined.
        :type point: QgsPointXY
        :return: The closest line to the specified point.
        :rtype: Line
        :raises QgsProcessingException: If no lines are found near the given point.
        """
        closest_line_id = self.spatial_index.nearestNeighbor(point, 1)

        if not closest_line_id:
            raise QgsProcessingException(f"No lines found near point {point}")

        return Line(self.id_line_map[closest_line_id[0]])


class Segment:
    """
    Represents a geometric segment defined by a start and an end point.

    The Segment class models a straight line between two points and provides properties for accessing various
    characteristics of the segment such as its length and azimuth.

    :ivar start: The starting point of the segment.
    :type start: QgsPoint
    :ivar end: The ending point of the segment.
    :type end: QgsPoint
    """

    def __init__(self, start: QgsPoint, end: QgsPoint):
        self.start = start
        self.end = end

    @cached_property
    def length(self) -> float:
        """
        Computes the length of a geometric segment defined by start and end points.

        The `length` is calculated lazily upon access using the `distance` method of the `start` point with respect to
        the `end` point. The result is cached after the first computation.

        :return: The computed length between the start and end points.
        :rtype: float
        """
        return self.start.distance(self.end)

    @cached_property
    def azimuth(self) -> float:
        """
        Represents a cached property that calculates the azimuth between two points.

        The azimuth is computed lazily based on the starting and ending points, which are expected to have an `azimuth`
        method. The result is cached after the first computation, so subsequent accesses do not require recalculation.

        QgsPoint.azimuth(QgsPoint) returns the azimuth between two points in a range of -180 to 180 degrees.

        :return: The azimuth computed between the start and end points.
        :rtype: float
        """
        return self.start.azimuth(self.end)

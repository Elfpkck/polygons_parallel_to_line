from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from qgis.core import (
    QgsFeature,
    QgsFeatureSink,
    QgsFields,
    QgsProcessingException,
    QgsProcessingFeatureSource,
)

from .azimuth import calculate_delta_azimuth
from .line import LineLayer
from .polygon import polygon_factory
from .rotator import PolygonRotator

if TYPE_CHECKING:
    from qgis.core import QgsProcessingFeedback

    from .line import Line
    from .polygon import Polygon


@dataclasses.dataclass
class Params:
    """Input parameters for the algorithm."""

    line_layer: QgsProcessingFeatureSource
    polygon_layer: QgsProcessingFeatureSource
    by_longest: bool
    no_multi: bool
    distance: float
    angle: float
    fields: QgsFields
    sink: QgsFeatureSink


class PolygonsParallelToLine:
    def __init__(self, feedback: QgsProcessingFeedback, params: Params):
        self.feedback = feedback
        self.params = params
        self.total_number = self.params.polygon_layer.featureCount()

    def run(self) -> None:
        # pydevd_pycharm.settrace("127.0.0.1", port=53100, stdoutToServer=True, stderrToServer=True)
        self.validate_polygon_layer()
        self.rotate_polygons()

    def validate_polygon_layer(self) -> None:
        if not self.total_number:
            raise QgsProcessingException("Layer does not have any polygons")

    def rotate_polygons(self) -> None:
        total = 100.0 / self.total_number

        for i, polygon in enumerate(self.params.polygon_layer.getFeatures(), start=1):
            if self.feedback.isCanceled():
                break

            processed_polygon = self.process_polygon(polygon)
            self.params.sink.addFeature(processed_polygon, QgsFeatureSink.FastInsert)
            self.feedback.setProgress(int(i * total))

    def process_polygon(self, polygon: QgsFeature) -> QgsFeature:
        poly = polygon_factory(polygon)
        line_layer = LineLayer(self.params.line_layer)
        line = line_layer.get_closest_line_geom(poly.center)
        distance = line.get_distance(poly.geom)

        if (self.params.distance and distance > self.params.distance) or (self.params.no_multi and poly.is_multi):
            return self.create_new_feature(poly, is_rotated=False)

        closest_part = poly.get_closest_part(line.geom)
        edge_1, edge_2 = closest_part.get_closest_edges()
        # Azimuths from the closest vertex pointing to adjacent vertices (next and previous)
        edge_1_azimuth, edge_2_azimuth = edge_1.get_line_azimuth(), edge_2.get_line_azimuth()
        line_segment_azimuth = line.get_closest_segment_azimuth(closest_part.closest_vertex)
        delta1 = calculate_delta_azimuth(line_segment_azimuth, edge_1_azimuth)
        delta2 = calculate_delta_azimuth(line_segment_azimuth, edge_2_azimuth)
        rotator = PolygonRotator(poly, delta1, delta2)
        self.rotate(rotator, edge_1, edge_2)  # TODO: why rotate method in this class and not in rotator?
        return self.create_new_feature(rotator.poly, rotator.is_rotated)

    def rotate(self, rotator: PolygonRotator, edge_1: Line, edge_2: Line) -> None:
        if abs(rotator.delta1) <= self.params.angle and abs(rotator.delta2) <= self.params.angle:
            if self.params.by_longest:
                return rotator.rotate_by_longest_edge(edge_1.length, edge_2.length)
            return rotator.rotate_by_smallest_angle()

        for delta in (rotator.delta1, rotator.delta2):
            if abs(delta) <= self.params.angle:
                return rotator.rotate_by_angle(delta)

    def create_new_feature(self, poly: Polygon, is_rotated: bool = False) -> QgsFeature:
        """
        Creates a new QgsFeature from a Polygon object.

        Args:
            poly: The Polygon object to convert to a QgsFeature
            is_rotated: Flag indicating if the polygon has been rotated

        Returns:
            A new QgsFeature with geometry and attributes from the Polygon
        """
        new_feature = QgsFeature(self.params.fields)
        new_feature.setGeometry(poly.geom)
        attrs = poly.poly.attributes()

        if is_rotated:
            attrs.append(1)  # Add 1 if the polygon was rotated

        new_feature.setAttributes(attrs)
        return new_feature

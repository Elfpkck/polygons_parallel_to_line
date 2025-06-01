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

from .azimuth import calc_delta_azimuth
from .line import LineLayer
from .polygon import polygon_factory
from .rotator import PolygonRotator

if TYPE_CHECKING:
    from qgis.core import QgsProcessingFeedback

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
        closest_line = line_layer.get_closest_line_geom(poly.center)
        distance = closest_line.calc_distance(poly.geom)

        if (self.params.distance and distance > self.params.distance) or (self.params.no_multi and poly.is_multi):
            return self.create_new_feature(poly)

        closest_poly_part = poly.get_closest_part(closest_line.geom)
        edge_1, edge_2 = closest_poly_part.closest_edges_pair
        # Azimuths from the closest vertex pointing to adjacent vertices (next and previous)
        edge_1_azimuth, edge_2_azimuth = edge_1.get_line_azimuth(), edge_2.get_line_azimuth()
        line_segment_azimuth = closest_line.get_closest_segment_azimuth(closest_poly_part.closest_vertex)
        delta1 = calc_delta_azimuth(line_segment_azimuth, edge_1_azimuth)
        delta2 = calc_delta_azimuth(line_segment_azimuth, edge_2_azimuth)
        # TODO: args
        PolygonRotator(poly, delta1, delta2).rotate(
            edge_1.length, edge_2.length, self.params.angle, self.params.by_longest
        )
        return self.create_new_feature(poly)

    def create_new_feature(self, poly: Polygon) -> QgsFeature:
        """
        Creates a new QgsFeature from a Polygon object.

        Args:
            poly: The Polygon object to convert to a QgsFeature

        Returns:
            A new QgsFeature with geometry and attributes from the Polygon
        """
        new_feature = QgsFeature(self.params.fields)
        new_feature.setGeometry(poly.geom)
        attrs = poly.poly.attributes()

        if poly.is_rotated:
            attrs.append(1)  # Add 1 if the polygon was rotated

        new_feature.setAttributes(attrs)
        return new_feature

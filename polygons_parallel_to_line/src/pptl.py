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

from .line import LineLayer
from .polygon import Polygon
from .rotator import PolygonRotator

if TYPE_CHECKING:
    from qgis.core import QgsProcessingFeedback


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
        poly = Polygon(polygon)
        line_layer = LineLayer(self.params.line_layer)
        closest_line = line_layer.get_closest_line(poly.center)
        distance = closest_line.calc_distance(poly.geom)

        if (self.params.distance and distance > self.params.distance) or (self.params.no_multi and poly.is_multi):
            return self.create_new_feature(poly)

        PolygonRotator(poly, closest_line, self.params.angle, self.params.by_longest).rotate()
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

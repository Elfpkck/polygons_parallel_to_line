from __future__ import annotations

import dataclasses
from functools import cached_property
from typing import TYPE_CHECKING

from qgis.core import (
    QgsFeature,
    QgsFeatureSink,
    QgsFields,
    QgsProcessingException,
    QgsProcessingFeatureSource,
)

from .const import COLUMN_NAME
from .line import LineLayer
from .polygon import Polygon
from .rotator import PolygonRotator

if TYPE_CHECKING:
    from qgis.core import QgsProcessingFeedback


@dataclasses.dataclass
class Params:
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
        self.total_number: int = self.params.polygon_layer.featureCount()

    @cached_property
    def line_layer(self) -> LineLayer:
        return LineLayer(self.params.line_layer)

    def run(self) -> None:
        # pydevd_pycharm.settrace("127.0.0.1", port=53100, stdoutToServer=True, stderrToServer=True) # noqa: ERA001
        self.validate_polygon_layer()
        self.rotate_polygons()

    def validate_polygon_layer(self) -> None:
        if not self.total_number:
            msg = "Layer does not have any polygons"
            raise QgsProcessingException(msg)

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

        if self.params.no_multi and poly.is_multi:
            return self.create_new_feature(poly)

        # Selected by centroid distance; an edge of the polygon may be nearer to a different line.
        closest_line = self.line_layer.get_closest_line(poly.center_xy)

        if self.params.distance and closest_line.geom.distance(poly.geom) > self.params.distance:
            return self.create_new_feature(poly)

        PolygonRotator(
            poly=poly,
            closest_line=closest_line,
            angle_threshold=self.params.angle,
            by_longest=self.params.by_longest,
        ).rotate()
        return self.create_new_feature(poly)

    def create_new_feature(self, poly: Polygon) -> QgsFeature:
        new_feature = QgsFeature(self.params.fields)
        new_feature.setGeometry(poly.geom)
        new_feature.setAttribute(COLUMN_NAME, poly.is_rotated)
        return new_feature

from __future__ import annotations

import dataclasses
from qgis.core import QgsFeatureSink, QgsFields, QgsProcessingException, QgsFeature
from typing import Any, TYPE_CHECKING

from .rotator import Rotator
from .polygon import polygon_factory
from .line import LineLayer
from .helpers import tr

if TYPE_CHECKING:
    from qgis.core import QgsProcessingFeedback
    from .polygon import Polygon


@dataclasses.dataclass
class Params:
    """Input parameters for the algorithm."""

    line_layer: Any
    polygon_layer: Any
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
        self.line_layer = LineLayer(self.params.line_layer)
        self.rotator = Rotator()

    def run(self) -> None:
        # pydevd_pycharm.settrace("127.0.0.1", port=53100, stdoutToServer=True, stderrToServer=True)
        self._validate_polygon_layer()
        self._rotate_and_write()

    def _validate_polygon_layer(self):
        if not self.total_number:
            raise QgsProcessingException(tr("Layer does not have any polygons"))

    def _rotate_and_write(self):
        total = 100.0 / self.total_number
        processed_polygons = []

        for i, polygon in enumerate(self.params.polygon_layer.getFeatures(), start=1):
            if self.feedback.isCanceled():
                break
            # TODO: control rotator lifecycle here?
            # TODO: create some new class for polygon and line? maybe instead of rotator?
            processed_polygons.append(self._lifecycle(polygon))
            self.feedback.setProgress(int(i * total))

        self.params.sink.addFeatures(processed_polygons, QgsFeatureSink.FastInsert)

    def _lifecycle(self, polygon):
        self.rotator.rotation_check = False
        poly = polygon_factory(polygon)
        line = self.line_layer.get_closest_line_geom(poly.center)
        distance = line.get_distance(poly.geom)

        if self.params.distance and distance > self.params.distance:
            return self.get_new_feature(poly)

        if self.params.no_multi and poly.is_multi:
            return self.get_new_feature(poly)

        closest_part = poly.get_closest_part(line.geom)
        edge_1, edge_2 = closest_part.get_closest_edges()
        # this 2 azimuths FROM the closest vertex TO the next and TO the previous vertexes
        edge_1_azimuth = edge_1.get_line_azimuth()
        edge_2_azimuth = edge_2.get_line_azimuth()
        line_segment_azimuth = line.get_closest_segment_azimuth(closest_part.closest_vertex)
        delta1 = self.rotator.get_delta_azimuth(line_segment_azimuth, edge_1_azimuth)
        delta2 = self.rotator.get_delta_azimuth(line_segment_azimuth, edge_2_azimuth)
        if abs(delta1) <= self.params.angle >= abs(delta2):
            if self.params.by_longest:
                self.rotator.rotate_by_longest(delta1, delta2, edge_1.length, edge_2.length, poly)
            else:
                self.rotator.rotate_not_by_longest(delta1, delta2, poly)
        else:
            self.rotator.others_rotations(delta1, delta2, poly, self.params.angle)

        return self.get_new_feature(poly)

    def get_new_feature(self, poly: Polygon):
        new_feature = QgsFeature(self.params.fields)
        new_feature.setGeometry(poly.geom)
        attrs = poly.poly.attributes()
        if self.rotator.rotation_check:
            attrs.append(1)
        new_feature.setAttributes(attrs)
        return new_feature


# TODO: for the future: a method to make 2 objects (lines, polygons) parallel
# TODO: update translations including path

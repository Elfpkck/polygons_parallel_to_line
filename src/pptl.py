from __future__ import annotations

import enum
import os
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsFeatureSink, QgsField, QgsFields, QgsProcessingException, QgsSpatialIndex
from typing import Any, TYPE_CHECKING

from .rotator import Rotator

if TYPE_CHECKING:
    from qgis.core import QgsProcessingAlgorithm, QgsProcessingContext, QgsProcessingFeedback


class Cfg(str, enum.Enum):
    OUTPUT_LAYER = "OUTPUT"
    LINE_LAYER = "LINE_LAYER"
    POLYGON_LAYER = "POLYGON_LAYER"
    LONGEST = "LONGEST"
    NO_MULTI = "NO_MULTI"
    DISTANCE = "DISTANCE"
    ANGLE = "ANGLE"
    COLUMN_NAME = "_rotated"


class PolygonsParallelToLine:
    def __init__(
        self,
        algo: QgsProcessingAlgorithm,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ):
        self.algo = algo
        self.parameters = parameters
        self.context = context
        self.feedback = feedback

    def run(self) -> dict[str, Any]:
        # pydevd_pycharm.settrace("127.0.0.1", port=53100, stdoutToServer=True, stderrToServer=True)
        self.get_input_values()
        self.create_line_spatial_index()
        self.validate_polygon_layer()
        self.lines_dict = {x.id(): x for x in self.line_layer.getFeatures()}
        self.rotate_and_write()
        ret = {Cfg.OUTPUT_LAYER: self.dest_id}
        if os.getenv("PPTL_TEST"):
            output_layer = self.context.getMapLayer(self.dest_id)
            line = [x.geometry() for x in self.line_layer.getFeatures()][0].asWkt()  # TODO: remove
            poly = [x.geometry() for x in self.polygon_layer.getFeatures()][0].asWkt()  # TODO: remove
            ret["result"] = [x.geometry() for x in output_layer.getFeatures()][0].asWkt()
        return ret

    def get_input_values(self):
        parameters, context = self.parameters, self.context
        self.line_layer = self.algo.parameterAsSource(parameters, Cfg.LINE_LAYER, context)
        self.polygon_layer = self.algo.parameterAsSource(parameters, Cfg.POLYGON_LAYER, context)
        self.by_longest = self.algo.parameterAsBool(parameters, Cfg.LONGEST, context)
        self.no_multi = self.algo.parameterAsBool(parameters, Cfg.NO_MULTI, context)
        self.distance = self.algo.parameterAsDouble(parameters, Cfg.DISTANCE, context)
        self.angle = self.algo.parameterAsDouble(parameters, Cfg.ANGLE, context)
        self.new_fields = new_fields = QgsFields()

        for field in self.polygon_layer.fields():
            if Cfg.COLUMN_NAME == field.name():
                continue
            new_fields.append(field)
        new_fields.append(QgsField(Cfg.COLUMN_NAME, QVariant.Int))
        self.sink, self.dest_id = self.algo.parameterAsSink(
            parameters,
            Cfg.OUTPUT_LAYER,
            context,
            new_fields,
            self.polygon_layer.wkbType(),
            self.polygon_layer.sourceCrs(),
        )

    def create_line_spatial_index(self):
        spatial_index = QgsSpatialIndex()
        spatial_index.addFeatures(self.line_layer.getFeatures())
        self.index = spatial_index

    def validate_polygon_layer(self):
        self.total_number = self.polygon_layer.featureCount()
        if not self.total_number:
            raise QgsProcessingException(self.algo.tr("Layer does not have any polygons"))

    def rotate_and_write(self):
        total = 100.0 / self.total_number
        processed_polygons = []
        for i, polygon in enumerate(self.polygon_layer.getFeatures(), start=1):
            if self.feedback.isCanceled():
                break
            rotator = Rotator(
                polygon,
                self.lines_dict,
                self.index,
                self.new_fields,
                self.by_longest,
                self.no_multi,
                self.distance,
                self.angle,
            )
            processed_polygons.append(rotator.get_rotated_polygon())
            self.feedback.setProgress(int(i * total))

        self.sink.addFeatures(processed_polygons, QgsFeatureSink.FastInsert)


# TODO: for the future: a method to make 2 objects (lines, polygons) parallel
# TODO: update translations including path

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

from .const import COLUMN_NAME
from .line import LineLayer
from .polygon import Polygon
from .rotator import PolygonRotator

if TYPE_CHECKING:
    from qgis.core import QgsProcessingFeedback


@dataclasses.dataclass
class Params:
    """
    Represents the parameters for processing geospatial data.

    This class defines a set of parameters required for processing geospatial data, such as line and polygon layers,
    adjustable distance, angle parameters, and options to control output formats and behavior. It acts as a container
    for inputs and configurations necessary for geospatial processing workflows.

    :ivar line_layer: A feature source representing the input line layer.
    :type line_layer: QgsProcessingFeatureSource
    :ivar polygon_layer: A feature source representing the input polygon layer.
    :type polygon_layer: QgsProcessingFeatureSource
    :ivar by_longest: Determines whether processing should consider the longest feature during calculations.
    :type by_longest: bool
    :ivar no_multi: Determines whether to restrict outputs to single-part geometries (no multiparts).
    :type no_multi: bool
    :ivar distance: A numeric value representing a distance parameter within the process.
    :type distance: float
    :ivar angle: A numeric value representing an angle parameter for calculations.
    :type angle: float
    :ivar fields: A collection of feature fields to be processed.
    :type fields: QgsFields
    :ivar sink: A feature sink where processed output features are stored.
    :type sink: QgsFeatureSink
    """

    line_layer: QgsProcessingFeatureSource
    polygon_layer: QgsProcessingFeatureSource
    by_longest: bool
    no_multi: bool
    distance: float
    angle: float
    fields: QgsFields
    sink: QgsFeatureSink


class PolygonsParallelToLine:
    """
    Handles the processing of polygons to align them parallel to the closest line from a provided line layer.

    This class is designed to process polygons from a given layer, validate their existence, and rotate them to align
    parallel to the nearest line within a specified line layer. The class operates based on provided parameters which
    define constraints and criteria for processing, such as distance thresholds, rotation angles, and multi-polygon
    behavior.

    The processing includes validating the input polygon layer, determining the closest line for each polygon,
    calculating necessary rotations, applying transformations, and saving the processed features into the sink layer.

    :ivar feedback: The QgsProcessingFeedback object used for sending feedback to the user during processing,
        such as progress updates.
    :type feedback: QgsProcessingFeedback
    :ivar params: The object encapsulating all parameters required for processing the polygons, such as layers to
        process, fields, and constraints.
    :type params: Params
    :ivar total_number: The total number of features (polygons) in the input layer being processed.
    :type total_number: int
    """

    def __init__(self, feedback: QgsProcessingFeedback, params: Params):
        self.feedback = feedback
        self.params = params
        self.total_number: int = self.params.polygon_layer.featureCount()

    def run(self) -> None:
        """
        Executes the main functionality of the object, involving validation and manipulation of polygon-related data.
        The function performs a series of predefined operations critical to the object’s intended behavior.
        Specifically, it validates a polygon layer and applies a rotation operation to the polygons.

        :return: None
        """
        # pydevd_pycharm.settrace("127.0.0.1", port=53100, stdoutToServer=True, stderrToServer=True)
        self.validate_polygon_layer()
        self.rotate_polygons()

    def validate_polygon_layer(self) -> None:
        if not self.total_number:
            raise QgsProcessingException("Layer does not have any polygons")

    def rotate_polygons(self) -> None:
        """
        Rotates and processes polygons from the provided layer and updates the progress feedback. The method iterates
        through the features in the polygon layer, processes each polygon, and adds the processed features to
        the designated sink. Progress is updated during each iteration, and the operation stops if it is canceled via
        feedback.

        :param self: An instance of the class the method belongs to.

        :returns: None
        """
        total = 100.0 / self.total_number

        for i, polygon in enumerate(self.params.polygon_layer.getFeatures(), start=1):
            if self.feedback.isCanceled():
                break

            processed_polygon = self.process_polygon(polygon)
            self.params.sink.addFeature(processed_polygon, QgsFeatureSink.FastInsert)
            self.feedback.setProgress(int(i * total))

    def process_polygon(self, polygon: QgsFeature) -> QgsFeature:
        """
        Processes a polygon by calculating its proximity to the closest line, applying various transformations and
        conditions, and creating a new feature based on the modifications or conditions provided.

        :param polygon: The QgsFeature object representing the input polygon to be processed.
        :type polygon: QgsFeature
        :return: A QgsFeature object representing the newly processed or modified polygon.
        :rtype: QgsFeature
        """
        poly = Polygon(polygon)
        line_layer = LineLayer(self.params.line_layer)
        closest_line = line_layer.get_closest_line(poly.center_xy)
        distance = closest_line.calc_distance(poly.geom)

        if (self.params.distance and distance > self.params.distance) or (self.params.no_multi and poly.is_multi):
            return self.create_new_feature(poly)

        PolygonRotator(
            poly=poly,
            closest_line=closest_line,
            angle_threshold=self.params.angle,
            by_longest=self.params.by_longest,
        ).rotate()
        return self.create_new_feature(poly)

    def create_new_feature(self, poly: Polygon) -> QgsFeature:
        """
        Creates a new feature and sets its geometry and attribute based on the provided polygon.

        This method creates a new QgsFeature using the provided fields, sets the geometry of the new feature to
        match the geometry of the provided polygon, and assigns the attribute value to indicate whether the polygon
        is rotated. The created QgsFeature is then returned.

        :param poly: The polygon object whose geometry and rotation status are used to define the new feature's
            properties.
        :type poly: Polygon
        :return: The newly created QgsFeature with its geometry and attributes set accordingly.
        :rtype: QgsFeature
        """
        new_feature = QgsFeature(self.params.fields)
        new_feature.setGeometry(poly.geom)
        new_feature.setAttribute(COLUMN_NAME, poly.is_rotated)
        return new_feature

from __future__ import annotations
from typing import TYPE_CHECKING

from qgis.core import QgsGeometry, QgsPoint

if TYPE_CHECKING:
    from qgis.core import QgsFeature


class Polygon:  # TODO: 2 forms for multi and simple?
    def __init__(self, polygon: QgsFeature):
        self.p = polygon
        self.p_geom = polygon.geometry()
        self.center = self.p_geom.centroid().asPoint()
        self.is_multi = self.p_geom.isMultipart()

        # Without the last vertex which is the same as the first one.
        if self.is_multi:
            self.vertexes = [part[0][:-1] for part in self.p_geom.asMultiPolygon()]
        else:
            self.vertexes = self.p_geom.asPolygon()[0][:-1]  # TODO: the same shape as above?

    def get_nearest_vertex(self, nearest_line_geom):
        if self.is_multi:
            dct = {}
            for i, part in enumerate(self.vertexes):
                min_distance, vertex_index, nearest_vertex = self._get_nearest_vertex(part, nearest_line_geom)
                dct[(i, vertex_index, nearest_vertex)] = min_distance
            i, vertex_index, nearest_vertex = min(dct, key=dct.get)
            return self.vertexes[i], vertex_index, nearest_vertex
        else:
            _, vertex_index, nearest_vertex = self._get_nearest_vertex(self.vertexes, nearest_line_geom)
            return self.vertexes, vertex_index, nearest_vertex

    def _get_nearest_vertex(self, polygon_vertexes, nearest_line_geom):
        vertex_to_segment_dict = {}
        for vertex in polygon_vertexes:
            vertex_geom = QgsGeometry.fromPointXY(vertex)
            vertex_to_segment = vertex_geom.distance(nearest_line_geom)  # float as key? TODO: change?
            vertex_to_segment_dict[vertex_to_segment] = vertex

        min_distance = min(vertex_to_segment_dict.keys())
        nearest_vertex = vertex_to_segment_dict[min_distance]
        vertex_index = polygon_vertexes.index(nearest_vertex)
        return min_distance, vertex_index, nearest_vertex

    @staticmethod
    def get_vertex_edges(polygon_vertexes, vertex_index) -> tuple:  # TODO: separate function?
        if vertex_index == 0:  # if vertex is first
            edge1 = QgsGeometry.fromPolyline([QgsPoint(polygon_vertexes[0]), QgsPoint(polygon_vertexes[1])])
            edge2 = QgsGeometry.fromPolyline([QgsPoint(polygon_vertexes[0]), QgsPoint(polygon_vertexes[-1])])
        elif vertex_index == len(polygon_vertexes) - 1:  # if vertex is last
            edge1 = QgsGeometry.fromPolyline([QgsPoint(polygon_vertexes[-1]), QgsPoint(polygon_vertexes[0])])
            edge2 = QgsGeometry.fromPolyline([QgsPoint(polygon_vertexes[-1]), QgsPoint(polygon_vertexes[-2])])
        else:
            edge1 = QgsGeometry.fromPolyline(
                [QgsPoint(polygon_vertexes[vertex_index]), QgsPoint(polygon_vertexes[vertex_index + 1])]
            )
            edge2 = QgsGeometry.fromPolyline(
                [QgsPoint(polygon_vertexes[vertex_index]), QgsPoint(polygon_vertexes[vertex_index - 1])]
            )
        return edge1, edge2

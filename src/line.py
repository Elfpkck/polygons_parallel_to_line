from qgis.core import QgsSpatialIndex


class LineLayer:
    def __init__(self, line_layer):
        self.line_layer = line_layer
        self.id_line_map = {x.id(): x for x in line_layer.getFeatures()}
        self.spatial_index = QgsSpatialIndex()
        self.spatial_index.addFeatures(line_layer.getFeatures())

    def get_closest_line(self, point):
        closest_line_id = self.spatial_index.nearestNeighbor(point, 1)
        return self.id_line_map[closest_line_id[0]]

    def get_closest_line_geom(self, point):
        return self.get_closest_line(point).geometry()

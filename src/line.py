from qgis.core import QgsSpatialIndex


class LineLayer:
    def __init__(self, line_layer):
        self.line_layer = line_layer
        self.lines_dict = {x.id(): x for x in line_layer.getFeatures()}

        self.index = QgsSpatialIndex()
        self.index.addFeatures(line_layer.getFeatures())

    def get_nearest_line(self, point):
        nearest_line_id = self.index.nearestNeighbor(point, 1)
        return self.lines_dict[nearest_line_id[0]]

    def get_nearest_line_geom(self, point):
        return self.get_nearest_line(point).geometry()

from qgis.core import QgsProcessingProvider
from .algorithm import Algorithm


class Provider(QgsProcessingProvider):
    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(Algorithm())

    def id(self, *args, **kwargs):
        return "pptl"

    def name(self, *args, **kwargs):
        return self.tr("Polygons parallel to line")

    def icon(self):
        return QgsProcessingProvider.icon(self)

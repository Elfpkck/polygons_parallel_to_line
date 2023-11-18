from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.core import QgsProcessingProvider

from .algorithm import Algorithm

if TYPE_CHECKING:
    from PyQt5.QtGui import QIcon


class Provider(QgsProcessingProvider):
    def loadAlgorithms(self, *args, **kwargs) -> None:
        self.addAlgorithm(Algorithm())

    def id(self, *args, **kwargs) -> str:
        return "pptl"

    def name(self, *args, **kwargs) -> str:
        return "Polygons parallel to the lines"

    def icon(self) -> QIcon:
        return QgsProcessingProvider.icon(self)

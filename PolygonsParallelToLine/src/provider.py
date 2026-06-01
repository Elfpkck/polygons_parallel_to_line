from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.core import QgsProcessingProvider

from .algorithm import Algorithm

if TYPE_CHECKING:
    from PyQt5.QtGui import QIcon


class Provider(QgsProcessingProvider):
    def loadAlgorithms(self) -> None:
        self.addAlgorithm(Algorithm())

    def id(self) -> str:
        return "pptl"

    def name(self) -> str:
        return "Polygons parallel to lines"

    def icon(self) -> QIcon:
        return super().icon()

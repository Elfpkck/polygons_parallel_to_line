from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.core import QgsProcessingProvider

from .algorithm import Algorithm

if TYPE_CHECKING:
    from qgis.PyQt.QtGui import QIcon  # type: ignore[import-not-found]


class Provider(QgsProcessingProvider):
    def loadAlgorithms(self) -> None:
        self.addAlgorithm(Algorithm())

    def id(self) -> str:
        return "pptl"

    def name(self) -> str:
        return "Parallelizer"

    def icon(self) -> QIcon:
        return super().icon()

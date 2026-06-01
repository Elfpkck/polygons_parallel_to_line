from __future__ import annotations

from qgis.core import QgsApplication

from .provider import Provider


class Plugin:
    def __init__(self) -> None:
        self.provider: Provider | None = None

    def initProcessing(self) -> None:
        self.provider = Provider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self) -> None:
        self.initProcessing()

    def unload(self) -> None:
        QgsApplication.processingRegistry().removeProvider(self.provider)

# flake8: noqa
import sys
from pathlib import Path

from qgis.core import QgsApplication

from .provider import Provider

cmd_folder = str(Path(__file__).parents[1])

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class Plugin:
    def __init__(self) -> None:
        self.provider = None

    def initProcessing(self) -> None:
        self.provider = Provider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self) -> None:
        self.initProcessing()

    def unload(self) -> None:
        QgsApplication.processingRegistry().removeProvider(self.provider)

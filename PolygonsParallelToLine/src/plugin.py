from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from qgis.core import QgsApplication
from qgis.PyQt.QtGui import QIcon  # type: ignore[import-not-found]
from qgis.PyQt.QtWidgets import QAction  # type: ignore[import-not-found]

from .provider import Provider
from .settings import MapToolSettings
from .settings_dialog import MapToolSettingsDialog

if TYPE_CHECKING:
    from qgis.gui import QgisInterface
    from qgis.PyQt.QtWidgets import QToolBar  # type: ignore[import-not-found]

    from .map_tool import ParallelToLineMapTool

_MENU_NAME = "Polygons Parallel to Line"


class Plugin:
    def __init__(self, iface: QgisInterface | None = None) -> None:
        self.iface = iface
        self.provider: Provider | None = None
        self.settings: MapToolSettings | None = None
        self.toolbar: QToolBar | None = None
        self.parallelize_action: QAction | None = None
        self.settings_action: QAction | None = None
        self.map_tool: ParallelToLineMapTool | None = None

    def initProcessing(self) -> None:
        self.provider = Provider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self) -> None:
        self.initProcessing()

        if self.iface is None:
            return

        from .map_tool import ParallelToLineMapTool

        self.settings = MapToolSettings()

        self.toolbar = self.iface.addToolBar(_MENU_NAME)
        self.toolbar.setObjectName("PolygonsParallelToLineToolBar")

        icon_path = Path(__file__).resolve().parent.parent / "icons" / "icon.png"
        self.parallelize_action = QAction(
            QIcon(str(icon_path)), "Parallel to Line (interactive)", self.iface.mainWindow()
        )
        self.parallelize_action.setCheckable(True)
        self.parallelize_action.toggled.connect(self._on_action_toggled)
        self.toolbar.addAction(self.parallelize_action)
        self.iface.addPluginToVectorMenu(_MENU_NAME, self.parallelize_action)

        self.settings_action = QAction(
            QgsApplication.getThemeIcon("/mActionOptions.svg"),
            "Settings…",
            self.iface.mainWindow(),
        )
        self.settings_action.triggered.connect(self._open_settings_dialog)
        self.toolbar.addAction(self.settings_action)
        self.iface.addPluginToVectorMenu(_MENU_NAME, self.settings_action)

        self.map_tool = ParallelToLineMapTool(self.iface, self.settings)
        self.map_tool.deactivated.connect(self._on_map_tool_deactivated)

    def _on_action_toggled(self, checked: bool) -> None:
        if self.iface is None or self.map_tool is None:
            return
        canvas = self.iface.mapCanvas()
        if checked:
            canvas.setMapTool(self.map_tool)
        elif canvas.mapTool() is self.map_tool:
            canvas.unsetMapTool(self.map_tool)

    def _on_map_tool_deactivated(self) -> None:
        if self.parallelize_action is not None and self.parallelize_action.isChecked():
            self.parallelize_action.setChecked(False)

    def _open_settings_dialog(self) -> None:
        if self.iface is None or self.settings is None:
            return
        dialog = MapToolSettingsDialog(self.settings, self.iface.mainWindow())
        dialog.exec()

    def unload(self) -> None:
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
        if self.iface is not None:
            if self.parallelize_action is not None:
                self.iface.removePluginVectorMenu(_MENU_NAME, self.parallelize_action)
            if self.settings_action is not None:
                self.iface.removePluginVectorMenu(_MENU_NAME, self.settings_action)
            if self.map_tool is not None:
                canvas = self.iface.mapCanvas()
                if canvas.mapTool() is self.map_tool:
                    canvas.unsetMapTool(self.map_tool)
        if self.toolbar is not None:
            self.toolbar.deleteLater()
        self.parallelize_action = None
        self.settings_action = None
        self.toolbar = None
        self.map_tool = None
        self.settings = None

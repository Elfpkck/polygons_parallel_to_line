from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.PyQt.QtWidgets import (  # type: ignore[import-not-found]
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from qgis.PyQt.QtWidgets import QWidget  # type: ignore[import-not-found]

    from .settings import MapToolSettings


class MapToolSettingsDialog(QDialog):
    def __init__(self, settings: MapToolSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Polygons Parallel to Line — Settings")

        rotation_group = QGroupBox("Rotation")
        self._by_longest_checkbox = QCheckBox("Rotate by longest segment")
        self._by_longest_checkbox.setChecked(settings.by_longest)
        group_layout = QVBoxLayout()
        group_layout.addWidget(self._by_longest_checkbox)
        rotation_group.setLayout(group_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._apply)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(rotation_group)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def _apply(self) -> None:
        self._settings.by_longest = self._by_longest_checkbox.isChecked()
        self.accept()

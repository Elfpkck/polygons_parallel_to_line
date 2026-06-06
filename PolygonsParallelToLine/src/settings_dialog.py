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
        rotation_layout = QVBoxLayout()
        rotation_layout.addWidget(self._by_longest_checkbox)
        rotation_group.setLayout(rotation_layout)

        picking_group = QGroupBox("Segment picking")
        self._pick_reference_checkbox = QCheckBox("Click a single segment of the reference line")
        self._pick_reference_checkbox.setChecked(settings.pick_reference_segment)
        self._pick_target_checkbox = QCheckBox("Click a single segment of the target feature")
        self._pick_target_checkbox.setChecked(settings.pick_target_segment)
        picking_layout = QVBoxLayout()
        picking_layout.addWidget(self._pick_reference_checkbox)
        picking_layout.addWidget(self._pick_target_checkbox)
        picking_group.setLayout(picking_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._apply)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(rotation_group)
        layout.addWidget(picking_group)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def _apply(self) -> None:
        self._settings.by_longest = self._by_longest_checkbox.isChecked()
        self._settings.pick_reference_segment = self._pick_reference_checkbox.isChecked()
        self._settings.pick_target_segment = self._pick_target_checkbox.isChecked()
        self.accept()

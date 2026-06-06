from __future__ import annotations

from qgis.PyQt.QtCore import QObject, QSettings, pyqtSignal  # type: ignore[import-not-found]

_SETTINGS_PREFIX = "PolygonsParallelToLine/map_tool/"
_KEY_BY_LONGEST = _SETTINGS_PREFIX + "by_longest"
_KEY_PICK_REFERENCE_SEGMENT = _SETTINGS_PREFIX + "pick_reference_segment"
_KEY_PICK_TARGET_SEGMENT = _SETTINGS_PREFIX + "pick_target_segment"


class MapToolSettings(QObject):
    changed = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        settings = QSettings()
        self._by_longest: bool = bool(settings.value(_KEY_BY_LONGEST, defaultValue=False, type=bool))
        self._pick_reference_segment: bool = bool(
            settings.value(_KEY_PICK_REFERENCE_SEGMENT, defaultValue=False, type=bool)
        )
        self._pick_target_segment: bool = bool(settings.value(_KEY_PICK_TARGET_SEGMENT, defaultValue=False, type=bool))

    @property
    def by_longest(self) -> bool:
        return self._by_longest

    @by_longest.setter
    def by_longest(self, value: bool) -> None:
        value = bool(value)
        if value == self._by_longest:
            return
        self._by_longest = value
        QSettings().setValue(_KEY_BY_LONGEST, value)
        self.changed.emit()

    @property
    def pick_reference_segment(self) -> bool:
        return self._pick_reference_segment

    @pick_reference_segment.setter
    def pick_reference_segment(self, value: bool) -> None:
        value = bool(value)
        if value == self._pick_reference_segment:
            return
        self._pick_reference_segment = value
        QSettings().setValue(_KEY_PICK_REFERENCE_SEGMENT, value)
        self.changed.emit()

    @property
    def pick_target_segment(self) -> bool:
        return self._pick_target_segment

    @pick_target_segment.setter
    def pick_target_segment(self, value: bool) -> None:
        value = bool(value)
        if value == self._pick_target_segment:
            return
        self._pick_target_segment = value
        QSettings().setValue(_KEY_PICK_TARGET_SEGMENT, value)
        self.changed.emit()

from __future__ import annotations

from qgis.PyQt.QtCore import QObject, QSettings, pyqtSignal  # type: ignore[import-not-found]

_SETTINGS_PREFIX = "PolygonsParallelToLine/map_tool/"
_KEY_BY_LONGEST = _SETTINGS_PREFIX + "by_longest"


class MapToolSettings(QObject):
    changed = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        settings = QSettings()
        self._by_longest: bool = bool(settings.value(_KEY_BY_LONGEST, defaultValue=False, type=bool))

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

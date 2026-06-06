from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from qgis.PyQt.QtCore import QSettings

from PolygonsParallelToLine.src.settings import MapToolSettings

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(autouse=True)
def _isolate_settings() -> Iterator[None]:
    settings = QSettings()
    settings.remove("PolygonsParallelToLine")
    settings.sync()
    yield
    settings = QSettings()
    settings.remove("PolygonsParallelToLine")
    settings.sync()


def test_default_by_longest_is_false():
    settings = MapToolSettings()
    assert settings.by_longest is False


def test_by_longest_persists_across_instances():
    settings = MapToolSettings()
    settings.by_longest = True
    QSettings().sync()

    reloaded = MapToolSettings()
    assert reloaded.by_longest is True


def test_setting_same_value_emits_no_signal():
    settings = MapToolSettings()
    emissions: list[None] = []
    settings.changed.connect(lambda: emissions.append(None))

    settings.by_longest = False
    assert emissions == []

    settings.by_longest = True
    assert len(emissions) == 1

    settings.by_longest = True
    assert len(emissions) == 1

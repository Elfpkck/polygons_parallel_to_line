from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .src.plugin import Plugin


def classFactory(iface) -> Plugin:
    from .src.plugin import Plugin

    return Plugin()

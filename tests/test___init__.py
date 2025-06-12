from __future__ import annotations

import pytest

from polygons_parallel_to_line.__init__ import classFactory
from polygons_parallel_to_line.src.plugin import Plugin


@pytest.fixture(scope="function")
def iface():
    class MockIface:
        pass

    return MockIface()


def test_classFactory_returns_plugin_instance(iface):  # noqa: N802
    """Test if classFactory returns an instance of Plugin."""
    plugin_instance = classFactory(iface)
    assert isinstance(plugin_instance, Plugin)

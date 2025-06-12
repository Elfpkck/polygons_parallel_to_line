from __future__ import annotations

import pytest
from qgis.core import QgsApplication

from PolygonsParallelToLine.src.plugin import Plugin
from PolygonsParallelToLine.src.provider import Provider


@pytest.fixture(scope="function")
def plugin_instance():
    """
    Fixture to create and return a Plugin instance.
    Cleaning up processing providers registered within the QgsApplication's processing registry.
    """
    yield Plugin()

    for provider in QgsApplication.processingRegistry().providers():
        QgsApplication.processingRegistry().removeProvider(provider)


def test_plugin_initialization(plugin_instance):
    """Test if the provider is None on Plugin initialization."""
    assert plugin_instance.provider is None


def test_init_processing(plugin_instance):
    """Test if initProcessing sets up the provider correctly."""
    plugin_instance.initProcessing()
    assert isinstance(plugin_instance.provider, Provider)
    assert plugin_instance.provider in QgsApplication.processingRegistry().providers()


def test_init_gui(plugin_instance):
    """Test if initGui initializes processing properly."""
    plugin_instance.initGui()
    assert isinstance(plugin_instance.provider, Provider)
    assert plugin_instance.provider in QgsApplication.processingRegistry().providers()


def test_unload(plugin_instance):
    """Test if unload removes the provider from the processing registry."""
    plugin_instance.initProcessing()
    plugin_instance.unload()
    assert plugin_instance.provider not in QgsApplication.processingRegistry().providers()

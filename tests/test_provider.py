from __future__ import annotations

import pytest

from PolygonsParallelToLine.src.provider import Provider


@pytest.fixture(scope="module")
def provider_instance():
    """Fixture to create an instance of the Provider."""
    return Provider()


def test_provider_id(provider_instance):
    """Test if the provider id is correct."""
    assert provider_instance.id() == "pptl"


def test_provider_name(provider_instance):
    """Test if the provider name is correct."""
    assert provider_instance.name() == "Polygons parallel to lines"


def test_provider_load_algorithms(provider_instance):
    """Test if algorithms are loaded properly by Provider."""
    provider_instance.loadAlgorithms()
    assert len(provider_instance.algorithms()) > 0


def test_provider_icon(provider_instance):
    """Test if the provider icon is returned successfully."""
    assert provider_instance.icon() is not None

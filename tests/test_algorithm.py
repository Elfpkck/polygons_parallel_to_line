from __future__ import annotations

import pytest

from PolygonsParallelToLine.src.algorithm import Algorithm


@pytest.fixture(scope="module")
def algorithm_instance():
    """Fixture to create an instance of the Algorithm class."""
    return Algorithm()


def test_algorithm_initialization(algorithm_instance):
    """Test if the Algorithm instance initializes correctly."""
    assert algorithm_instance.name() == "pptl_algo"
    assert algorithm_instance.displayName() == "Parallelizer"
    assert algorithm_instance.group() == ""
    assert algorithm_instance.groupId() == ""
    assert algorithm_instance.shortHelpString() == (
        "Rotates polygons parallel to features in a reference layer (line or polygon)."
    )
    assert algorithm_instance.helpUrl() == "https://elfpkck.github.io/parallelizer/"


def test_algorithm_create_instance(algorithm_instance):
    """Test if the createInstance method creates a new instance of the algorithm."""
    new_instance = algorithm_instance.createInstance()
    assert isinstance(new_instance, Algorithm)

"""
Pytest configuration and fixtures for IFC Graph tests.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def sample_ifc_path() -> Path:
    """Path to a sample IFC file for testing."""
    # You may need to include a small test IFC file in tests/fixtures/
    return Path(__file__).parent / "fixtures" / "test_model.ifc"


@pytest.fixture
def project_root() -> Path:
    """Path to the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def neo4j_test_config() -> dict:
    """Neo4j configuration for testing."""
    return {
        "uri": "bolt://localhost:7687",
        "user": "neo4j",
        "password": "test_password",
    }


@pytest.fixture
def sample_extraction_config() -> dict:
    """Sample extraction configuration for testing."""
    return {
        'include_property_sets': True,
        'include_materials': True,
        'include_geometry': False,
        'max_properties_per_element': 50,
    }


@pytest.fixture
def sample_element_types() -> list[str]:
    """Sample element types for testing."""
    return [
        'IfcWall',
        'IfcDoor',
        'IfcWindow',
        'IfcColumn',
        'IfcBeam',
        'IfcSlab',
    ]


@pytest.fixture
def mock_ifc_element():
    """Create a mock IFC element for testing."""
    element = MagicMock()
    element.id.return_value = 123
    element.is_a.return_value = 'IfcWall'
    element.Name = 'Test Wall'
    element.GlobalId = 'abc123'
    element.ObjectType = 'Standard Wall'
    element.Description = 'A test wall element'
    element.Tag = 'W-001'
    return element


@pytest.fixture
def mock_ifc_file(mock_ifc_element):
    """Create a mock IFC file for testing."""
    ifc_file = MagicMock()
    ifc_file.by_type.return_value = [mock_ifc_element]
    
    # Mock project
    project = MagicMock()
    project.id.return_value = 1
    project.Name = 'Test Project'
    project.Description = 'A test project'
    project.Phase = 'Design'
    ifc_file.by_type.side_effect = lambda t: [project] if t == 'IfcProject' else [mock_ifc_element]
    
    return ifc_file

"""
Tests for the IFC element filter module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ifc_graph import (
    IFCElementFilter,
    IFCLoadError,
    IFCValidationError,
    filter_physical_elements,
    extract_element_properties,
    extract_spatial_info,
    extract_material_info,
    extract_property_sets,
)


class TestIFCElementFilter:
    """Tests for IFCElementFilter class."""

    def test_filter_initialization(self, sample_extraction_config):
        """Test that the filter can be initialized with config."""
        filter = IFCElementFilter("path/to/model.ifc", config=sample_extraction_config)
        assert filter.file_path == "path/to/model.ifc"
        assert filter.config == sample_extraction_config

    def test_filter_default_config(self):
        """Test that filter uses default config when none provided."""
        filter = IFCElementFilter("path/to/model.ifc")
        assert 'include_property_sets' in filter.config
        assert 'include_materials' in filter.config


class TestIFCValidation:
    """Tests for IFC file validation."""

    def test_validation_file_not_found(self, tmp_path):
        """Test validation fails for non-existent file."""
        from ifc_graph.element_filter import validate_ifc_file
        
        with pytest.raises(IFCValidationError, match="IFC file not found"):
            validate_ifc_file(str(tmp_path / "nonexistent.ifc"))

    def test_validation_invalid_extension(self, tmp_path):
        """Test validation fails for wrong file extension."""
        from ifc_graph.element_filter import validate_ifc_file
        
        # Create a file with wrong extension
        wrong_ext = tmp_path / "model.txt"
        wrong_ext.write_text("test content")
        
        with pytest.raises(IFCValidationError, match="Invalid file extension"):
            validate_ifc_file(str(wrong_ext))

    def test_validation_empty_file(self, tmp_path):
        """Test validation fails for empty file."""
        from ifc_graph.element_filter import validate_ifc_file
        
        # Create an empty IFC file
        empty_file = tmp_path / "empty.ifc"
        empty_file.touch()
        
        with pytest.raises(IFCValidationError, match="IFC file is empty"):
            validate_ifc_file(str(empty_file))


class TestExtractElementProperties:
    """Tests for element property extraction."""

    def test_extract_basic_properties(self, mock_ifc_element):
        """Test extraction of basic element properties."""
        config = {'include_property_sets': True}
        props = extract_element_properties(mock_ifc_element, config)
        
        assert props['id'] == '123'
        assert props['name'] == 'Test Wall'
        assert props['guid'] == 'abc123'
        assert props['type'] == 'IfcWall'
        assert props['object_type'] == 'Standard Wall'
        assert props['description'] == 'A test wall element'
        assert props['tag'] == 'W-001'

    def test_extract_properties_with_missing_attributes(self):
        """Test extraction handles missing attributes gracefully."""
        element = MagicMock()
        element.id.return_value = 456
        element.is_a.return_value = 'IfcDoor'
        element.Name = None
        element.GlobalId = None
        element.ObjectType = None
        element.Description = None
        element.Tag = None
        
        config = {}
        props = extract_element_properties(element, config)
        
        assert props['id'] == '456'
        assert props['name'] == 'Unnamed'
        assert props['guid'] == ''
        assert props['type'] == 'IfcDoor'


class TestExtractSpatialInfo:
    """Tests for spatial information extraction."""

    def test_extract_spatial_info_no_containment(self, mock_ifc_element):
        """Test extraction returns empty list when no spatial containment."""
        mock_ifc_element.ContainedInStructure = []
        result = extract_spatial_info(mock_ifc_element)
        assert result == []

    def test_extract_spatial_info_with_structure(self):
        """Test extraction of spatial structure info."""
        # Create mock structure
        structure = MagicMock()
        structure.id.return_value = 100
        structure.is_a.return_value = 'IfcBuildingStorey'
        structure.Name = 'Level 1'
        structure.LongName = 'Ground Floor'
        structure.Elevation = 0.0
        
        # Create mock relationship
        rel = MagicMock()
        rel.RelatingStructure = structure
        
        # Create element with containment
        element = MagicMock()
        element.id.return_value = 123
        element.ContainedInStructure = [rel]
        
        result = extract_spatial_info(element)
        
        assert len(result) == 1
        assert result[0]['id'] == '100'
        assert result[0]['name'] == 'Level 1'
        assert result[0]['type'] == 'IfcBuildingStorey'
        assert result[0]['long_name'] == 'Ground Floor'
        assert result[0]['elevation'] == 0.0


class TestFilterPhysicalElements:
    """Tests for the main filter function."""

    @patch('ifc_graph.element_filter.load_ifc_file')
    def test_filter_with_default_types(self, mock_load):
        """Test filtering with default element types."""
        mock_file = MagicMock()
        mock_file.by_type.return_value = []
        mock_load.return_value = mock_file
        
        result, ifc = filter_physical_elements("test.ifc")
        
        assert isinstance(result, dict)
        mock_load.assert_called_once_with("test.ifc")

    @patch('ifc_graph.element_filter.load_ifc_file')
    def test_filter_with_custom_types(self, mock_load):
        """Test filtering with custom element types."""
        mock_element = MagicMock()
        mock_file = MagicMock()
        mock_file.by_type.return_value = [mock_element]
        mock_load.return_value = mock_file
        
        custom_types = ['IfcWall', 'IfcDoor']
        result, ifc = filter_physical_elements("test.ifc", element_types=custom_types)
        
        assert 'IfcWall' in result or 'IfcDoor' in result

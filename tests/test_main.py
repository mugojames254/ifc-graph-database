"""
Tests for the main module CLI and configuration.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to import after patching
import yaml


class TestLoadConfig:
    """Tests for load_config function."""
    
    def test_loads_valid_yaml(self, temp_config_file):
        """Test loading a valid YAML configuration."""
        from main import load_config
        
        config = load_config(str(temp_config_file))
        
        assert 'element_types' in config
        assert 'IfcWall' in config['element_types']
    
    def test_raises_for_missing_file(self, tmp_path):
        """Test that missing config files raise FileNotFoundError."""
        from main import load_config
        
        with pytest.raises(FileNotFoundError):
            load_config(str(tmp_path / "nonexistent.yaml"))
    
    def test_raises_for_invalid_yaml(self, tmp_path):
        """Test that invalid YAML raises an error."""
        from main import load_config
        
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(yaml.YAMLError):
            load_config(str(invalid_file))


class TestGetDefaultConfig:
    """Tests for get_default_config function."""
    
    def test_returns_default_element_types(self):
        """Test that default config includes expected element types."""
        from main import get_default_config
        
        config = get_default_config()
        
        assert 'element_types' in config
        assert 'IfcWall' in config['element_types']
        assert 'IfcDoor' in config['element_types']
        assert 'IfcColumn' in config['element_types']
    
    def test_returns_extraction_settings(self):
        """Test that default config includes extraction settings."""
        from main import get_default_config
        
        config = get_default_config()
        
        assert 'extraction' in config
        assert 'include_property_sets' in config['extraction']
        assert 'include_materials' in config['extraction']


class TestParseArguments:
    """Tests for parse_arguments function."""
    
    def test_default_arguments(self, monkeypatch):
        """Test default argument values."""
        from main import parse_arguments
        
        monkeypatch.setattr(sys, 'argv', ['main.py'])
        args = parse_arguments()
        
        assert args.ifc_file is None
        assert args.config == 'config.yaml'
        assert args.clear_db is False
        assert args.dry_run is False
    
    def test_ifc_file_argument(self, monkeypatch):
        """Test --ifc-file argument."""
        from main import parse_arguments
        
        monkeypatch.setattr(sys, 'argv', ['main.py', '--ifc-file', 'test.ifc'])
        args = parse_arguments()
        
        assert args.ifc_file == 'test.ifc'
    
    def test_clear_db_flag(self, monkeypatch):
        """Test --clear-db flag."""
        from main import parse_arguments
        
        monkeypatch.setattr(sys, 'argv', ['main.py', '--clear-db'])
        args = parse_arguments()
        
        assert args.clear_db is True
    
    def test_config_argument(self, monkeypatch):
        """Test --config argument."""
        from main import parse_arguments
        
        monkeypatch.setattr(sys, 'argv', ['main.py', '--config', 'custom.yaml'])
        args = parse_arguments()
        
        assert args.config == 'custom.yaml'
    
    def test_dry_run_flag(self, monkeypatch):
        """Test --dry-run flag."""
        from main import parse_arguments
        
        monkeypatch.setattr(sys, 'argv', ['main.py', '--dry-run'])
        args = parse_arguments()
        
        assert args.dry_run is True
    
    def test_log_level_argument(self, monkeypatch):
        """Test --log-level argument."""
        from main import parse_arguments
        
        monkeypatch.setattr(sys, 'argv', ['main.py', '--log-level', 'DEBUG'])
        args = parse_arguments()
        
        assert args.log_level == 'DEBUG'


class TestMain:
    """Tests for main function."""
    
    @patch('main.save_to_neo4j')
    @patch('main.filter_physical_elements')
    @patch('main.load_dotenv')
    def test_dry_run_does_not_save(
        self, mock_load_env, mock_filter, mock_save,
        monkeypatch, temp_config_file, temp_ifc_file
    ):
        """Test that dry run doesn't save to database."""
        from main import main
        
        # Create a mock IFC file
        temp_ifc_file.write_text("ISO-10303-21;")
        
        mock_filter.return_value = ({'IfcWall': []}, MagicMock())
        
        monkeypatch.setattr(sys, 'argv', [
            'main.py',
            '--dry-run',
            '--ifc-file', str(temp_ifc_file),
            '--config', str(temp_config_file),
        ])
        monkeypatch.setenv('NEO4J_URI', 'bolt://localhost:7687')
        monkeypatch.setenv('NEO4J_USER', 'neo4j')
        monkeypatch.setenv('NEO4J_PASSWORD', 'password')
        
        result = main()
        
        assert result == 0
        mock_save.assert_not_called()
    
    def test_missing_ifc_file_returns_error(self, monkeypatch, temp_config_file):
        """Test that missing IFC file returns error code."""
        from main import main
        
        monkeypatch.setattr(sys, 'argv', [
            'main.py',
            '--config', str(temp_config_file),
        ])
        # Don't set IFC_FILE_PATH
        monkeypatch.delenv('IFC_FILE_PATH', raising=False)
        
        result = main()
        
        assert result == 1
    
    def test_missing_neo4j_settings_returns_error(
        self, monkeypatch, temp_config_file, temp_ifc_file
    ):
        """Test that missing Neo4j settings returns error code."""
        from main import main
        
        temp_ifc_file.write_text("ISO-10303-21;")
        
        monkeypatch.setattr(sys, 'argv', [
            'main.py',
            '--ifc-file', str(temp_ifc_file),
            '--config', str(temp_config_file),
        ])
        # Clear Neo4j environment variables
        monkeypatch.delenv('NEO4J_URI', raising=False)
        monkeypatch.delenv('NEO4J_USER', raising=False)
        monkeypatch.delenv('NEO4J_PASSWORD', raising=False)
        
        result = main()
        
        assert result == 1

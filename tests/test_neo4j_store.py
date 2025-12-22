"""
Tests for the Neo4j store module.
"""

import pytest
from unittest.mock import patch, MagicMock

from ifc_graph import (
    Neo4jConnection,
    DatabaseConnectionError,
    DatabaseOperationError,
)


class TestNeo4jConnection:
    """Tests for Neo4jConnection class."""

    def test_connection_initialization(self, neo4j_test_config):
        """Test that the connection can be initialized."""
        conn = Neo4jConnection(
            uri=neo4j_test_config['uri'],
            username=neo4j_test_config['user'],
            password=neo4j_test_config['password'],
        )
        
        assert conn.uri == neo4j_test_config['uri']
        assert conn.username == neo4j_test_config['user']
        assert conn.password == neo4j_test_config['password']
        assert conn._driver is None

    def test_connection_default_retry_settings(self, neo4j_test_config):
        """Test default retry settings."""
        conn = Neo4jConnection(
            uri=neo4j_test_config['uri'],
            username=neo4j_test_config['user'],
            password=neo4j_test_config['password'],
        )
        
        assert conn.max_retries == 3
        assert conn.retry_delay == 1.0

    def test_connection_custom_retry_settings(self, neo4j_test_config):
        """Test custom retry settings."""
        conn = Neo4jConnection(
            uri=neo4j_test_config['uri'],
            username=neo4j_test_config['user'],
            password=neo4j_test_config['password'],
            max_retries=5,
            retry_delay=2.0,
        )
        
        assert conn.max_retries == 5
        assert conn.retry_delay == 2.0

    @patch('ifc_graph.neo4j_store.GraphDatabase')
    def test_connection_success(self, mock_graph_db, neo4j_test_config):
        """Test successful connection to Neo4j."""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        conn = Neo4jConnection(
            uri=neo4j_test_config['uri'],
            username=neo4j_test_config['user'],
            password=neo4j_test_config['password'],
        )
        conn.connect()
        
        mock_graph_db.driver.assert_called_once()
        mock_driver.verify_connectivity.assert_called_once()
        assert conn._driver is not None

    @patch('ifc_graph.neo4j_store.GraphDatabase')
    def test_connection_close(self, mock_graph_db, neo4j_test_config):
        """Test closing the connection."""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        conn = Neo4jConnection(
            uri=neo4j_test_config['uri'],
            username=neo4j_test_config['user'],
            password=neo4j_test_config['password'],
        )
        conn.connect()
        conn.close()
        
        mock_driver.close.assert_called_once()
        assert conn._driver is None

    @patch('ifc_graph.neo4j_store.GraphDatabase')
    def test_connection_context_manager(self, mock_graph_db, neo4j_test_config):
        """Test using connection as context manager."""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        with Neo4jConnection(
            uri=neo4j_test_config['uri'],
            username=neo4j_test_config['user'],
            password=neo4j_test_config['password'],
        ) as conn:
            assert conn._driver is not None
        
        mock_driver.close.assert_called_once()

    def test_session_without_connection(self, neo4j_test_config):
        """Test that session raises error when not connected."""
        conn = Neo4jConnection(
            uri=neo4j_test_config['uri'],
            username=neo4j_test_config['user'],
            password=neo4j_test_config['password'],
        )
        
        with pytest.raises(DatabaseConnectionError, match="Not connected"):
            with conn.session():
                pass


class TestDatabaseOperations:
    """Tests for database operation functions."""

    @patch('ifc_graph.neo4j_store.load_query')
    def test_clear_database(self, mock_load_query):
        """Test clear_database function."""
        from ifc_graph.neo4j_store import clear_database
        
        mock_session = MagicMock()
        mock_load_query.return_value = "MATCH (n) DETACH DELETE n"
        
        clear_database(mock_session)
        
        mock_load_query.assert_called_with("clear_database")
        mock_session.run.assert_called_once()

    @patch('ifc_graph.neo4j_store.load_query')
    def test_create_project_node(self, mock_load_query):
        """Test create_project_node function."""
        from ifc_graph.neo4j_store import create_project_node
        
        mock_session = MagicMock()
        mock_load_query.return_value = "CREATE (p:Project {id: $id, name: $name})"
        
        mock_project = MagicMock()
        mock_project.id.return_value = 1
        mock_project.Name = "Test Project"
        mock_project.Description = "Description"
        mock_project.Phase = "Design"
        
        project_id = create_project_node(mock_session, mock_project)
        
        assert project_id == "1"
        mock_session.run.assert_called_once()


class TestBatchOperations:
    """Tests for batch operation functions."""

    @patch('ifc_graph.neo4j_store.load_query')
    @patch('ifc_graph.neo4j_store.extract_element_properties')
    @patch('ifc_graph.neo4j_store.extract_spatial_info')
    @patch('ifc_graph.neo4j_store.extract_material_info')
    @patch('ifc_graph.neo4j_store.extract_property_sets')
    def test_batch_create_elements(
        self,
        mock_psets,
        mock_materials,
        mock_spatial,
        mock_props,
        mock_load_query
    ):
        """Test batch_create_elements function."""
        from ifc_graph.neo4j_store import batch_create_elements
        
        mock_session = MagicMock()
        mock_load_query.return_value = "CREATE query"
        mock_props.return_value = {'id': '1', 'name': 'Element'}
        mock_spatial.return_value = []
        mock_materials.return_value = []
        mock_psets.return_value = []
        
        mock_element = MagicMock()
        elements = [mock_element]
        config = {'include_materials': True, 'include_property_sets': True}
        
        count, spatial, materials, psets = batch_create_elements(
            mock_session, elements, config
        )
        
        assert count == 1
        assert spatial == []
        assert materials == []

    @patch('ifc_graph.neo4j_store.load_query')
    def test_batch_create_structures(self, mock_load_query):
        """Test batch_create_structures function."""
        from ifc_graph.neo4j_store import batch_create_structures
        
        mock_session = MagicMock()
        mock_load_query.return_value = "MERGE query"
        
        spatial_info = [
            {'id': '100', 'name': 'Level 1', 'type': 'IfcBuildingStorey', 'long_name': '', 'elevation': 0.0}
        ]
        
        count = batch_create_structures(mock_session, spatial_info)
        
        assert count == 1
        mock_session.run.assert_called_once()

    @patch('ifc_graph.neo4j_store.load_query')
    def test_batch_create_structures_empty(self, mock_load_query):
        """Test batch_create_structures with empty list."""
        from ifc_graph.neo4j_store import batch_create_structures
        
        mock_session = MagicMock()
        
        count = batch_create_structures(mock_session, [])
        
        assert count == 0
        mock_session.run.assert_not_called()

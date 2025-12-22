"""
Tests for the query loader module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from ifc_graph import QueryLoader, load_query
from ifc_graph.query_loader import (
    get_queries_directory,
    list_available_queries,
    clear_cache,
    validate_queries,
)


class TestQueryLoader:
    """Tests for QueryLoader class."""

    def test_loader_initialization(self):
        """Test that the loader can be initialized."""
        loader = QueryLoader()
        assert loader._use_cache is True
        assert loader._cache == {}

    def test_loader_custom_directory(self, tmp_path):
        """Test loader with custom directory."""
        loader = QueryLoader(queries_dir=tmp_path, use_cache=False)
        assert loader.queries_dir == tmp_path
        assert loader._use_cache is False

    def test_loader_list_queries(self, tmp_path):
        """Test listing available queries."""
        # Create some test query files
        (tmp_path / "query1.cypher").write_text("MATCH (n) RETURN n")
        (tmp_path / "query2.cypher").write_text("CREATE (n:Node)")
        
        loader = QueryLoader(queries_dir=tmp_path)
        queries = loader.list_queries()
        
        assert "query1" in queries
        assert "query2" in queries

    def test_loader_load_query(self, tmp_path):
        """Test loading a query."""
        query_content = "MATCH (n:Element) RETURN n"
        (tmp_path / "test_query.cypher").write_text(query_content)
        
        loader = QueryLoader(queries_dir=tmp_path)
        result = loader.load("test_query")
        
        assert result == query_content

    def test_loader_query_not_found(self, tmp_path):
        """Test loading non-existent query raises error."""
        loader = QueryLoader(queries_dir=tmp_path)
        
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent")

    def test_loader_caching(self, tmp_path):
        """Test that queries are cached."""
        query_content = "MATCH (n) RETURN n"
        (tmp_path / "cached_query.cypher").write_text(query_content)
        
        loader = QueryLoader(queries_dir=tmp_path, use_cache=True)
        
        # First load
        result1 = loader.load("cached_query")
        assert "cached_query" in loader._cache
        
        # Modify file (won't affect cached result)
        (tmp_path / "cached_query.cypher").write_text("DIFFERENT QUERY")
        
        # Second load should return cached value
        result2 = loader.load("cached_query")
        assert result1 == result2

    def test_loader_clear_cache(self, tmp_path):
        """Test clearing the cache."""
        query_content = "MATCH (n) RETURN n"
        (tmp_path / "query.cypher").write_text(query_content)
        
        loader = QueryLoader(queries_dir=tmp_path)
        loader.load("query")
        
        assert len(loader._cache) > 0
        
        loader.clear_cache()
        assert len(loader._cache) == 0


class TestModuleFunctions:
    """Tests for module-level query loader functions."""

    def test_get_queries_directory(self):
        """Test getting the queries directory."""
        queries_dir = get_queries_directory()
        assert queries_dir.name == "cypher_queries"
        assert queries_dir.parent.name == "ifc_graph"

    def test_list_available_queries(self):
        """Test listing available queries in the package."""
        queries = list_available_queries()
        
        # Should find the packaged queries
        assert isinstance(queries, list)
        # Common queries that should exist
        expected_queries = [
            "clear_database",
            "create_project",
            "create_elements_batch",
        ]
        for expected in expected_queries:
            assert expected in queries, f"Expected query '{expected}' not found"

    def test_load_query_success(self):
        """Test loading a packaged query."""
        query = load_query("clear_database")
        assert "MATCH" in query or "DELETE" in query

    def test_load_query_caching(self):
        """Test that load_query uses caching."""
        # Clear cache first
        clear_cache()
        
        # Load query twice
        query1 = load_query("clear_database", use_cache=True)
        query2 = load_query("clear_database", use_cache=True)
        
        assert query1 == query2

    def test_load_query_no_cache(self):
        """Test loading query without cache."""
        query = load_query("clear_database", use_cache=False)
        assert isinstance(query, str)

    def test_validate_queries(self):
        """Test validating all queries."""
        results = validate_queries()
        
        assert isinstance(results, dict)
        # All packaged queries should be valid
        for query_name, is_valid in results.items():
            assert is_valid, f"Query '{query_name}' is invalid"

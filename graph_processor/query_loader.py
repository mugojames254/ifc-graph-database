"""
Query Loader Module

Loads Cypher queries from external .cypher files for cleaner code organization.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Cache for loaded queries
_query_cache: dict[str, str] = {}


def get_queries_directory() -> Path:
    """Get the path to the cypher_queries directory."""
    return Path(__file__).parent.parent / "cypher_queries"


def load_query(query_name: str, use_cache: bool = True) -> str:
    """
    Load a Cypher query from a .cypher file.
    
    Args:
        query_name: Name of the query file (without .cypher extension)
        use_cache: Whether to use cached queries (default: True)
    
    Returns:
        The Cypher query string
    
    Raises:
        FileNotFoundError: If the query file doesn't exist
        IOError: If there's an error reading the file
    """
    if use_cache and query_name in _query_cache:
        logger.debug(f"Using cached query: {query_name}")
        return _query_cache[query_name]
    
    query_path = get_queries_directory() / f"{query_name}.cypher"
    
    if not query_path.exists():
        raise FileNotFoundError(f"Query file not found: {query_path}")
    
    try:
        query = query_path.read_text(encoding='utf-8')
        
        # Cache the query
        if use_cache:
            _query_cache[query_name] = query
        
        logger.debug(f"Loaded query from file: {query_name}")
        return query
        
    except IOError as e:
        logger.error(f"Error reading query file {query_path}: {e}")
        raise


def clear_cache() -> None:
    """Clear the query cache."""
    _query_cache.clear()
    logger.debug("Query cache cleared")


def list_available_queries() -> list[str]:
    """
    List all available query files.
    
    Returns:
        List of query names (without .cypher extension)
    """
    queries_dir = get_queries_directory()
    
    if not queries_dir.exists():
        return []
    
    return [f.stem for f in queries_dir.glob("*.cypher")]


def validate_queries() -> dict[str, bool]:
    """
    Validate that all query files exist and are readable.
    
    Returns:
        Dictionary mapping query names to their validity status
    """
    results = {}
    
    for query_name in list_available_queries():
        try:
            load_query(query_name, use_cache=False)
            results[query_name] = True
        except Exception as e:
            logger.warning(f"Invalid query {query_name}: {e}")
            results[query_name] = False
    
    return results

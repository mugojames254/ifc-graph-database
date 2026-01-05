"""
IFC Graph Database

A Python library for converting IFC BIM models to Neo4j graph databases.
Enables graph-based querying of building information models.
"""

from .element_filter import (
    IFCElementFilter,
    IFCLoadError,
    IFCValidationError,
    filter_physical_elements,
    load_ifc_file,
    extract_element_properties,
    extract_spatial_info,
    extract_material_info,
    extract_property_sets,
    extract_spatial_hierarchy,
    extract_all_structures,
)
from .neo4j_store import (
    Neo4jConnection,
    DatabaseConnectionError,
    DatabaseOperationError,
    save_to_neo4j,
)
from .query_loader import QueryLoader, load_query

__version__ = "0.1.0"
__author__ = "James Mugo"
__email__ = "deeplearningcentral@gmail.com"

__all__ = [
    # Element Filter
    "IFCElementFilter",
    "IFCLoadError",
    "IFCValidationError",
    "filter_physical_elements",
    "load_ifc_file",
    "extract_element_properties",
    "extract_spatial_info",
    "extract_material_info",
    "extract_property_sets",
    "extract_spatial_hierarchy",
    "extract_all_structures",
    # Neo4j Store
    "Neo4jConnection",
    "DatabaseConnectionError",
    "DatabaseOperationError",
    "save_to_neo4j",
    # Query Loader
    "QueryLoader",
    "load_query",
    # Metadata
    "__version__",
]

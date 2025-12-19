"""
Neo4j Store Module

Saves IFC elements to Neo4j database using batch operations for performance.
Includes robust error handling and connection management.
"""

import logging
import time
from typing import Any, Optional
from contextlib import contextmanager

from neo4j import GraphDatabase
from neo4j.exceptions import (
    ServiceUnavailable,
    AuthError,
    Neo4jError,
)

from .query_loader import load_query
from .element_filter import (
    extract_element_properties,
    extract_spatial_info,
    extract_material_info,
    extract_property_sets,
)

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when there's an error connecting to the database."""
    pass


class DatabaseOperationError(Exception):
    """Raised when a database operation fails."""
    pass


class Neo4jConnection:
    """
    Manages Neo4j database connections with retry logic and proper cleanup.
    """
    
    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        self.uri = uri
        self.username = username
        self.password = password
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._driver = None
    
    def connect(self) -> None:
        """
        Establish connection to Neo4j database with retry logic.
        
        Raises:
            DatabaseConnectionError: If connection cannot be established
        """
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Connecting to Neo4j (attempt {attempt}/{self.max_retries})...")
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password)
                )
                # Verify connection
                self._driver.verify_connectivity()
                logger.info("Successfully connected to Neo4j")
                return
                
            except AuthError as e:
                raise DatabaseConnectionError(
                    f"Authentication failed. Check username/password: {e}"
                ) from e
                
            except ServiceUnavailable as e:
                last_error = e
                if attempt < self.max_retries:
                    logger.warning(
                        f"Connection attempt {attempt} failed. Retrying in {self.retry_delay}s..."
                    )
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                raise DatabaseConnectionError(
                    f"Unexpected error connecting to Neo4j: {e}"
                ) from e
        
        raise DatabaseConnectionError(
            f"Failed to connect after {self.max_retries} attempts: {last_error}"
        )
    
    def close(self) -> None:
        """Close the database connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")
    
    @contextmanager
    def session(self):
        """Context manager for database sessions."""
        if not self._driver:
            raise DatabaseConnectionError("Not connected to database")
        
        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def clear_database(session) -> None:
    """
    Clear all nodes and relationships from the database.
    
    Args:
        session: Neo4j session
    """
    logger.warning("Clearing entire database...")
    query = load_query("clear_database")
    session.run(query)
    logger.info("Database cleared")


def create_project_node(session, project) -> str:
    """
    Create the project node in the database.
    
    Args:
        session: Neo4j session
        project: IFC project entity
    
    Returns:
        Project ID
    """
    project_id = str(project.id())
    
    query = load_query("create_project")
    session.run(
        query,
        id=project_id,
        name=getattr(project, 'Name', None) or 'Unnamed Project',
        description=getattr(project, 'Description', None) or '',
        phase=getattr(project, 'Phase', None) or '',
    )
    
    logger.info(f"Created project node: {project_id}")
    return project_id


def batch_create_elements(
    session,
    elements: list,
    config: dict,
    batch_size: int = 500
) -> tuple[int, list[dict], list[dict], list[dict]]:
    """
    Batch create element nodes with properties.
    
    Args:
        session: Neo4j session
        elements: List of IFC elements
        config: Extraction configuration
        batch_size: Number of elements per batch
    
    Returns:
        Tuple of (element count, spatial info list, materials list, property sets list)
    """
    all_element_data = []
    all_spatial_info = []
    all_materials = []
    all_property_sets = []
    
    # Extract data from all elements
    for element in elements:
        # Basic properties
        elem_data = extract_element_properties(element, config)
        all_element_data.append(elem_data)
        
        # Spatial containment
        spatial_info = extract_spatial_info(element)
        for info in spatial_info:
            info['element_id'] = elem_data['id']
        all_spatial_info.extend(spatial_info)
        
        # Materials
        if config.get('include_materials', True):
            materials = extract_material_info(element)
            all_materials.extend(materials)
        
        # Property sets
        if config.get('include_property_sets', True):
            max_props = config.get('max_properties_per_element', 50)
            psets = extract_property_sets(element, max_props)
            all_property_sets.extend(psets)
    
    # Batch insert elements
    query = load_query("create_elements_batch")
    
    for i in range(0, len(all_element_data), batch_size):
        batch = all_element_data[i:i + batch_size]
        session.run(query, elements=batch)
        logger.debug(f"Created element batch {i // batch_size + 1}")
    
    return len(all_element_data), all_spatial_info, all_materials, all_property_sets


def batch_create_structures(session, spatial_info: list[dict], batch_size: int = 500) -> int:
    """
    Batch create or merge structure nodes.
    
    Args:
        session: Neo4j session
        spatial_info: List of spatial structure info dictionaries
        batch_size: Number of structures per batch
    
    Returns:
        Number of structures processed
    """
    if not spatial_info:
        return 0
    
    # Deduplicate structures by ID
    unique_structures = {}
    for info in spatial_info:
        struct_id = info.get('id')
        if struct_id and struct_id not in unique_structures:
            unique_structures[struct_id] = {
                'id': struct_id,
                'name': info.get('name', 'Unnamed'),
                'type': info.get('type', ''),
                'long_name': info.get('long_name', ''),
                'elevation': info.get('elevation'),
            }
    
    structures = list(unique_structures.values())
    query = load_query("create_structures_batch")
    
    for i in range(0, len(structures), batch_size):
        batch = structures[i:i + batch_size]
        session.run(query, structures=batch)
    
    logger.info(f"Created {len(structures)} structure nodes")
    return len(structures)


def batch_create_project_relationships(
    session,
    project_id: str,
    element_ids: list[str],
    batch_size: int = 500
) -> None:
    """
    Batch create CONTAINS relationships from project to elements.
    
    Args:
        session: Neo4j session
        project_id: Project node ID
        element_ids: List of element IDs
        batch_size: Number of relationships per batch
    """
    query = load_query("create_project_contains")
    
    for i in range(0, len(element_ids), batch_size):
        batch = element_ids[i:i + batch_size]
        session.run(query, project_id=project_id, element_ids=batch)
    
    logger.debug(f"Created {len(element_ids)} project->element relationships")


def batch_create_structure_relationships(
    session,
    spatial_info: list[dict],
    batch_size: int = 500
) -> None:
    """
    Batch create CONTAINS relationships from structures to elements.
    
    Args:
        session: Neo4j session
        spatial_info: List of spatial info with element_id and structure id
        batch_size: Number of relationships per batch
    """
    if not spatial_info:
        return
    
    containments = [
        {'structure_id': info['id'], 'element_id': info['element_id']}
        for info in spatial_info
        if 'element_id' in info
    ]
    
    query = load_query("create_structure_contains")
    
    for i in range(0, len(containments), batch_size):
        batch = containments[i:i + batch_size]
        session.run(query, containments=batch)
    
    logger.debug(f"Created {len(containments)} structure->element relationships")


def batch_create_materials(
    session,
    materials: list[dict],
    batch_size: int = 500
) -> int:
    """
    Batch create material nodes and relationships.
    
    Args:
        session: Neo4j session
        materials: List of material info dictionaries
        batch_size: Number of materials per batch
    
    Returns:
        Number of material relationships created
    """
    if not materials:
        return 0
    
    query = load_query("create_materials_batch")
    
    for i in range(0, len(materials), batch_size):
        batch = materials[i:i + batch_size]
        session.run(query, materials=batch)
    
    logger.info(f"Created {len(materials)} material relationships")
    return len(materials)


def create_metadata(session, data: dict) -> None:
    """
    Create metadata node with import information.
    
    Args:
        session: Neo4j session
        data: Metadata dictionary
    """
    query = load_query("create_metadata")
    session.run(
        query,
        timestamp=data.get('timestamp', time.strftime("%Y-%m-%d %H:%M:%S")),
        count=data.get('element_count', 0),
        types=data.get('types', ''),
        ifc_file=data.get('ifc_file', ''),
        duration=data.get('duration', 0.0),
    )
    logger.info("Created metadata node")


def save_to_neo4j(
    filtered_elements: dict,
    ifc_file,
    uri: str,
    username: str,
    password: str,
    clear_db: bool = False,
    config: Optional[dict] = None
) -> dict:
    """
    Saves filtered IFC elements to Neo4j database using batch operations.
    
    Args:
        filtered_elements: Dictionary of element type -> elements list
        ifc_file: Loaded IFC file object
        uri: Neo4j connection URI
        username: Neo4j username
        password: Neo4j password
        clear_db: Whether to clear the database before import (default: False)
        config: Extraction configuration
    
    Returns:
        Dictionary with import statistics
    
    Raises:
        DatabaseConnectionError: If connection fails
        DatabaseOperationError: If database operations fail
    """
    if config is None:
        config = {
            'include_materials': True,
            'include_property_sets': True,
            'max_properties_per_element': 50,
        }
    
    start_time = time.time()
    stats = {
        'elements': 0,
        'structures': 0,
        'materials': 0,
        'property_sets': 0,
    }
    
    try:
        with Neo4jConnection(uri, username, password) as conn:
            with conn.session() as session:
                # Optionally clear database
                if clear_db:
                    clear_database(session)
                
                # Create project node
                project = ifc_file.by_type("IfcProject")[0]
                project_id = create_project_node(session, project)
                
                # Process all elements
                all_spatial_info = []
                all_materials = []
                all_element_ids = []
                
                for element_type, elements in filtered_elements.items():
                    logger.info(f"Processing {len(elements)} {element_type} elements...")
                    
                    count, spatial, materials, psets = batch_create_elements(
                        session, elements, config
                    )
                    
                    stats['elements'] += count
                    all_spatial_info.extend(spatial)
                    all_materials.extend(materials)
                    
                    # Collect element IDs for project relationships
                    for elem in elements:
                        all_element_ids.append(str(elem.id()))
                
                # Create relationships
                batch_create_project_relationships(session, project_id, all_element_ids)
                
                # Create structures and their relationships
                stats['structures'] = batch_create_structures(session, all_spatial_info)
                batch_create_structure_relationships(session, all_spatial_info)
                
                # Create materials
                stats['materials'] = batch_create_materials(session, all_materials)
                
                # Create metadata
                duration = time.time() - start_time
                create_metadata(session, {
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'element_count': stats['elements'],
                    'types': ", ".join(filtered_elements.keys()),
                    'ifc_file': str(ifc_file.header.file_name.name if hasattr(ifc_file, 'header') else 'Unknown'),
                    'duration': round(duration, 2),
                })
        
        save_time = time.time() - start_time
        logger.info(f"Saved {stats['elements']} elements to Neo4j in {save_time:.2f} seconds")
        
        return stats
        
    except DatabaseConnectionError:
        raise
    except Neo4jError as e:
        raise DatabaseOperationError(f"Database operation failed: {e}") from e
    except Exception as e:
        raise DatabaseOperationError(f"Unexpected error during save: {e}") from e

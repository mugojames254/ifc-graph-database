"""
Element Filter Module

Filters and extracts physical elements from IFC files with configurable element types
and enhanced property extraction for richer graph models.
"""

import logging
import time
from typing import Any, Optional

import ifcopenshell

logger = logging.getLogger(__name__)

# Key properties to flatten onto Element nodes (common Pset_* properties)
KEY_PROPERTIES = {
    'IsExternal', 'LoadBearing', 'FireRating', 'ThermalTransmittance',
    'AcousticRating', 'Reference', 'Status', 'Combustible', 'SurfaceSpreadOfFlame'
}

# Quantity mappings by element type prefix
QUANTITY_MAPPINGS = {
    'IfcWall': ['Width', 'Height', 'Length', 'GrossArea', 'NetArea', 'GrossVolume'],
    'IfcSlab': ['Width', 'GrossArea', 'NetArea', 'GrossVolume', 'Perimeter'],
    'IfcDoor': ['Height', 'Width', 'Area'],
    'IfcWindow': ['Height', 'Width', 'Area'],
    'IfcBeam': ['Length', 'CrossSectionArea', 'GrossVolume', 'NetVolume'],
    'IfcColumn': ['Length', 'CrossSectionArea', 'GrossVolume', 'NetVolume'],
    'IfcSpace': ['GrossFloorArea', 'NetFloorArea', 'GrossVolume', 'NetVolume', 'Height'],
    'IfcRoof': ['GrossArea', 'NetArea', 'GrossVolume'],
    'IfcStair': ['NumberOfRiser', 'NumberOfTreads', 'RiserHeight', 'TreadLength'],
}


class IFCLoadError(Exception):
    """Raised when there's an error loading an IFC file."""
    pass


class IFCValidationError(Exception):
    """Raised when an IFC file fails validation."""
    pass


class IFCElementFilter:
    """
    Filter and extract elements from IFC files.
    
    This class provides a convenient interface for loading IFC files
    and extracting elements with their properties.
    """
    
    def __init__(self, file_path: str, config: Optional[dict] = None):
        """
        Initialize the IFC element filter.
        
        Args:
            file_path: Path to the IFC file
            config: Optional extraction configuration
        """
        self.file_path = file_path
        self.config = config or {
            'include_property_sets': True,
            'include_materials': True,
            'max_properties_per_element': 50,
        }
        self._ifc_file = None
    
    def load(self) -> ifcopenshell.file:
        """Load the IFC file."""
        self._ifc_file = load_ifc_file(self.file_path)
        return self._ifc_file
    
    @property
    def ifc_file(self) -> ifcopenshell.file:
        """Get the loaded IFC file, loading it if necessary."""
        if self._ifc_file is None:
            self.load()
        return self._ifc_file
    
    def extract_elements(
        self, 
        element_types: Optional[list[str]] = None
    ) -> tuple[dict, ifcopenshell.file]:
        """
        Extract elements from the IFC file.
        
        Args:
            element_types: List of IFC element types to extract
        
        Returns:
            Tuple of (filtered_elements dictionary, ifc_file object)
        """
        return filter_physical_elements(
            self.file_path,
            element_types=element_types,
            config=self.config
        )


def validate_ifc_file(file_path: str) -> None:
    """
    Validate that an IFC file exists and is accessible.
    
    Args:
        file_path: Path to the IFC file
    
    Raises:
        IFCValidationError: If the file is invalid or inaccessible
    """
    from pathlib import Path
    
    path = Path(file_path)
    
    if not path.exists():
        raise IFCValidationError(f"IFC file not found: {file_path}")
    
    if not path.is_file():
        raise IFCValidationError(f"Path is not a file: {file_path}")
    
    if path.suffix.lower() not in ['.ifc', '.ifczip']:
        raise IFCValidationError(f"Invalid file extension: {path.suffix}. Expected .ifc or .ifczip")
    
    if path.stat().st_size == 0:
        raise IFCValidationError(f"IFC file is empty: {file_path}")


def load_ifc_file(file_path: str) -> ifcopenshell.file:
    """
    Load an IFC file with error handling.
    
    Args:
        file_path: Path to the IFC file
    
    Returns:
        Loaded IFC file object
    
    Raises:
        IFCLoadError: If there's an error loading the file
    """
    try:
        validate_ifc_file(file_path)
        logger.info(f"Loading IFC file: {file_path}")
        return ifcopenshell.open(file_path)
    except IFCValidationError:
        raise
    except Exception as e:
        raise IFCLoadError(f"Failed to load IFC file: {file_path}. Error: {e}") from e


def extract_element_properties(element: Any, config: dict) -> dict[str, Any]:
    """
    Extract properties from an IFC element for graph storage.
    Includes key properties and quantities flattened onto the element.
    
    Args:
        element: IFC element to extract properties from
        config: Extraction configuration
    
    Returns:
        Dictionary of extracted properties
    """
    props = {
        'id': str(element.id()),
        'name': getattr(element, 'Name', None) or 'Unnamed',
        'guid': getattr(element, 'GlobalId', '') or '',
        'type': element.is_a(),
        'object_type': getattr(element, 'ObjectType', None) or '',
        'description': getattr(element, 'Description', None) or '',
        'tag': getattr(element, 'Tag', None) or '',
    }
    
    # For IfcSpace, also extract LongName
    if element.is_a('IfcSpace'):
        props['long_name'] = getattr(element, 'LongName', None) or ''
    
    # Extract key properties and quantities directly onto element
    if config.get('include_property_sets', True):
        key_props = _extract_key_properties(element)
        props.update(key_props)
        
        quantities = _extract_quantities(element)
        props.update(quantities)
    
    return props


def _extract_key_properties(element: Any) -> dict[str, Any]:
    """Extract commonly-queried properties directly from property sets."""
    props = {}
    try:
        if not hasattr(element, 'IsDefinedBy'):
            return props
        for definition in element.IsDefinedBy:
            if not definition.is_a('IfcRelDefinesByProperties'):
                continue
            prop_def = definition.RelatingPropertyDefinition
            if not prop_def.is_a('IfcPropertySet'):
                continue
            if not hasattr(prop_def, 'HasProperties'):
                continue
            for prop in prop_def.HasProperties:
                if prop.Name in KEY_PROPERTIES:
                    value = _get_property_value(prop)
                    if value is not None:
                        props[prop.Name] = value
    except Exception as e:
        logger.debug(f"Error extracting key properties for {element.id()}: {e}")
    return props


def _extract_quantities(element: Any) -> dict[str, Any]:
    """Extract quantities (dimensions) from IfcElementQuantity."""
    quantities = {}
    elem_type = element.is_a()
    
    # Find matching quantity names for this element type
    relevant_quantities = set()
    for type_prefix, qty_names in QUANTITY_MAPPINGS.items():
        if elem_type.startswith(type_prefix):
            relevant_quantities.update(qty_names)
            break
    
    if not relevant_quantities:
        return quantities
    
    try:
        if not hasattr(element, 'IsDefinedBy'):
            return quantities
        for definition in element.IsDefinedBy:
            if not definition.is_a('IfcRelDefinesByProperties'):
                continue
            prop_def = definition.RelatingPropertyDefinition
            if not prop_def.is_a('IfcElementQuantity'):
                continue
            if not hasattr(prop_def, 'Quantities'):
                continue
            for qty in prop_def.Quantities:
                if qty.Name not in relevant_quantities:
                    continue
                value = _get_quantity_value(qty)
                if value is not None:
                    quantities[qty.Name] = value
    except Exception as e:
        logger.debug(f"Error extracting quantities for {element.id()}: {e}")
    return quantities


def _get_quantity_value(qty) -> Optional[float]:
    """Extract numeric value from an IFC quantity."""
    try:
        if qty.is_a('IfcQuantityLength'):
            return float(qty.LengthValue) if qty.LengthValue is not None else None
        elif qty.is_a('IfcQuantityArea'):
            return float(qty.AreaValue) if qty.AreaValue is not None else None
        elif qty.is_a('IfcQuantityVolume'):
            return float(qty.VolumeValue) if qty.VolumeValue is not None else None
        elif qty.is_a('IfcQuantityWeight'):
            return float(qty.WeightValue) if qty.WeightValue is not None else None
        elif qty.is_a('IfcQuantityCount'):
            return float(qty.CountValue) if qty.CountValue is not None else None
    except (TypeError, ValueError):
        pass
    return None


def extract_spatial_info(element: Any) -> list[dict]:
    """
    Extract spatial containment information for an element.
    
    Args:
        element: IFC element to extract spatial info from
    
    Returns:
        List of spatial structure information dictionaries
    """
    spatial_info = []
    
    try:
        if hasattr(element, 'ContainedInStructure') and element.ContainedInStructure:
            for rel in element.ContainedInStructure:
                if rel.RelatingStructure:
                    structure = rel.RelatingStructure
                    spatial_info.append({
                        'id': str(structure.id()),
                        'name': getattr(structure, 'Name', None) or 'Unnamed',
                        'type': structure.is_a(),
                        'long_name': getattr(structure, 'LongName', None) or '',
                        'elevation': _get_elevation(structure),
                    })
    except Exception as e:
        logger.debug(f"Error extracting spatial info for element {element.id()}: {e}")
    
    return spatial_info


def _get_elevation(structure) -> Optional[float]:
    """Get elevation of a spatial structure if available."""
    try:
        if hasattr(structure, 'Elevation') and structure.Elevation is not None:
            return float(structure.Elevation)
    except (TypeError, ValueError):
        pass
    return None


def extract_spatial_hierarchy(ifc_file) -> list[dict]:
    """
    Extract spatial hierarchy relationships from IfcRelAggregates.
    Returns list of parent->child relationships for Site->Building->Storey->Space.
    
    Args:
        ifc_file: Loaded IFC file object
    
    Returns:
        List of dicts with parent/child info and relationship data
    """
    hierarchy = []
    spatial_types = {'IfcSite', 'IfcBuilding', 'IfcBuildingStorey', 'IfcSpace'}
    
    try:
        for rel in ifc_file.by_type('IfcRelAggregates'):
            parent = rel.RelatingObject
            if parent is None or parent.is_a() not in spatial_types:
                continue
            
            for child in (rel.RelatedObjects or []):
                if child is None or child.is_a() not in spatial_types:
                    continue
                hierarchy.append({
                    'parent_id': str(parent.id()),
                    'parent_type': parent.is_a(),
                    'parent_name': getattr(parent, 'Name', None) or 'Unnamed',
                    'child_id': str(child.id()),
                    'child_type': child.is_a(),
                    'child_name': getattr(child, 'Name', None) or 'Unnamed',
                })
    except Exception as e:
        logger.debug(f"Error extracting spatial hierarchy: {e}")
    
    return hierarchy


def extract_all_structures(ifc_file) -> list[dict]:
    """
    Extract all spatial structure elements (Site, Building, Storey, Space).
    
    Args:
        ifc_file: Loaded IFC file object
    
    Returns:
        List of structure dictionaries
    """
    structures = []
    spatial_types = ['IfcSite', 'IfcBuilding', 'IfcBuildingStorey', 'IfcSpace']
    
    for spatial_type in spatial_types:
        try:
            for structure in ifc_file.by_type(spatial_type):
                struct_data = {
                    'id': str(structure.id()),
                    'name': getattr(structure, 'Name', None) or 'Unnamed',
                    'type': structure.is_a(),
                    'long_name': getattr(structure, 'LongName', None) or '',
                    'elevation': _get_elevation(structure),
                }
                # For spaces, extract floor area quantities
                if spatial_type == 'IfcSpace':
                    quantities = _extract_quantities(structure)
                    struct_data.update(quantities)
                structures.append(struct_data)
        except Exception as e:
            logger.debug(f"Error extracting {spatial_type}: {e}")
    
    return structures


def extract_material_info(element: Any) -> list[dict]:
    """
    Extract material information for an element.
    
    Args:
        element: IFC element to extract material info from
    
    Returns:
        List of material information dictionaries
    """
    materials = []
    
    try:
        if hasattr(element, 'HasAssociations'):
            for association in element.HasAssociations:
                if association.is_a('IfcRelAssociatesMaterial'):
                    material_select = association.RelatingMaterial
                    materials.extend(_process_material(material_select, element))
    except Exception as e:
        logger.debug(f"Error extracting materials for element {element.id()}: {e}")
    
    return materials


def _process_material(material_select, element) -> list[dict]:
    """Process a material selection and return material info."""
    materials = []
    
    if material_select is None:
        return materials
    
    try:
        # Single material
        if material_select.is_a('IfcMaterial'):
            materials.append({
                'element_id': str(element.id()),
                'material_id': str(material_select.id()),
                'material_name': getattr(material_select, 'Name', '') or '',
                'material_category': getattr(material_select, 'Category', '') or '',
            })
        
        # Material layer set
        elif material_select.is_a('IfcMaterialLayerSetUsage'):
            layer_set = material_select.ForLayerSet
            if layer_set and hasattr(layer_set, 'MaterialLayers'):
                for layer in layer_set.MaterialLayers:
                    if layer.Material:
                        materials.append({
                            'element_id': str(element.id()),
                            'material_id': str(layer.Material.id()),
                            'material_name': getattr(layer.Material, 'Name', '') or '',
                            'material_category': getattr(layer.Material, 'Category', '') or '',
                        })
        
        # Material list
        elif material_select.is_a('IfcMaterialList'):
            for mat in material_select.Materials:
                materials.append({
                    'element_id': str(element.id()),
                    'material_id': str(mat.id()),
                    'material_name': getattr(mat, 'Name', '') or '',
                    'material_category': getattr(mat, 'Category', '') or '',
                })
    except Exception as e:
        logger.debug(f"Error processing material for element {element.id()}: {e}")
    
    return materials


def extract_property_sets(element: Any, max_properties: int = 50) -> list[dict]:
    """
    Extract property sets for an element.
    
    Args:
        element: IFC element to extract property sets from
        max_properties: Maximum number of properties to extract per element
    
    Returns:
        List of property set information dictionaries
    """
    property_sets = []
    total_props = 0
    
    try:
        if hasattr(element, 'IsDefinedBy'):
            for definition in element.IsDefinedBy:
                if total_props >= max_properties:
                    break
                    
                if definition.is_a('IfcRelDefinesByProperties'):
                    prop_def = definition.RelatingPropertyDefinition
                    
                    if prop_def.is_a('IfcPropertySet'):
                        pset_data = {
                            'element_id': str(element.id()),
                            'pset_id': str(prop_def.id()),
                            'pset_name': prop_def.Name or 'Unnamed',
                            'properties': {}
                        }
                        
                        if hasattr(prop_def, 'HasProperties'):
                            for prop in prop_def.HasProperties:
                                if total_props >= max_properties:
                                    break
                                
                                prop_value = _get_property_value(prop)
                                if prop_value is not None:
                                    pset_data['properties'][prop.Name] = prop_value
                                    total_props += 1
                        
                        if pset_data['properties']:
                            property_sets.append(pset_data)
                            
    except Exception as e:
        logger.debug(f"Error extracting property sets for element {element.id()}: {e}")
    
    return property_sets


def _get_property_value(prop) -> Any:
    """Extract the value from an IFC property."""
    try:
        if prop.is_a('IfcPropertySingleValue'):
            if prop.NominalValue:
                value = prop.NominalValue.wrappedValue
                # Convert to JSON-serializable types
                if isinstance(value, (int, float, str, bool)):
                    return value
                return str(value)
    except Exception:
        pass
    return None


def filter_physical_elements(
    ifc_file_path: str,
    element_types: Optional[list[str]] = None,
    config: Optional[dict] = None
) -> tuple[dict, ifcopenshell.file]:
    """
    Filters specific physical elements from an IFC file.
    
    Args:
        ifc_file_path: Path to the IFC file
        element_types: List of IFC element types to extract (e.g., ['IfcWall', 'IfcDoor'])
        config: Extraction configuration dictionary
    
    Returns:
        Tuple of (filtered_elements dictionary, ifc_file object)
    
    Raises:
        IFCLoadError: If the file cannot be loaded
        IFCValidationError: If the file is invalid
    """
    # Default element types if none provided
    if element_types is None:
        element_types = [
            'IfcWall', 
            'IfcDoor', 
            'IfcWindow', 
            'IfcStair',
            'IfcSlab',
            'IfcRoof',
            'IfcColumn',
            'IfcBeam',
            'IfcSpace',
        ]
    
    if config is None:
        config = {
            'include_property_sets': True,
            'include_materials': True,
            'max_properties_per_element': 50,
        }
    
    logger.info(f"Loading IFC file: {ifc_file_path}")
    start_time = time.time()
    
    # Load the IFC file with error handling
    ifc_file = load_ifc_file(ifc_file_path)
    
    # Dictionary to store elements by type
    filtered_elements = {}
    
    # Filter elements
    for element_type in element_types:
        try:
            elements = ifc_file.by_type(element_type)
            if elements:
                filtered_elements[element_type] = elements
                logger.info(f"Found {len(elements)} {element_type} elements")
        except Exception as e:
            logger.warning(f"Error filtering {element_type}: {e}")
    
    load_time = time.time() - start_time
    total_elements = sum(len(elems) for elems in filtered_elements.values())
    logger.info(f"Filtered {total_elements} elements in {load_time:.2f} seconds")
    
    return filtered_elements, ifc_file

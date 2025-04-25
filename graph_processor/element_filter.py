import ifcopenshell
import time

def filter_physical_elements(ifc_file_path):
    """
    Filters specific physical elements from an IFC file.
    """
    print(f"Loading IFC file: {ifc_file_path}")
    start_time = time.time()
    
    # Load the IFC file
    ifc_file = ifcopenshell.open(ifc_file_path)
    
    # Define the element types to extract
    physical_element_types = [
        'IfcWall', 
        'IfcDoor', 
        'IfcWindow', 
        'IfcStair',
        'IfcSlab',
        'IfcRoof',
        'IfcColumn',
        'IfcBeam'
    ]
    
    # Dictionary to store elements by type
    filtered_elements = {}
    
    # Filter elements
    for element_type in physical_element_types:
        elements = ifc_file.by_type(element_type)
        if elements:
            filtered_elements[element_type] = elements
            print(f"Found {len(elements)} {element_type} elements")
    
    load_time = time.time() - start_time
    print(f"Filtered IFC data loaded in {load_time:.2f} seconds")
    
    return filtered_elements, ifc_file

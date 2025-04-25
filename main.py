from graph_processor.element_filter import filter_physical_elements
from graph_processor.neo4j_store import save_to_neo4j


def main():
    # Configuration
    ifc_file_path = "test_model.ifc"  # Update with your file path
    neo4j_uri = "bolt://localhost:7687"        # Update with your Neo4j URI
    neo4j_user = "neo4j"                       # Update with your username
    neo4j_password = "4central"                # Update with your password
    
    # Filter elements
    filtered_elements, ifc_file = filter_physical_elements(ifc_file_path)
    
    # Save to Neo4j
    save_to_neo4j(filtered_elements, ifc_file, neo4j_uri, neo4j_user, neo4j_password)
    
    print("Process completed successfully!")

if __name__ == "__main__":
    main()

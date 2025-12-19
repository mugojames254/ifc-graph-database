from graph_processor.element_filter import filter_physical_elements
from graph_processor.neo4j_store import save_to_neo4j
from dotenv import load_dotenv
import os


def main():
    # Configuration
    load_dotenv()
    ifc_file_path =os.getenv("IFC_FILE_PATH")  # Update with your file path
    neo4j_uri = os.getenv('NEO4J_URI')        # Update with your Neo4j URI
    neo4j_user =os.getenv('NEO4J_USER')                       # Update with your username
    neo4j_password =os.getenv('NEO4J_PASSWORD')                # Update with your password
    
    # Filter elements
    filtered_elements, ifc_file = filter_physical_elements(ifc_file_path)
    
    # Save to Neo4j
    save_to_neo4j(filtered_elements, ifc_file, neo4j_uri, neo4j_user, neo4j_password)
    
    print("Process completed successfully!")

if __name__ == "__main__":
    main()

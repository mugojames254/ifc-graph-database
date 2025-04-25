from neo4j import GraphDatabase

import time 


def save_to_neo4j(filtered_elements, ifc_file, uri, username, password):
    """
    Saves filtered IFC elements to Neo4j database.
    """
    print("Connecting to Neo4j database...")
    start_time = time.time()
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    # Create session
    with driver.session() as session:
        # Clear existing data (optional)
        session.run("MATCH (n) DETACH DELETE n")
        
        # Create project node 
        project = ifc_file.by_type("IfcProject")[0]
        project_name = project.Name or "Unnamed Project"
        session.run(
            "CREATE (p:Project {id: $id, name: $name, type: 'IfcProject'})",
            id=str(project.id()), name=project_name
        )
        
        # Process each element type
        total_elements = 0
        
        for element_type, elements in filtered_elements.items():
            print(f"Processing {len(elements)} {element_type} elements...")
            
            for element in elements:
                # Extract basic properties
                element_id = str(element.id())
                element_name = element.Name if hasattr(element, "Name") and element.Name else "Unnamed"
                element_guid = element.GlobalId if hasattr(element, "GlobalId") else ""
                
                # Create element node
                session.run(
                    """
                    CREATE (e:Element {
                        id: $id, 
                        name: $name, 
                        guid: $guid, 
                        type: $type
                    })
                    """,
                    id=element_id, name=element_name, guid=element_guid, type=element_type
                )
                
                # Connect to project
                session.run(
                    """
                    MATCH (p:Project {id: $project_id})
                    MATCH (e:Element {id: $element_id})
                    CREATE (p)-[:CONTAINS]->(e)
                    """,
                    project_id=str(project.id()), element_id=element_id
                )
                
                # Extract simple properties
                try:
                    if hasattr(element, "ObjectType") and element.ObjectType:
                        session.run(
                            """
                            MATCH (e:Element {id: $id})
                            SET e.objectType = $object_type
                            """,
                            id=element_id, object_type=element.ObjectType
                        )
                    
                    # Extract spatial relationships
                    if hasattr(element, "ContainedInStructure") and element.ContainedInStructure:
                        for rel in element.ContainedInStructure:
                            if rel.RelatingStructure:
                                structure_id = str(rel.RelatingStructure.id())
                                structure_type = rel.RelatingStructure.is_a()
                                structure_name = rel.RelatingStructure.Name if hasattr(rel.RelatingStructure, "Name") and rel.RelatingStructure.Name else "Unnamed"
                                
                                # Create structure node if it doesn't exist
                                session.run(
                                    """
                                    MERGE (s:Structure {id: $id})
                                    ON CREATE SET s.name = $name, s.type = $type
                                    """,
                                    id=structure_id, name=structure_name, type=structure_type
                                )
                                
                                # Connect element to structure
                                session.run(
                                    """
                                    MATCH (e:Element {id: $element_id})
                                    MATCH (s:Structure {id: $structure_id})
                                    CREATE (s)-[:CONTAINS]->(e)
                                    """,
                                    element_id=element_id, structure_id=structure_id
                                )
                except Exception as e:
                    print(f"Error processing relationships for {element_type} {element_id}: {str(e)}")
                
                total_elements += 1
        
        # Add metadata
        session.run(
            """
            CREATE (m:Metadata {
                timestamp: $timestamp,
                element_count: $count,
                filtered_types: $types
            })
            """,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            count=total_elements,
            types=", ".join(filtered_elements.keys())
        )
    
    driver.close()
    
    save_time = time.time() - start_time
    print(f"Saved {total_elements} elements to Neo4j in {save_time:.2f} seconds")

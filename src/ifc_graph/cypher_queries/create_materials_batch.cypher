// Batch create or merge Material nodes and relationships to elements
// Parameters: $materials - list of {element_id, material_id, material_name, material_category}
UNWIND $materials AS mat
MERGE (m:Material {id: mat.material_id})
ON CREATE SET 
    m.name = mat.material_name,
    m.category = mat.material_category
WITH m, mat
MATCH (e:Element {id: mat.element_id})
CREATE (e)-[:HAS_MATERIAL]->(m)
RETURN count(*) AS material_relationships_created

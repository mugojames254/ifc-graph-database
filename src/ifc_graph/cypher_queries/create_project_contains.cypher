// Create batch CONTAINS relationships between project and elements
// Parameters: $project_id, $element_ids - list of element IDs
MATCH (p:Project {id: $project_id})
UNWIND $element_ids AS elem_id
MATCH (e:Element {id: elem_id})
CREATE (p)-[:CONTAINS]->(e)
RETURN count(*) AS relationships_created

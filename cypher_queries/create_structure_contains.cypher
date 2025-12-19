// Create batch CONTAINS relationships between structures and elements
// Parameters: $containments - list of {structure_id, element_id}
UNWIND $containments AS cont
MATCH (s:Structure {id: cont.structure_id})
MATCH (e:Element {id: cont.element_id})
CREATE (s)-[:CONTAINS]->(e)
RETURN count(*) AS relationships_created

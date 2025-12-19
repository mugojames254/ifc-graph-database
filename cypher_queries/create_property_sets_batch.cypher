// Batch create PropertySet nodes and relationships
// Parameters: $property_sets - list of {element_id, pset_id, pset_name, properties}
UNWIND $property_sets AS pset
CREATE (ps:PropertySet {
    id: pset.pset_id,
    name: pset.pset_name
})
WITH ps, pset
UNWIND keys(pset.properties) AS prop_key
SET ps += {prop_key: pset.properties[prop_key]}
WITH DISTINCT ps, pset
MATCH (e:Element {id: pset.element_id})
CREATE (e)-[:HAS_PROPERTY_SET]->(ps)
RETURN count(*) AS property_sets_created

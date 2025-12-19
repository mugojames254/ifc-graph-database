// Batch create relationships between nodes
// Parameters: $relationships - list of relationship objects with from_id, to_id, rel_type
UNWIND $relationships AS rel
MATCH (from {id: rel.from_id})
MATCH (to {id: rel.to_id})
CALL apoc.create.relationship(from, rel.rel_type, {}, to) YIELD rel AS created
RETURN count(created) AS relationship_count

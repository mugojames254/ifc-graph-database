// Batch create AGGREGATES relationships for spatial hierarchy
// (IfcSite)-[:AGGREGATES]->(IfcBuilding)-[:AGGREGATES]->(IfcBuildingStorey)-[:AGGREGATES]->(IfcSpace)
// Parameters: $aggregates - list of {parent_id, child_id}
UNWIND $aggregates AS agg
MATCH (parent:Structure {id: agg.parent_id})
MATCH (child:Structure {id: agg.child_id})
MERGE (parent)-[:AGGREGATES]->(child)
RETURN count(*) AS relationships_created

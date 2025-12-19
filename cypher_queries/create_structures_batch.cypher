// Batch create or merge Structure nodes (Site, Building, Storey, Space)
// Parameters: $structures - list of structure objects
UNWIND $structures AS struct
MERGE (s:Structure {id: struct.id})
ON CREATE SET 
    s.name = struct.name,
    s.type = struct.type,
    s.long_name = struct.long_name,
    s.elevation = struct.elevation
RETURN count(s) AS structure_count

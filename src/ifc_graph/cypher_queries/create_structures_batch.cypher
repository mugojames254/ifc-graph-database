// Batch create or merge Structure nodes (Site, Building, Storey, Space)
// Parameters: $structures - list of structure objects with optional quantity properties
UNWIND $structures AS struct
MERGE (s:Structure {id: struct.id})
SET s += struct
RETURN count(s) AS structure_count

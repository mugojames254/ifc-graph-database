// Batch create Element nodes from a list of elements
// Parameters: $elements - list of element objects with properties (including quantities and key props)
UNWIND $elements AS elem
CREATE (e:Element)
SET e += elem
RETURN count(e) AS created_count

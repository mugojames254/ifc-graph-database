// Create metadata node with import information
// Parameters: $timestamp, $count, $types, $ifc_file, $duration
CREATE (m:Metadata {
    timestamp: $timestamp,
    element_count: $count,
    filtered_types: $types,
    source_file: $ifc_file,
    import_duration_seconds: $duration
})
RETURN m

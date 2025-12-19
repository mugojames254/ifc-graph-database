// Batch create Element nodes from a list of elements
// Parameters: $elements - list of element objects with properties
UNWIND $elements AS elem
CREATE (e:Element {
    id: elem.id,
    name: elem.name,
    guid: elem.guid,
    type: elem.type,
    object_type: elem.object_type,
    description: elem.description,
    tag: elem.tag
})
RETURN count(e) AS created_count

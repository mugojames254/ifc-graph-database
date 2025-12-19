// Create the IFC Project node
CREATE (p:Project {
    id: $id,
    name: $name,
    type: 'IfcProject',
    description: $description,
    phase: $phase
})
RETURN p

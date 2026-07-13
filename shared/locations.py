"""
Shared geographic reference data — the physical anchor points
representing 'home', 'work', and 'outdoors' for mock patients.

Used by BOTH the simulator (to generate believable raw GPS jittered
around these points, standing in for the physical world) and the fog
node (to classify incoming raw GPS into a zone label). This is
deliberately shared, unlike simulator/fog_node business logic, because
both layers must agree on the same underlying physical geography.
"""

LOCATION_ANCHORS = {
    "home": (51.5074, -0.1278),
    "work": (51.5155, -0.0922),
    "outdoors": (51.5033, -0.1195),
}

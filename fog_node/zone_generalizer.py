"""
Zone generalization: converts raw GPS coordinates into a coarse named
zone, and strips the raw coordinates from the outgoing event. This is
the fog node's privacy-preserving responsibility,
distinct from its alerting responsibility.

Uses simple Euclidean distance, not Haversine — acceptable at the small
scale (a few km) our mock anchors and GPS jitter operate within.
"""

from shared.locations import LOCATION_ANCHORS


def _nearest_zone(lat, lon):
    """
    Returns the name of the nearest zone (from LOCATION_ANCHORS)
    to the given latitude and longitude.
    """
    closest_zone = None
    closest_distance = float("inf")

    # Find the closest anchor point (zone) to the given coordinates
    # Euclidean distance is sufficient for small distances (a few km).
    for zone_name, (anchor_lat, anchor_lon) in LOCATION_ANCHORS.items():
        distance = ((lat - anchor_lat) ** 2 + (lon - anchor_lon) ** 2) ** 0.5
        if distance < closest_distance:
            closest_distance = distance
            closest_zone = zone_name

    return closest_zone


def generalize_location(event):
    """
    Returns a new event dict: raw_latitude/raw_longitude replaced with
    a 'zone' field. Applies to any event carrying raw coordinates
    (actuation and ambient_reading both do, as of this design decision) —
    events without them are returned unchanged.
    """
    if "raw_latitude" not in event or "raw_longitude" not in event:
        return event

    zone = _nearest_zone(event["raw_latitude"], event["raw_longitude"])

    generalized = dict(event)
    generalized.pop("raw_latitude", None)
    generalized.pop("raw_longitude", None)
    generalized["zone"] = zone

    return generalized

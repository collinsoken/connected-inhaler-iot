"""
Unit tests for the fog node's stateless/stateful detection logic.
Run with: pytest tests/test_fog_node.py -v

Covers overuse_detector, technique_detector, dose_monitor, and
zone_generalizer -- the four fog_node modules with fully
self-contained logic (no MQTT/AWS dependencies), which makes them
straightforward to unit test in isolation from the rest of the
pipeline (mqtt_client.py and main.py are integration-level and are
exercised instead via the end-to-end manual test runs documented in
the report/continuation guide, not here).
"""

from datetime import datetime, timezone

from fog_node.overuse_detector import check_overuse
from fog_node.technique_detector import check_technique
from fog_node.dose_monitor import check_low_dose
from fog_node.zone_generalizer import generalize_location
from fog_node.config import LOCATION_ANCHORS


def _actuation_event(patient_id, **overrides):
    event = {
        "event_type": "actuation",
        "patient_id": patient_id,
        "device_role": "rescue",
        "device_type": "MDI",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "inhalation_flow_rate": 35.0,
        "device_tilt_angle": 10.0,
        "remaining_doses": 100,
    }
    event.update(overrides)
    return event


class TestOveruseDetector:
    # NOTE: overuse_detector keeps its history in a module-level dict
    # keyed by patient_id, so each test below uses its own unique
    # patient_id to avoid cross-test state pollution.

    def test_below_threshold_no_alert(self):
        patient_id = "test_patient_overuse_below"
        result = False
        for _ in range(4):  # threshold fires on COUNT > 4, so 4 events must not alert
            result = check_overuse(_actuation_event(patient_id))
        assert result is False

    def test_above_threshold_alerts(self):
        patient_id = "test_patient_overuse_above"
        result = False
        for _ in range(5):  # the 5th event pushes count to 5, which is > 4
            result = check_overuse(_actuation_event(patient_id))
        assert result is True

    def test_ignores_non_rescue_events(self):
        patient_id = "test_patient_overuse_maintenance"
        event = _actuation_event(patient_id, device_role="maintenance")
        assert check_overuse(event) is False

    def test_ignores_non_actuation_events(self):
        event = {"event_type": "ambient_reading", "patient_id": "test_patient_ambient"}
        assert check_overuse(event) is False


class TestTechniqueDetector:
    def test_good_technique_no_reasons(self):
        event = _actuation_event("p1", device_type="MDI", inhalation_flow_rate=35.0, device_tilt_angle=10.0)
        assert check_technique(event) == []

    def test_low_flow_rate_flagged(self):
        event = _actuation_event("p1", device_type="MDI", inhalation_flow_rate=10.0, device_tilt_angle=10.0)
        reasons = check_technique(event)
        assert len(reasons) == 1
        assert "flow rate" in reasons[0]

    def test_excessive_tilt_flagged(self):
        event = _actuation_event("p1", device_type="MDI", inhalation_flow_rate=35.0, device_tilt_angle=45.0)
        reasons = check_technique(event)
        assert len(reasons) == 1
        assert "tilt angle" in reasons[0]

    def test_both_flow_and_tilt_flagged_simultaneously(self):
        event = _actuation_event("p1", device_type="DPI", inhalation_flow_rate=10.0, device_tilt_angle=45.0)
        assert len(check_technique(event)) == 2

    def test_device_type_aware_threshold(self):
        # 30 L/min clears MDI's 20.0 minimum but fails DPI's 40.0 minimum --
        # this is the device-type-awareness the fog node is specifically
        # designed to apply (see Architecture Reference section 6).
        mdi_event = _actuation_event("p1", device_type="MDI", inhalation_flow_rate=30.0, device_tilt_angle=10.0)
        dpi_event = _actuation_event("p1", device_type="DPI", inhalation_flow_rate=30.0, device_tilt_angle=10.0)
        assert check_technique(mdi_event) == []
        assert len(check_technique(dpi_event)) == 1


class TestDoseMonitor:
    def test_sufficient_doses_no_alert(self):
        assert check_low_dose(_actuation_event("p1", remaining_doses=100)) is False

    def test_at_threshold_alerts(self):
        assert check_low_dose(_actuation_event("p1", remaining_doses=20)) is True

    def test_below_threshold_alerts(self):
        assert check_low_dose(_actuation_event("p1", remaining_doses=5)) is True

    def test_non_actuation_event_no_alert(self):
        event = {"event_type": "ambient_reading", "remaining_doses": 0}
        assert check_low_dose(event) is False


class TestZoneGeneralizer:
    def test_generalizes_to_nearest_anchor(self):
        home_lat, home_lon = LOCATION_ANCHORS["home"]
        event = {"raw_latitude": home_lat, "raw_longitude": home_lon, "patient_id": "p1"}
        result = generalize_location(event)
        assert result["zone"] == "home"

    def test_strips_raw_coordinates(self):
        home_lat, home_lon = LOCATION_ANCHORS["home"]
        event = {"raw_latitude": home_lat, "raw_longitude": home_lon}
        result = generalize_location(event)
        assert "raw_latitude" not in result
        assert "raw_longitude" not in result

    def test_event_without_coordinates_returned_unchanged(self):
        event = {"patient_id": "p1", "event_type": "actuation"}
        assert generalize_location(event) == event

    def test_does_not_mutate_original_event(self):
        # generalize_location must return a new dict (shallow copy),
        # not mutate the caller's event in place.
        home_lat, home_lon = LOCATION_ANCHORS["home"]
        event = {"raw_latitude": home_lat, "raw_longitude": home_lon}
        generalize_location(event)
        assert "raw_latitude" in event

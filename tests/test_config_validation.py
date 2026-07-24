"""
Tests confirming simulator config validation catches invalid device
types (guards against an unvalidated device_type
silently generating wrong flow-rate data instead of raising). Also
confirms the simulator and fog node agree on the same location anchors,
which zone generalization depends on for correctness.
"""

import pytest

import simulator.config as simulator_config
from shared.locations import LOCATION_ANCHORS as SHARED_ANCHORS
from fog_node.config import LOCATION_ANCHORS as FOG_NODE_ANCHORS


def test_simulator_config_is_valid_on_import():
    # validate_config() already runs at import time in config.py;
    # calling it again here documents the invariant explicitly and
    # fails loudly in CI if it's ever accidentally removed.
    simulator_config.validate_config()


def test_simulator_and_fog_node_share_same_location_anchors():
    # Both layers MUST agree on the same physical geography -- if they
    # drift apart, fog-node zone generalization would classify GPS
    # jitter against the wrong reference points.
    assert FOG_NODE_ANCHORS == SHARED_ANCHORS


def test_invalid_device_type_raises(monkeypatch):
    bad_patients = [
        {
            "patient_id": "bad_patient",
            "devices": {
                "rescue": {"device_id": "x", "device_type": "INVALID"},
                "maintenance": {"device_id": "y", "device_type": "MDI"},
            },
        }
    ]
    monkeypatch.setattr(simulator_config, "PATIENTS", bad_patients)

    with pytest.raises(AssertionError):
        simulator_config.validate_config()


def test_missing_required_device_role_raises(monkeypatch):
    bad_patients = [
        {
            "patient_id": "bad_patient_no_maintenance",
            "devices": {
                "rescue": {"device_id": "x", "device_type": "MDI"},
                # "maintenance" role missing entirely
            },
        }
    ]
    monkeypatch.setattr(simulator_config, "PATIENTS", bad_patients)

    with pytest.raises(AssertionError):
        simulator_config.validate_config()

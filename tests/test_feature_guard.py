# kubeopt/tests/test_feature_guard.py
import pytest
from unittest.mock import patch, MagicMock
from kubeopt.infrastructure.services.feature_guard import get_ui_feature_flags
from kubeopt.infrastructure.services.license_validator import LicenseTier


def _mock_validator(tier):
    v = MagicMock()
    v.get_tier.return_value = tier
    v.get_plan_generation_status.return_value = {"available": True, "remaining": 10}
    return v


def test_pro_tier_shows_ai_plans():
    with patch("kubeopt.infrastructure.services.feature_guard.get_license_validator",
               return_value=_mock_validator(LicenseTier.PRO)):
        flags = get_ui_feature_flags()
    assert flags["show_ai_plans"] is True


def test_none_tier_hides_ai_plans():
    with patch("kubeopt.infrastructure.services.feature_guard.get_license_validator",
               return_value=_mock_validator(LicenseTier.NONE)):
        flags = get_ui_feature_flags()
    assert flags["show_ai_plans"] is False


def test_enterprise_tier_shows_ai_plans():
    with patch("kubeopt.infrastructure.services.feature_guard.get_license_validator",
               return_value=_mock_validator(LicenseTier.ENTERPRISE)):
        flags = get_ui_feature_flags()
    assert flags["show_ai_plans"] is True


def test_none_tier_shows_deterministic_recommendations():
    with patch("kubeopt.infrastructure.services.feature_guard.get_license_validator",
               return_value=_mock_validator(LicenseTier.NONE)):
        flags = get_ui_feature_flags()
    assert flags["show_recommendations"] is True

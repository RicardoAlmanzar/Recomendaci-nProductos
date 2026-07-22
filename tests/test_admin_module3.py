"""Tests del módulo administrativo — reglas y estado del sistema."""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.regla import Regla
from app.services.admin import (
    create_rule,
    get_rule,
    get_system_status,
    list_rules,
    serialize_rule,
    update_rule,
)


class TestSerializeRule(unittest.TestCase):
    def test_serializes_all_fields(self):
        rule = Regla(
            rule_id=1,
            source_category="packaging",
            target_category="labels",
            weight=0.9,
            reason_code="CROSS_SELL_RULE",
            active=True,
        )
        result = serialize_rule(rule)
        self.assertEqual(result["rule_id"], 1)
        self.assertEqual(result["source_category"], "packaging")
        self.assertTrue(result["active"])


class TestCreateRule(unittest.TestCase):
    def test_create_rule_success(self):
        session = MagicMock()
        created = Regla(
            rule_id=10,
            source_category="cleaning",
            target_category="protective",
            weight=0.65,
            reason_code="CROSS_SELL_RULE",
            active=True,
        )

        def refresh_side_effect(rule):
            rule.rule_id = 10

        session.refresh.side_effect = refresh_side_effect

        with patch("app.services.admin.Regla", return_value=created):
            result = create_rule(
                session,
                {
                    "source_category": "cleaning",
                    "target_category": "protective",
                    "weight": 0.65,
                    "reason_code": "CROSS_SELL_RULE",
                },
            )

        self.assertEqual(result["rule_id"], 10)
        session.add.assert_called_once()
        session.commit.assert_called_once()

    def test_create_rule_missing_fields(self):
        session = MagicMock()
        with self.assertRaises(ValueError) as ctx:
            create_rule(session, {"source_category": "packaging"})
        self.assertIn("target_category", str(ctx.exception))


class TestUpdateRule(unittest.TestCase):
    def test_update_rule_partial(self):
        session = MagicMock()
        existing = Regla(
            rule_id=3,
            source_category="paper",
            target_category="labels",
            weight=0.82,
            reason_code="CROSS_SELL_RULE",
            active=True,
        )
        session.get.return_value = existing

        updated = update_rule(session, 3, {"active": False, "weight": 0.5})

        self.assertFalse(updated.active)
        self.assertEqual(updated.weight, 0.5)
        session.commit.assert_called_once()

    def test_update_rule_not_found(self):
        session = MagicMock()
        session.get.return_value = None
        self.assertIsNone(update_rule(session, 999, {"active": False}))


class TestListRules(unittest.TestCase):
    def test_list_rules_returns_serialized_items(self):
        session = MagicMock()
        session.exec.return_value.all.return_value = [
            Regla(
                rule_id=1,
                source_category="packaging",
                target_category="labels",
                weight=0.9,
                reason_code="CROSS_SELL_RULE",
                active=True,
            )
        ]
        result = list_rules(session)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["rule_id"], 1)


class TestGetRule(unittest.TestCase):
    def test_get_rule_returns_model(self):
        session = MagicMock()
        rule = Regla(
            rule_id=2,
            source_category="food_service",
            target_category="packaging",
            weight=0.85,
            reason_code="CROSS_SELL_RULE",
            active=True,
        )
        session.get.return_value = rule
        self.assertEqual(get_rule(session, 2), rule)


class TestSystemStatus(unittest.TestCase):
    def test_system_status_ok(self):
        session = MagicMock()
        session.exec.side_effect = [
            MagicMock(one=lambda: 1),
            MagicMock(one=lambda: 7),
            MagicMock(one=lambda: 5),
            MagicMock(one=lambda: 15),
            MagicMock(one=lambda: 14),
            MagicMock(one=lambda: 3),
            MagicMock(one=lambda: 120),
        ]

        result = get_system_status(session)

        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["database"]["connected"])
        self.assertEqual(result["counts"]["rules_total"], 7)
        self.assertEqual(result["counts"]["rules_active"], 5)
        self.assertIn("cache", result)
        self.assertIn("service", result)

    def test_system_status_degraded_when_db_fails(self):
        session = MagicMock()
        session.exec.side_effect = [
            Exception("db down"),
            MagicMock(one=lambda: 0),
            MagicMock(one=lambda: 0),
            MagicMock(one=lambda: 0),
            MagicMock(one=lambda: 0),
            MagicMock(one=lambda: 0),
            MagicMock(one=lambda: 0),
        ]

        result = get_system_status(session)

        self.assertEqual(result["status"], "degraded")
        self.assertFalse(result["database"]["connected"])
        self.assertIn("db down", result["database"]["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

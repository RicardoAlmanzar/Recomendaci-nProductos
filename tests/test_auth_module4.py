"""Tests de autenticación JWT y RBAC — Módulo 4."""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.usuario import AdminUser, UserRole
from app.services.auth import (
    ROLE_RANK,
    create_access_token,
    decode_access_token,
    ensure_default_admin,
    login_with_email,
)


class TestAuthService(unittest.TestCase):
    def test_create_and_decode_token(self):
        user = AdminUser(email="admin@gjs.local", role=UserRole.super_admin, active=True)
        token = create_access_token(user)
        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], "admin@gjs.local")
        self.assertEqual(payload["role"], "super_admin")

    def test_login_with_valid_email(self):
        session = MagicMock()
        user = AdminUser(email="admin@gjs.local", role=UserRole.super_admin, active=True)
        session.exec.return_value.first.return_value = user

        result = login_with_email(session, "admin@gjs.local")

        self.assertIn("access_token", result)
        self.assertEqual(result["token_type"], "bearer")
        self.assertEqual(result["user"]["role"], "super_admin")

    def test_login_with_unknown_email(self):
        session = MagicMock()
        session.exec.return_value.first.return_value = None
        with self.assertRaises(ValueError):
            login_with_email(session, "missing@gjs.local")

    def test_ensure_default_admin_creates_user(self):
        session = MagicMock()
        session.exec.return_value.first.return_value = None

        ensure_default_admin(session)

        session.add.assert_called_once()
        session.commit.assert_called_once()

    def test_role_rank_order(self):
        self.assertGreater(ROLE_RANK[UserRole.admin], ROLE_RANK[UserRole.viewer])
        self.assertGreater(ROLE_RANK[UserRole.super_admin], ROLE_RANK[UserRole.admin])


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Tests de campañas y ofertas — Módulo 4."""
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.campana import Campana
from app.models.oferta import Oferta
from app.services.campaigns import create_campaign, create_offer, get_active_offer_scores


class TestCampaignsService(unittest.TestCase):
    def test_create_campaign(self):
        session = MagicMock()
        created = Campana(campaign_id=1, name="Q3 Promo", channel="whatsapp", active=True)

        def refresh_side_effect(campaign):
            campaign.campaign_id = 1

        session.refresh.side_effect = refresh_side_effect

        with unittest.mock.patch("app.services.campaigns.Campana", return_value=created):
            result = create_campaign(
                session,
                {"name": "Q3 Promo", "channel": "whatsapp"},
            )

        self.assertEqual(result["campaign_id"], 1)
        session.commit.assert_called_once()

    def test_create_offer_requires_campaign(self):
        session = MagicMock()
        session.get.return_value = None
        with self.assertRaises(ValueError):
            create_offer(
                session,
                {"campaign_id": 99, "product_id": "P-001", "extra_score": 0.2},
            )

    def test_get_active_offer_scores_filters_by_channel(self):
        session = MagicMock()
        now = datetime.utcnow()
        campaigns = [
            Campana(
                campaign_id=1,
                name="WA Promo",
                channel="whatsapp",
                active=True,
                starts_at=now - timedelta(days=1),
                ends_at=now + timedelta(days=1),
            ),
            Campana(
                campaign_id=2,
                name="Market Promo",
                channel="marketplace",
                active=True,
            ),
        ]
        offers = [
            Oferta(offer_id=1, campaign_id=1, product_id="P-001", extra_score=0.3, active=True),
            Oferta(offer_id=2, campaign_id=2, product_id="P-002", extra_score=0.5, active=True),
        ]
        session.exec.side_effect = [
            MagicMock(all=lambda: campaigns),
            MagicMock(all=lambda: [offers[0]]),
        ]

        scores = get_active_offer_scores(session, channel="whatsapp", now=now)

        self.assertEqual(scores, {"P-001": 0.3})


if __name__ == "__main__":
    unittest.main(verbosity=2)

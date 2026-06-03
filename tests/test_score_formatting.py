import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.engine.formatting import SCORE_DECIMALS, round_score
from app.engine.ranker import RankingContext, rank


class MockProducto:
    def __init__(self, product_id, margin_pct=0.333333, strategic_priority=0.777777):
        self.product_id = product_id
        self.sku = f"SKU-{product_id}"
        self.name = f"Producto {product_id}"
        self.category = "packaging"
        self.active = True
        self.margin_pct = margin_pct
        self.strategic_priority = strategic_priority


class MockCliente:
    customer_id = "CUST-FORMAT"
    business_type = "retail"
    city = "Santo Domingo"


class TestScoreFormatting(unittest.TestCase):
    def test_round_score_uses_project_standard(self):
        self.assertEqual(SCORE_DECIMALS, 4)
        self.assertEqual(round_score(0.123456), 0.1235)
        self.assertEqual(round_score(None), 0.0)

    def test_rank_output_scores_are_rounded(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[],
            affinity_rules=[],
            limit=1,
        )

        result = rank(candidates=[MockProducto("P-001")], context=ctx)

        self.assertEqual(result[0]["score"], round_score(result[0]["score"]))
        self.assertEqual(
            result[0]["explanation"]["final_score"],
            round_score(result[0]["explanation"]["final_score"]),
        )

    def test_formula_displays_four_decimals(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[],
            affinity_rules=[],
            limit=1,
        )

        result = rank(candidates=[MockProducto("P-001")], context=ctx)
        formula = result[0]["explanation"]["formula"]

        for token in formula.replace("=", "+").split("+"):
            value = token.strip()
            if value:
                self.assertRegex(value, r"^-?\d+\.\d{4}$")


if __name__ == "__main__":
    unittest.main(verbosity=2)

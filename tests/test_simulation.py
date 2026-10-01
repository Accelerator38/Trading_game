import unittest

from simulation import Agent, Order, match_orders, simulate


class SimulationTests(unittest.TestCase):
    def test_reproducible_and_nonnegative(self):
        first = simulate(steps=25, agent_count=15, seed=7)
        self.assertEqual(first, simulate(steps=25, agent_count=15, seed=7))
        self.assertEqual(len(first), 25)
        self.assertTrue(all(row["price_usd"] > 0 for row in first))
        self.assertTrue(all(row["exchange_fees_usd"] >= 0 for row in first))

    def test_trade_conserves_cash_including_fees(self):
        buyer = Agent(0, 2, usd=100.0, btc=0.0)
        seller = Agent(1, 1, usd=0.0, btc=1.0)
        prices, fees = match_orders(
            [Order(buyer, "buy", 100.0, 1.0)],
            [Order(seller, "sell", 100.0, 1.0)],
            fee_rate=0.01,
        )
        self.assertEqual(prices, [100.0])
        self.assertGreaterEqual(buyer.usd, -1e-10)
        self.assertAlmostEqual(buyer.btc + seller.btc, 1.0)
        self.assertAlmostEqual(buyer.usd + seller.usd + fees, 100.0)

    def test_rejects_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            simulate(steps=0)


if __name__ == "__main__":
    unittest.main()

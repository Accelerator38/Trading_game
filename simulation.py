"""Reproducible toy BTC/USD limit-order simulation.

The model is educational: external orders are an explicit source/sink of assets.
It does not simulate a real exchange or predict trading returns.
"""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Agent:
    number: int
    strategy: int
    usd: float = 5_000.0
    btc: float = 10.0

    @property
    def name(self) -> str:
        return f"agent_{self.number}_{self.strategy}"


@dataclass
class Order:
    agent: Agent | None
    side: str
    price: float
    quantity: float


def choose_side(strategy: int, price: float, history: list[float], rng: random.Random) -> str | None:
    """Return a deliberately simple strategy decision."""
    if strategy == 0:
        return rng.choice([None, None, "buy"])
    if strategy == 1:
        return "sell"
    if strategy == 2:
        return "buy"
    if strategy == 3:
        return rng.choice(["buy", "sell"])
    if strategy in (4, 7):
        return "buy" if rng.random() < 0.7 else None
    if strategy == 5:
        return "sell" if rng.random() < 0.5 else None
    if strategy == 6:
        return "sell" if rng.random() < 0.1 else None
    if strategy == 8:
        return rng.choice(["buy", "sell"])
    if strategy == 9:
        return rng.choice(["buy", "sell"]) if rng.random() < 0.05 else None
    if strategy == 10 and len(history) >= 20:
        mean = sum(history[-20:]) / 20
        return "buy" if price > mean * 1.002 else "sell" if price < mean * 0.998 else None
    if strategy == 11 and len(history) >= 3:
        return "buy" if history[-1] > history[-2] > history[-3] else "sell" if history[-1] < history[-2] < history[-3] else None
    if strategy == 12 and len(history) >= 10:
        mean = sum(history[-10:]) / 10
        return "buy" if price < mean * 0.985 else "sell" if price > mean * 1.015 else None
    if strategy == 13 and len(history) >= 5:
        return "sell" if price > history[-5] * 1.01 else None
    if strategy == 14 and len(history) >= 10:
        return "buy" if price > history[-10] * 1.015 else None
    return None


def make_order(agent: Agent, price: float, history: list[float], rng: random.Random) -> Order | None:
    side = choose_side(agent.strategy, price, history, rng)
    if side is None:
        return None
    limit = price * (1 + rng.uniform(-0.003, 0.003))
    quantity = rng.uniform(0.1, 1.5)
    quantity = min(quantity, agent.usd / limit if side == "buy" else agent.btc)
    return Order(agent, side, limit, quantity) if quantity > 0 else None


def match_orders(buys: list[Order], sells: list[Order], fee_rate: float) -> tuple[list[float], float]:
    """Match price-time orders and return trade prices and fees collected."""
    if not 0 <= fee_rate < 1:
        raise ValueError("fee_rate must be in [0, 1)")
    buys.sort(key=lambda order: -order.price)
    sells.sort(key=lambda order: order.price)
    prices: list[float] = []
    fees = 0.0
    i = j = 0
    while i < len(buys) and j < len(sells):
        buy, sell = buys[i], sells[j]
        if buy.price < sell.price:
            break
        deal_price = (buy.price + sell.price) / 2
        quantity = min(buy.quantity, sell.quantity)
        if buy.agent is not None:
            quantity = min(quantity, buy.agent.usd / (deal_price * (1 + fee_rate)))
        if sell.agent is not None:
            quantity = min(quantity, sell.agent.btc)
        if quantity <= 1e-12:
            if buy.agent is not None and buy.agent.usd <= 1e-9:
                i += 1
            elif sell.agent is not None and sell.agent.btc <= 1e-12:
                j += 1
            else:
                # The residual amount is too small to trade safely.
                break
            continue
        cost = deal_price * quantity
        fee = cost * fee_rate
        if buy.agent is not None:
            buy.agent.usd -= cost + fee
            buy.agent.btc += quantity
            fees += fee
        if sell.agent is not None:
            sell.agent.usd += cost - fee
            sell.agent.btc -= quantity
            fees += fee
        buy.quantity -= quantity
        sell.quantity -= quantity
        prices.append(deal_price)
        if buy.quantity <= 1e-12:
            i += 1
        if sell.quantity <= 1e-12:
            j += 1
    return prices, fees


def simulate(steps: int = 500, agent_count: int = 100, seed: int = 42, fee_rate: float = 0.0005) -> list[dict[str, float | int]]:
    if steps <= 0 or agent_count <= 0:
        raise ValueError("steps and agent_count must be positive")
    rng = random.Random(seed)
    agents = [Agent(i, i % 15) for i in range(agent_count)]
    history: list[float] = []
    results: list[dict[str, float | int]] = []
    price = 30_000.0
    exchange_fees = 0.0
    for step in range(steps):
        # Decisions see completed earlier steps only.
        buys: list[Order] = []
        sells: list[Order] = []
        for agent in agents:
            order = make_order(agent, price, history, rng)
            if order is not None:
                (buys if order.side == "buy" else sells).append(order)
        if step % 10 == 0:
            buys.append(Order(None, "buy", price * rng.uniform(1.001, 1.005), rng.uniform(3, 8)))
        if step % 10 == 5:
            sells.append(Order(None, "sell", price * rng.uniform(0.995, 0.999), rng.uniform(2, 5)))
        trade_prices, fees = match_orders(buys, sells, fee_rate)
        exchange_fees += fees
        history.append(price)
        price = (sum(trade_prices) / len(trade_prices) if trade_prices else price) * rng.uniform(1.0, 1.0004)
        row: dict[str, float | int] = {"step": step, "price_usd": price, "exchange_fees_usd": exchange_fees, "trades": len(trade_prices)}
        row.update({agent.name: agent.usd + agent.btc * price for agent in agents})
        results.append(row)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--agents", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("results.csv"))
    args = parser.parse_args()
    rows = simulate(args.steps, args.agents, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} steps to {args.output}")


if __name__ == "__main__":
    main()

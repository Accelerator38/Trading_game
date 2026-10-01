import random
import pandas as pd
import matplotlib.pyplot as plt

# Параметры симуляции
NUM_AGENTS = 100
NUM_STRATEGIES = 15
NUM_STEPS = 5000
FEE_RATE = 0.0005
INITIAL_PRICE = 30000

price_history = []

# Класс агента
class Agent:
    def __init__(self, agent_number, strategy_id):
        self.id = f"{agent_number}_{strategy_id}"
        self.strategy_id = strategy_id
        self.usd_balance = 5000.0
        self.btc_balance = 10.0

    def decide_order(self, current_price, step):
        action = None
        price = None
        quantity = None

        # Простые стратегии
        if self.strategy_id == 0:
            if random.random() < 0.7:
                return []
        elif self.strategy_id == 1:
            action = 'sell'
        elif self.strategy_id == 2:
            action = 'buy'
        elif self.strategy_id == 3:
            action = random.choice(['buy', 'sell'])
        elif self.strategy_id == 4:
            if random.random() < 0.7:
                action = 'buy'
            else:
                return []
        elif self.strategy_id == 5:
            if random.random() < 0.5:
                action = 'sell'
            else:
                return []
        elif self.strategy_id == 6:
            if random.random() < 0.9:
                return []
            action = 'sell'
        elif self.strategy_id == 7:
            if random.random() < 0.7:
                action = 'buy'
            else:
                return []
        elif self.strategy_id == 8:
            action = random.choice(['buy', 'sell'])
        elif self.strategy_id == 9:
            if random.random() < 0.95:
                return []
            action = random.choice(['buy', 'sell'])
        elif self.strategy_id == 10:
            if step >= 20:
                sma = sum(price_history[-20:]) / 20
                if current_price > sma * 1.002:
                    action = 'buy'
                elif current_price < sma * 0.998:
                    action = 'sell'
                else:
                    return []
            else:
                return []
        elif self.strategy_id == 11:
            if step >= 3:
                if price_history[-1] > price_history[-2] > price_history[-3]:
                    action = 'buy'
                elif price_history[-1] < price_history[-2] < price_history[-3]:
                    action = 'sell'
                else:
                    return []
            else:
                return []
        elif self.strategy_id == 12:
            if step >= 10:
                sma = sum(price_history[-10:]) / 10
                if current_price < sma * 0.985:
                    action = 'buy'
                elif current_price > sma * 1.015:
                    action = 'sell'
                else:
                    return []
            else:
                return []
        elif self.strategy_id == 13:
            if step >= 5:
                if current_price > price_history[-5] * 1.01:
                    action = 'sell'
                else:
                    return []
            else:
                return []
        elif self.strategy_id == 14:
            if step >= 10:
                if current_price > price_history[-10] * 1.015:
                    action = 'buy'
                else:
                    return []
            else:
                return []

        price_shift = random.uniform(-0.003, 0.003) * current_price
        price = current_price + price_shift
        quantity = random.uniform(0.1, 1.5)

        if action == 'buy':
            max_affordable = self.usd_balance / price
            quantity = min(quantity, max_affordable)
            if quantity <= 0:
                return []
        elif action == 'sell':
            quantity = min(quantity, self.btc_balance)
            if quantity <= 0:
                return []

        return [{'agent': self, 'type': action, 'price': price, 'quantity': quantity}]

agents = [Agent(i, i % NUM_STRATEGIES) for i in range(NUM_AGENTS)]
exchange_balance = 0.0
results = []
avg_prices = []
current_price = INITIAL_PRICE

# Основной цикл
for step in range(NUM_STEPS):
    price_history.append(current_price)
    buy_orders = []
    sell_orders = []
    matched_prices = []

    for agent in agents:
        orders = agent.decide_order(current_price, step)
        for order in orders:
            if order['type'] == 'buy':
                buy_orders.append(order)
            elif order['type'] == 'sell':
                sell_orders.append(order)

    # Внешний спрос и предложение
    if step % 10 == 0:
        buy_orders.append({
            'agent': None,
            'type': 'buy',
            'price': current_price * random.uniform(1.001, 1.005),
            'quantity': random.uniform(3, 8)
        })

    if step % 10 == 5:
        sell_orders.append({
            'agent': None,
            'type': 'sell',
            'price': current_price * random.uniform(0.995, 0.999),
            'quantity': random.uniform(2, 5)
        })

    buy_orders.sort(key=lambda x: -x['price'])
    sell_orders.sort(key=lambda x: x['price'])

    i, j = 0, 0
    while i < len(buy_orders) and j < len(sell_orders):
        buy = buy_orders[i]
        sell = sell_orders[j]

        if buy['price'] >= sell['price']:
            deal_price = (buy['price'] + sell['price']) / 2
            deal_quantity = min(buy['quantity'], sell['quantity'])
            total_cost = deal_price * deal_quantity

            if buy['agent'] and buy['agent'].usd_balance < total_cost:
                i += 1
                continue
            if sell['agent'] and sell['agent'].btc_balance < deal_quantity:
                j += 1
                continue

            fee = total_cost * FEE_RATE
            exchange_balance += fee * 2

            if buy['agent']:
                buy['agent'].usd_balance -= total_cost + fee
                buy['agent'].btc_balance += deal_quantity

            if sell['agent']:
                sell['agent'].usd_balance += total_cost - fee
                sell['agent'].btc_balance -= deal_quantity

            matched_prices.append(deal_price)

            buy['quantity'] -= deal_quantity
            sell['quantity'] -= deal_quantity

            if buy['quantity'] <= 0:
                i += 1
            if sell['quantity'] <= 0:
                j += 1
        else:
            break

    if matched_prices:
        market_price = sum(matched_prices) / len(matched_prices)
    else:
        market_price = current_price

    drift = random.uniform(1.0000, 1.0004)
    current_price = market_price * drift

    avg_prices.append(current_price)

    row = {
        'step': step,
        'exchange_balance': exchange_balance,
        'avg_price': current_price
    }
    for agent in agents:
        total_asset = agent.usd_balance + agent.btc_balance * current_price
        row[f'agent_{agent.id}'] = total_asset
    results.append(row)

# Сохранение
df = pd.DataFrame(results)
df.to_excel('trading_simulation_results.xlsx', index=False)

# График цены
plt.figure(figsize=(12, 5))
plt.plot(avg_prices, label='Средняя цена сделки')
plt.title('Динамика цены BTC')
plt.xlabel('Шаг')
plt.ylabel('Цена BTC')
plt.grid(True)
plt.legend()
plt.show()

# Топ-5 агентов
last_assets = {f'agent_{agent.id}': df[f'agent_{agent.id}'].iloc[-1] for agent in agents}
top5_agents = sorted(last_assets.items(), key=lambda x: -x[1])[:5]

plt.figure(figsize=(12, 6))
for name, _ in top5_agents:
    plt.plot(df['step'], df[name], label=name)
plt.title('Изменение активов топ-5 агентов')
plt.xlabel('Шаг')
plt.ylabel('Активы в USD эквиваленте')
plt.grid(True)
plt.legend()
plt.show()

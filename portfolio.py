from typing import Dict

class Portfolio:
    def __init__(self, initial_balance: float):
        self.balance = initial_balance
        self.holdings: Dict[str, float] = {}  # symbol: quantity

    def buy(self, symbol: str, price: float, quantity: float):
        cost = price * quantity
        if cost > self.balance:
            return
        self.balance -= cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity

    def sell(self, symbol: str, price: float, quantity: float):
        if symbol not in self.holdings or quantity > self.holdings[symbol]:
            return
        revenue = price * quantity
        self.balance += revenue
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]

    def get_value(self, current_price: float) -> float:
        holdings_value = sum(quantity * current_price for quantity in self.holdings.values())
        return self.balance + holdings_value
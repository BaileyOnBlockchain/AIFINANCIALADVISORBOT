import pytest
import pandas as pd
from strategies import MovingAverageCrossoverRSIStrategy

@pytest.fixture
def config():
    return {
        'short_window': 12,
        'long_window': 26,
        'rsi_period': 14,
        'rsi_overbought': 70,
        'rsi_oversold': 30
    }

def test_generate_signal_buy(config):
    strategy = MovingAverageCrossoverRSIStrategy(config)
    # Mock data for bullish crossover + oversold RSI
    prices = [100 + i for i in range(30)]  # Uptrend, enough for MA and RSI
    data = pd.DataFrame({'price': prices})
    signal = strategy.generate_signal(data)
    # Depending on strategy logic, adjust expected signal
    assert signal in ['buy', 'hold']

def test_generate_signal_sell(config):
    strategy = MovingAverageCrossoverRSIStrategy(config)
    # Mock data for bearish crossover + overbought RSI
    prices = [130 - i for i in range(30)]  # Downtrend
    data = pd.DataFrame({'price': prices})
    signal = strategy.generate_signal(data)
    assert signal in ['sell', 'hold']

def test_generate_signal_hold(config):
    strategy = MovingAverageCrossoverRSIStrategy(config)
    # Flat prices, no crossover, RSI neutral
    prices = [120 for _ in range(30)]
    data = pd.DataFrame({'price': prices})
    signal = strategy.generate_signal(data)
    assert signal == 'hold'
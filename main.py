import logging
import sys
import yaml # type: ignore
from datetime import datetime
import pandas as pd
import requests
import time
from strategies import MovingAverageCrossoverRSIStrategy
from portfolio import Portfolio

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Setup logging
logging.basicConfig(filename=config['logging']['file'], level=config['logging']['level'],
                    format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_historical_data(symbol: str, start_date: str, end_date: str, vs_currency: str) -> pd.DataFrame:
    """Fetch historical price data from CoinGecko."""
    url = f"{config['api']['base_url']}/coins/{symbol}/market_chart/range"
    params = {
        'vs_currency': vs_currency,
        'from': int(datetime.strptime(start_date, '%Y-%m-%d').timestamp()),
        'to': int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        logging.error(f"API error: {response.text}")
        sys.exit(1)
    data = response.json()['prices']
    df = pd.DataFrame(data, columns=['timestamp', 'price'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def fetch_live_data(symbol: str, vs_currency: str) -> float:
    """Fetch current price."""
    url = f"{config['api']['base_url']}/simple/price"
    params = {'ids': symbol, 'vs_currencies': vs_currency}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        logging.error(f"API error: {response.text}")
        return 0.0
    return response.json()[symbol][vs_currency]

def run_backtest(symbol: str, start_date: str, end_date: str):
    df = fetch_historical_data(symbol, start_date, end_date, config['api']['vs_currency'])
    strategy = MovingAverageCrossoverRSIStrategy(config['strategy'])
    portfolio = Portfolio(config['portfolio']['initial_balance'])
    
    for i in range(max(config['strategy']['long_window'], config['strategy']['rsi_period']), len(df)):
        current_data = df.iloc[:i]
        signal = strategy.generate_signal(current_data)
        price = df.iloc[i]['price']
        if signal == 'buy':
            portfolio.buy(symbol, price, config['portfolio']['trade_size'] * portfolio.balance / price)
        elif signal == 'sell' and portfolio.holdings.get(symbol, 0) > 0:
            portfolio.sell(symbol, price, portfolio.holdings[symbol])
    
    logging.info(f"Backtest complete. Final portfolio value: {portfolio.get_value(df.iloc[-1]['price'])}")

def run_live(symbol: str):
    strategy = MovingAverageCrossoverRSIStrategy(config['strategy'])
    portfolio = Portfolio(config['portfolio']['initial_balance'])
    historical_data = fetch_historical_data(symbol, '2024-01-01', datetime.now().strftime('%Y-%m-%d'), config['api']['vs_currency'])
    
    while True:  # In production, use a scheduler like APScheduler
        price = fetch_live_data(symbol, config['api']['vs_currency'])
        if price == 0.0:
            time.sleep(10)
            continue
        new_row = pd.DataFrame({'price': [price]}, index=[datetime.now()])
        historical_data = pd.concat([historical_data, new_row])
        signal = strategy.generate_signal(historical_data)
        if signal == 'buy':
            portfolio.buy(symbol, price, config['portfolio']['trade_size'] * portfolio.balance / price)
        elif signal == 'sell' and portfolio.holdings.get(symbol, 0) > 0:
            portfolio.sell(symbol, price, portfolio.holdings[symbol])
        logging.info(f"Current price: {price} | Portfolio value: {portfolio.get_value(price)}")
        time.sleep(60)  # Sleep for 1 minute between live checks

if __name__ == "__main__":
    # Improved argument parsing
    mode = None
    if '--mode' in sys.argv:
        mode_idx = sys.argv.index('--mode') + 1
        if mode_idx < len(sys.argv):
            mode = sys.argv[mode_idx]
    symbol = config['api']['symbols'][0]

    if mode == 'backtest':
        start_date = sys.argv[sys.argv.index('--start_date') + 1] if '--start_date' in sys.argv else '2024-01-01'
        end_date = sys.argv[sys.argv.index('--end_date') + 1] if '--end_date' in sys.argv else datetime.now().strftime('%Y-%m-%d')
        run_backtest(symbol, start_date, end_date)
    else:
        run_live(symbol)
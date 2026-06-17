import os
from datetime import datetime, timedelta
import pandas as pd

def fetch_realtime_data(ticker: str) -> dict:
    """Fetch real-time VN stock data directly using vnstock 4.x"""
    from vnstock.api.quote import Quote
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    # Fetch 30 days of data to have enough history for the recent 5 days
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    q = Quote(symbol=ticker, source='VCI')
    df = q.history(start=start_date, end=end_date)
    
    # Rename columns to standard names
    df.rename(columns={
        'time': 'Date', 
        'open': 'Open', 
        'high': 'High',
        'low': 'Low', 
        'close': 'Close', 
        'volume': 'Volume'
    }, inplace=True)
    
    if 'Date' in df.columns:
        df.set_index('Date', inplace=True)
        
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    
    current_price = float(df.iloc[-1]['Close'])
    recent_5 = df.tail(5)
    recent_15 = df.tail(15)
    
    return {
        "ticker": ticker,
        "current_price": current_price,
        "price_date": df.index[-1].strftime('%Y-%m-%d'),
        "recent_5_days": [
            {
                "date": str(d.date()), 
                "open": float(r['Open']), 
                "high": float(r['High']),
                "low": float(r['Low']), 
                "close": float(r['Close']), 
                "volume": int(r['Volume'])
            }
            for d, r in recent_5.iterrows()
        ],
        "recent_15_days": [
            {
                "date": str(d.date()), 
                "open": float(r['Open']), 
                "high": float(r['High']),
                "low": float(r['Low']), 
                "close": float(r['Close']), 
                "volume": int(r['Volume'])
            }
            for d, r in recent_15.iterrows()
        ]
    }

if __name__ == "__main__":
    # Test data fetching
    ticker = "FPT"
    print(f"Testing real-time data fetch for {ticker}...")
    try:
        data = fetch_realtime_data(ticker)
        print("Data fetched successfully:")
        print(f"Ticker: {data['ticker']}")
        print(f"Current Price: {data['current_price']}k VND")
        print(f"Date: {data['price_date']}")
        print(f"Recent 5 days history:")
        for day in data['recent_5_days']:
            print(f"  {day['date']}: Close={day['close']}, Volume={day['volume']}")
    except Exception as e:
        print(f"Error fetching data: {e}")

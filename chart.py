import os
from datetime import datetime, timedelta
import matplotlib
# Use 'Agg' backend to generate images without requiring a GUI server (essential for background tasks)
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

def generate_stock_chart(ticker: str) -> str:
    """
    Fetch 30 days of historical data for ticker, plot a premium TradingView-style dark chart,
    and save it as an image. Returns the file path of the saved chart.
    """
    from vnstock.api.quote import Quote

    # Fetch 30 days of historical data
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    q = Quote(symbol=ticker, source='VCI')
    df = q.history(start=start_date, end=end_date)
    
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
    
    # Check if we have enough data
    if df.empty:
        raise ValueError(f"No historical data found for {ticker}")

    # Set up matplotlib style (TradingView dark theme style)
    plt.style.use('dark_background')
    
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    fig.patch.set_facecolor('#131722')
    ax.set_facecolor('#131722')
    
    # Plot the Close price line
    # TradingView style blue line
    line_color = '#2962FF' 
    ax.plot(df.index, df['Close'], color=line_color, linewidth=2.5, label=f"{ticker} Close")
    
    # Gradient area fill under the line
    ax.fill_between(df.index, df['Close'], df['Close'].min() * 0.99, 
                    color=line_color, alpha=0.15)
    
    # Set labels and title
    current_price = df['Close'].iloc[-1]
    change = current_price - df['Close'].iloc[0]
    pct_change = (change / df['Close'].iloc[0]) * 100
    change_sign = "+" if change >= 0 else ""
    change_color = "#089981" if change >= 0 else "#F23645"  # Green / Red
    
    title_text = f"{ticker} Technical Chart"
    subtitle_text = f"Price: {current_price:.1f}k VND ({change_sign}{pct_change:.2f}%)"
    
    # Adding text directly in chart for a clean modern dashboard look
    ax.text(0.02, 0.92, title_text, transform=ax.transAxes, fontsize=14, fontweight='bold', color='#FFFFFF')
    ax.text(0.02, 0.84, subtitle_text, transform=ax.transAxes, fontsize=11, fontweight='medium', color=change_color)
    
    # Grid lines
    ax.grid(True, linestyle='--', alpha=0.2, color='#2a2e39')
    
    # Formatting axes
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.xticks(rotation=0)
    
    # Format Y axis labels to add 'k'
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}k".format(int(x))))
    
    # Hide top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#2a2e39')
    ax.spines['bottom'].set_color('#2a2e39')
    ax.tick_params(colors='#848e9c')
    
    plt.tight_layout()
    
    # Save the chart as a local image file
    chart_filename = f"chart_{ticker.lower()}.png"
    chart_path = os.path.join(os.getcwd(), chart_filename)
    
    plt.savefig(chart_path, facecolor='#131722', edgecolor='none', bbox_inches='tight')
    plt.close(fig)  # Clear plt memory
    
    return chart_path

if __name__ == "__main__":
    # Test chart generation
    ticker = "HPG"
    print(f"Generating test chart for {ticker}...")
    try:
        path = generate_stock_chart(ticker)
        print(f"Chart saved successfully at: {path}")
    except Exception as e:
        print(f"Error generating chart: {e}")

import os
from datetime import datetime
import pytz
import requests
import lancedb
from dotenv import load_dotenv
from crewai import Crew, Process, Task, Agent, LLM

# Load environment variables
load_dotenv()

from data import fetch_realtime_data
from telegram_utils import send_telegram_report, send_telegram_photo
from chart import generate_stock_chart

def get_embedding(text: str) -> list:
    """Get text embeddings from local Ollama nomic-embed-text model"""
    ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip('/')
    url = f"{ollama_base_url}/api/embed"
    payload = {
        "model": "nomic-embed-text",
        "input": text
    }
    import time
    for attempt in range(3):
        try:
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code == 200:
                embeddings = resp.json().get("embeddings", [])
                if embeddings:
                    return embeddings[0]
        except Exception as e:
            print(f"Attempt {attempt+1} failed to get local Ollama embedding: {e}")
            if attempt < 2:
                time.sleep(2)
    # Fallback to zero vector if failed
    return [0.0] * 768

def save_to_vectordb(ticker: str, price: float, date: str, analysis: str, chart_bytes: bytes = None):
    """Save analysis results and embeddings to local LanceDB in vectordb/ folder"""
    try:
        db_dir = os.path.join(os.getcwd(), "vectordb")
        os.makedirs(db_dir, exist_ok=True)
        db = lancedb.connect(db_dir)
        
        # Generate embedding for the analysis text
        embedding = get_embedding(analysis)
        
        data = [{
            "ticker": ticker,
            "price": price,
            "date": date,
            "analysis": analysis,
            "vector": embedding,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "chart_image": chart_bytes if chart_bytes is not None else b""
        }]
        
        table_name = "stock_analysis"
        
        # In newer versions of LanceDB, we want to handle schema differences robustly.
        # Overwrite table if we want to update the schema to include the new field.
        if table_name in db.table_names():
            table = db.open_table(table_name)
            try:
                table.add(data)
            except Exception as schema_error:
                # If there is a schema mismatch (e.g. older table without chart_image), recreate the table
                print(f"Schema mismatch or table error, recreating table: {schema_error}")
                db.create_table(table_name, data=data, mode="overwrite")
        else:
            db.create_table(table_name, data=data)
        print(f"Saved analysis for {ticker} on {date} to LanceDB in 'vectordb/' folder.")
    except Exception as e:
        print(f"Error saving to vector database: {e}")

def run_analysis(ticker: str = "FPT", chat_id: str = None):
    """Run complete analysis and send report with chart to Telegram"""
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    timestamp = datetime.now(vn_tz).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{timestamp}] 🚀 Starting analysis run for {ticker} (chat_id={chat_id})...")
    
    try:
        data = fetch_realtime_data(ticker)
        price = data['current_price']
        price_date = data['price_date']
        recent = data['recent_5_days']
        recent_15 = data['recent_15_days']
        print(f"Data fetched successfully: {ticker} = {price}k VND on {price_date}")
    except Exception as e:
        print(f"Failed to fetch stock data: {e}")
        return

    # Generate the stock chart
    chart_path = None
    try:
        chart_path = generate_stock_chart(ticker)
        print(f"Technical chart generated at: {chart_path}")
    except Exception as e:
        print(f"Failed to generate stock chart: {e}")

    # Format data summary for the AI prompt (using 15 days of context)
    history_lines = []
    for d in recent_15:
        line = f"  {d['date']}: Open={d['open']}, High={d['high']}, Low={d['low']}, Close={d['close']}, Vol={d['volume']:,}"
        history_lines.append(line)
        
    history_text = "\n".join(history_lines)
    data_summary = f"""
STOCK: {ticker}
CURRENT PRICE: {price} nghìn đồng (VND)
DATE: {price_date}
RECENT 15 DAYS OF TRADING HISTORY:
{history_text}
"""

    print("Initializing Ollama local LLM (llama3:latest)...")
    ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip('/')
    llm = LLM(
        model="ollama/llama3:latest", 
        base_url=ollama_base_url,
        temperature=0.7
    )

    # Define Agent
    analyst = Agent(
        role="Chuyên gia phân tích chứng khoán Việt Nam",
        goal=f"Phân tích dữ liệu cổ phiếu {ticker} và đưa ra nhận định rõ ràng, đa chiều hoàn toàn bằng tiếng Việt.",
        backstory="Bạn là một chuyên gia phân tích định lượng cao cấp, am hiểu sâu sắc về thị trường chứng khoán Việt Nam (HOSE/HNX).",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    # Define Task
    analyze_task = Task(
        description=f"""Hãy phân tích dữ liệu thực tế của cổ phiếu {ticker} tính đến ngày {price_date}:

{data_summary}

Yêu cầu báo cáo bao gồm:
1. Chiều xu hướng (tăng/giảm/đi ngang) kèm theo lập luận dựa trên lịch sử giá 15 phiên gần nhất.
2. Các vùng giá quan trọng (vùng hỗ trợ / vùng kháng cự).
3. Triển vọng ngắn hạn (từ 1 đến 5 ngày tới).
4. Khuyến nghị hành động rõ ràng (Mua/Giữ/Bán). Không chọn 'Giữ' trừ khi xu hướng thực sự đi ngang không rõ ràng. Nếu có xu hướng tăng/giảm rõ rệt, hãy đưa ra khuyến nghị 'Mua' hoặc 'Bán'.

Yêu cầu đặc biệt: Viết báo cáo HOÀN TOÀN BẰNG TIẾNG VIỆT. Trình bày ngắn gọn, súc tích (tối đa 200 từ). Đưa các con số và dữ liệu thực tế của {ticker} vào phân tích.""",
        expected_output="Báo cáo phân tích ngắn gọn bằng tiếng Việt gồm xu hướng, mức giá hỗ trợ/kháng cự, triển vọng và khuyến nghị hành động.",
        agent=analyst
    )

    # Kickoff the CrewAI process
    print("Running CrewAI analyst agent...")
    crew = Crew(agents=[analyst], tasks=[analyze_task], process=Process.sequential, verbose=True)
    result = crew.kickoff()
    analysis_text = str(result)

    # Compile the final report message
    history_table = []
    for d in recent:
        vol_k = d['volume'] // 1000
        history_table.append(f"{d['date']}  {d['close']:.1f}k  {vol_k}K")
    
    table_text = "\n".join(history_table)
    
    report = f"""<b>BÁO CÁO CHỨNG KHOÁN - {ticker}</b>
<code>{'━'*30}</code>
<b>Giá hôm nay ({price_date}):</b> {price:,.1f}k VND
<b>Khối lượng:</b> {recent[-1]['volume']:,} cp

<b>Lịch sử 5 phiên:</b>
<pre>Ngày        Đóng cửa   KL
{table_text}</pre>

<b>Phân tích AI:</b>
{analysis_text[:1200]}

<code>{'━'*30}</code>"""

    # Read the chart bytes if generated, so we can save it to the database
    chart_bytes = None
    if chart_path and os.path.exists(chart_path):
        try:
            with open(chart_path, "rb") as f:
                chart_bytes = f.read()
        except Exception as e:
            print(f"Failed to read chart file: {e}")

    # Send report with chart to Telegram if generated
    if chart_path and os.path.exists(chart_path):
        print(f"Sending report with chart to Telegram (chat_id={chat_id})...")
        send_telegram_photo(chart_path, report, chat_id=chat_id)
        try:
            os.remove(chart_path)
            print("🧹 Cleaned up temporary chart file.")
        except Exception as e:
            print(f"Failed to remove temp chart file: {e}")
    else:
        print(f"Sending text-only report to Telegram (chat_id={chat_id})...")
        send_telegram_report(report, ticker, chat_id=chat_id)

    # Save final analysis results to local LanceDB vector database
    save_to_vectordb(ticker, price, price_date, analysis_text, chart_bytes)

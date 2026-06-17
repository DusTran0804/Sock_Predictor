# 📊 Vietnam Stock Prediction & Chatbot System

Hệ thống phân tích, dự đoán chứng khoán Việt Nam tích hợp Chatbot Telegram tự động, sử dụng các mô hình ngôn ngữ lớn (LLM) chạy cục bộ qua Ollama kết hợp với CrewAI và cơ sở dữ liệu Vector LanceDB.

---

## ✨ Tính năng nổi bật

1. **📊 Phân tích cổ phiếu tự động**: Tự động tải dữ liệu lịch sử giao dịch thời gian thực (từ HOSE/HNX) và tạo báo cáo nhận định xu hướng hoàn toàn bằng tiếng Việt sử dụng tác nhân CrewAI.
2. **📈 Biểu đồ kỹ thuật chuyên nghiệp**: Vẽ và xuất biểu đồ kỹ thuật giá cổ phiếu 30 ngày gần nhất theo phong cách tối giản (dark theme) của TradingView.
3. **💬 Chatbot Telegram tương tác (Qwen 2.5)**: Tích hợp bot chat hỗ trợ trả lời câu hỏi và thực hiện phân tích cổ phiếu theo yêu cầu của người dùng thông qua câu lệnh `/analyze <Mã_Cổ_Phiếu>`.
4. **⏰ Lập lịch tự động gửi báo cáo**: Hệ thống lập lịch tự động phân tích và gửi báo cáo kèm biểu đồ đến Telegram của bạn vào lúc **07:00 sáng** hàng ngày (Giờ Việt Nam).
5. **🗄️ Lưu trữ Vector Database (LanceDB)**: Tự động nhúng (embedding) nội dung phân tích bằng mô hình `nomic-embed-text` và lưu trữ lịch sử báo cáo kèm hình ảnh biểu đồ vào cơ sở dữ liệu LanceDB cục bộ để phục vụ truy vấn/RAG sau này.

---

## 🛠️ Yêu cầu hệ thống

* **Python**: Phiên bản 3.9 trở lên.
* **Ollama**: Đã cài đặt và đang chạy trên cổng mặc định (`http://localhost:11434`).
  * Các mô hình LLM cần tải sẵn:
    ```bash
    ollama pull llama3:latest
    ollama pull qwen2.5:3b
    ollama pull nomic-embed-text
    ```
* **Tài khoản Telegram**: Tạo một Bot Telegram qua BotFather để lấy `TELEGRAM_BOT_TOKEN`.

---

## ⚙️ Cấu hình file `.env`

Tạo file `.env` ở thư mục gốc của dự án (nếu chưa có) và bổ sung các thông tin cấu hình sau:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
# Các cấu hình khác tùy chỉnh nếu cần thiết
```

---

## 🚀 Hướng dẫn cài đặt & Khởi chạy

### Cách 1: Khởi chạy nhanh bằng script (Khuyên dùng)
Dự án đã tích hợp sẵn một script tự động kiểm tra môi trường, tạo virtual environment (`venv`), cài đặt dependencies và chạy hệ thống:

```bash
chmod +x run.sh
./run.sh
```

### Cách 2: Khởi chạy thủ công từng bước

1. **Tạo và kích hoạt môi trường ảo (Virtual Environment)**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Cài đặt các thư viện cần thiết**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Chạy ứng dụng chính**:
   ```bash
   python main.py
   ```

Khi khởi chạy, chương trình sẽ hỏi bạn mã cổ phiếu muốn theo dõi mặc định (ví dụ: `FPT`, `HPG`, `VNM`,...).

### Cách 3: Sử dụng Docker & Docker Compose (Khuyên dùng khi triển khai)

Dự án đã được đóng gói sẵn để chạy trong Docker Container, tự động kết nối với dịch vụ Ollama chạy trên máy host.

1. **Khởi chạy hệ thống**:
   ```bash
   docker-compose up --build -d
   ```

2. **Cấu hình kết nối Ollama**:
   Mặc định, biến môi trường `OLLAMA_BASE_URL` trong [docker-compose.yml](file:///Users/tranduz/Documents/Stock_Prediction/docker-compose.yml) được cấu hình là `http://host.docker.internal:11434` để kết nối trực tiếp tới Ollama chạy trên máy host của bạn (đối với Windows và macOS).
   Nếu bạn sử dụng Linux, hãy đảm bảo Ollama được khởi chạy với biến cấu hình để chấp nhận kết nối ngoài: `OLLAMA_HOST=0.0.0.0` và cập nhật URL nếu cần.

3. **Kiểm tra logs của ứng dụng**:
   ```bash
   docker-compose logs -f app
   ```

4. **Dừng hệ thống**:
   ```bash
   docker-compose down
   ```

---

## 📁 Cấu trúc thư mục dự án

```text
├── main.py              # File chạy chính (Khởi chạy Scheduler và Chatbot)
├── agent.py             # Định nghĩa CrewAI Agent và pipeline phân tích cổ phiếu
├── bot.py               # Quản lý sự kiện và xử lý tin nhắn/lệnh của Telegram Bot
├── chart.py             # Module lấy dữ liệu và vẽ biểu đồ kỹ thuật TradingView-style
├── data.py              # Module tích hợp vnstock lấy thông tin chứng khoán thời gian thực
├── telegram_utils.py    # Các hàm tiện ích hỗ trợ gửi tin nhắn và ảnh sang Telegram
├── requirements.txt     # Danh sách các thư viện phụ thuộc của dự án
├── run.sh               # Bash script khởi chạy dự án tự động
├── vectordb/            # Thư mục lưu trữ database LanceDB cục bộ (được tạo tự động)
└── venv/                # Thư mục môi trường ảo Python (được tạo tự động)
```

---

## 🤖 Các câu lệnh hỗ trợ trên Bot Telegram

* `/start`: Khởi động lại cuộc trò chuyện và làm mới bộ nhớ tạm thời của bot.
* `/analyze <ticker>`: Phân tích nhanh một mã cổ phiếu bất kỳ (ví dụ: `/analyze HPG`).
* `/clear`: Xóa lịch sử trò chuyện hiện tại với chatbot.
* *Nhập mã cổ phiếu trực tiếp* (ví dụ: `FPT`, `VNM`): Bot sẽ tự động nhận diện mã cổ phiếu gồm 3 chữ cái viết hoa và tiến hành phân tích ngay lập tức.
# Sock_Predictor

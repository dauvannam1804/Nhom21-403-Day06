# ✈️ NEO 2.0 - Vietnam Airlines AI Assistant 🇻🇳

Chào mừng bạn đến với mã nguồn của dự án **NEO 2.0** - Trợ lý ảo AI thông minh dành riêng cho dịch vụ khách hàng của Vietnam Airlines. Dự án này được xây dựng theo kiến trúc **Agentic AI Workflow** bằng LangGraph kết hợp với giao diện hiện đại từ Next.js.

![Vietnam Airlines Assistant](frontend/public/a-14.jpg)

## 🌟 Tính năng nổi bật
Hệ thống sử dụng mô hình ngôn ngữ lớn (OpenAI `gpt-4o-mini`) kết hợp với luồng tác vụ đa nhịp (Multi-agentic workflow):
- **Tra cứu lịch bay**: Nhận diện tự động mã chuyến bay và ngày cất cánh.
- **Tra cứu hành lý ký gửi & xách tay**: Giới hạn trọng lượng và kích thước theo đúng chuẩn hãng cho hạng Phổ thông/Thương gia.
- **Tham khảo giá vé**: Lọc vé thông minh theo Điểm đi/Điểm đến, Buổi bay, Hạng vé và tự động sắp xếp Vé rẻ nhất.
- **Quản lý vé máy bay**: Truy vấn thông tin chi tiết qua Mã vé hoặc Họ tên.
- **Giao diện Cinematic**: Sử dụng Glassmorphism UI, Responsive Web App cùng Mascot của VNA, hỗ trợ hệ thống Rating sao thông minh.

---

## 🛠 Kiến trúc Hệ thống (Tech Stack)
- **Backend**: FastAPI (Python), LangGraph, Langchain, Pydantic (Structured Outputs).
- **Frontend**: Next.js (TypeScript), React, Vanilla CSS.
- **AI Model**: OpenAI GPT-4o-mini.

---

## 🚀 Hướng dẫn Cài đặt & Chạy Dự án (Local)

Để chạy được dự án này, bạn cần phải mở **2 Tab Terminal** song song (Một cái cho Backend, một cái cho Frontend).

### Bước 1: Thiết lập môi trường Backend (FastAPI + AI)

1. Mở Terminal đầu tiên và di chuyển vào thư mục gốc của dự án:
   ```bash
   cd Nhom21-403-Day06
   ```

2. (Tùy chọn) Khởi tạo và kích hoạt môi trường ảo (Virtual Environment)
   ```bash
   conda create -n vna_env python=3.10
   conda activate vna_env
   ```

3. Cài đặt các thư viện Python dùng cho Backend:
   ```bash
   pip install fastapi uvicorn langchain-openai langgraph pydantic python-dotenv
   ```

4. Cấu hình chìa khóa API (API Key):
   Tạo một file có tên là `.env` ngay tại thư mục gốc (cùng cấp với file `main.py`). Bổ sung nội dung sau vào file:
   ```env
   OPENAI_API_KEY=sk-proj-Thay_bang_API_KEY_OpenAI_cua_ban_vao_day
   ```

5. Khởi động AI Server:
   ```bash
   uvicorn api:app --reload
   ```
   *Terminal sẽ báo xanh: `Uvicorn running on http://0.0.0.0:8000` (Backend đã sẵn sàng nhận lệnh).*

---

### Bước 2: Thiết lập giao diện Frontend (Next.js)

1. Mở một **Tab Terminal thứ 2**, di chuyển vào thư mục giao diện:
   ```bash
   cd Nhom21-403-Day06/frontend
   ```

2. Tải các gói thư viện Node.js:
   ```bash
   npm install
   ```

3. Khởi chạy Giao diện Website:
   ```bash
   npm run dev
   ```

4. Mở trình duyệt web của bạn (Chrome, Edge) và truy cập vào địa chỉ:
   👉 **[http://localhost:3000](http://localhost:3000)**

---

## 🏗 Cấu trúc mã nguồn chính
```text
Nhom21-403-Day06/
├── api.py                   # Cổng kết nối (API Router) kết hợp FastAPI
├── main.py                  # Lõi AI (Trái tim của dự án): Cấu trúc luồng chạy LangGraph
├── state.py                 # Khai báo cấu trúc bộ nhớ của StateGraph
├── tools/                   # Các hàm công cụ Python thuần túy gọi DB giả lập
│   ├── flight_tools.py      
│   ├── fare_tools.py        
│   ├── baggage_tools.py     
│   └── ticket_tools.py      
├── prompts/                 # Lưu trữ định dạng "Nhân cách" và "Kịch bản" của AI
│   └── response_prompt.txt  
├── frontend/                # Thư mục mã nguồn Website React/Next.js
│   ├── src/app/page.tsx     # Giao diện Chatbot & Logic Fetch dữ liệu
│   └── src/app/globals.css  # Tinh chỉnh hiệu ứng Kính mờ (Glassmorphism)
└── data/                    # (Nếu có) Dữ liệu mẫu dạng JSON mô phỏng Database
```

## 📝 Bản quyền
Dự án được xây dựng và phát triển phục vụ mục đích học thuật / hackathon AI. Thương hiệu và Mascot VNA thuộc bản quyền của Vietnam Airlines.

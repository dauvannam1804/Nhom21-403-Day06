# Kế hoạch Triển khai (Implementation Plan) - Feature 1: Thông tin chuyến bay

Bản kế hoạch này thiết kế một demo hoàn chỉnh cho **Feature 1: Tra cứu thông tin chuyến bay**, bám sát theo kiến trúc Hybrid mà nhóm 403 đã phác thảo trong SPEC (dùng LLM để hiểu intent/trích xuất thực thể thay vì đóng vai trò lõi dữ liệu).

## Phân tích thiết kế hệ thống

### 1. Kiến trúc luồng Pipeline (Slot-filling + Tool Calling)

Vì domain hàng không ưu tiên **Precision > Recall**, ta không dọng thẳng câu hỏi của User vào LLM để nó tự trả lời. Ta thiết kế pipeline như sau:

1. **User Input:** "Chuyến VN245 ngày mai bay lúc mấy giờ?"
2. **LLM as NLU (Trích xuất & Hiểu):** LLM phân tích câu hỏi để lấy 2 tham số (Slots) quan trọng: 
   - `flight_code` = "VN245"
   - `date` = "ngày mai" (có quy đổi xử lý ra ngày cụ thể DD/MM/YYYY)
3. **Condition Check (Rule-based):**
   - *Đủ slot:* Sang bước 4.
   - *Thiếu slot:* Ví dụ khách chỉ hỏi "Chuyến VN245 mấy giờ bay?" -> Kích hoạt **Low-confidence path**, bot ép khách trả lời bằng câu hỏi *"Bạn muốn tra cứu bay vào ngày hôm nay hay ngày mai?"*
4. **Database Lookup:** Dùng code gọi hàm truy xuất dữ liệu chuyến bay từ Mock Database (JSON tĩnh).
5. **LLM Response Generation:** Trả kết quả JSON thô về cho LLM, để LLM format lại thành câu giao tiếp tự nhiên (VD: *"Chuyến bay VN245 hạ cánh lúc 15h, cửa ra máy bay số 4"*).
6. **UI Display:** Hiển thị cho người dùng qua giao diện.

### 2. Thiết kế Mock Data (Dữ liệu giả lập)

Chúng ta không cần Database xịn, chỉ cần một file tĩnh `mock_db.json` giả lập API tra cứu chuyến bay nội bộ của hãng.

```json
{
  "flights": [
    {
      "flight_code": "VN123",
      "departure": "HAN (Hà Nội)",
      "arrival": "SGN (TP.HCM)",
      "scheduled_departure_time": "2026-04-10 08:00:00",
      "scheduled_arrival_time": "2026-04-10 10:15:00",
      "status": "On Time",
      "gate": "V1",
      "terminal": "T1"
    },
    {
      "flight_code": "VN245",
      "departure": "SGN (TP.HCM)",
      "arrival": "DAD (Đà Nẵng)",
      "scheduled_departure_time": "2026-04-10 14:30:00",
      "scheduled_arrival_time": "2026-04-10 16:00:00",
      "status": "Delayed",
      "gate": "A4",
      "terminal": "T1"
    }
  ]
}
```

---

## Đề xuất Cấu trúc Source Code mẫu

Chúng ta sẽ dùng **Python** với UI bằng **Streamlit** (để mô phỏng khung chat nhanh gọn) và thư viện **LangChain / OpenAI** để xây dựng Agent gọi hàm. Đặt trong file `app.py`.

```python
import streamlit as st
import json

# 1. Giả lập Database Lookup Function (Tool)
def get_flight_status(flight_code: str, date: str) -> str:
    \"\"\"Tra cứu chuyến bay từ Database\"\"\"
    # Load mock data
    mock_db = {
        "VN123_2026-04-10": {
            "status": "On time", 
            "scheduled_departure": "2026-04-10 08:00:00",
            "estimated_departure": "2026-04-10 08:00:00",
            "gate": "V1"
        },
        "VN245_2026-04-10": {
            "status": "Delayed", 
            "scheduled_departure": "2026-04-10 14:30:00",
            "estimated_departure": "2026-04-10 15:30:00",
            "gate": "A4"
        }
    }
    
    key = f"{flight_code.upper()}_{date}"
    flight_info = mock_db.get(key)
    
    if flight_info:
        return json.dumps(flight_info)
    else:
        return json.dumps({"error": "not_found", "message": "Không tìm thấy chuyến bay, vui lòng kiểm tra lại mã mã chuyến hoặc ngày bay."})

# 2. Xây dựng Middleware (Giả mã logic xử lý AI)
# Trong thực tế lúc chạy Hackathon, bạn sẽ dùng OpenAI Structured Outputs để force LLM trả về đúng JSON {flight_code, date}
def process_chat(user_message: str) -> str:
    # BƯỚC 1: LLM trích xuất slot (Date, Flight_code)
    # Ví dụ: user_message = "Chuyến VN245 bay ngày 10/04 có đúng giờ không?" 
    # => LLM extract ra: VN245, 2026-04-10
    
    # BƯỚC 2: Kiểm tra Slots
    # Nếu thiếu flight_code -> Yêu cầu user bổ sung, prompt lại LLM.
    # Nếu thiếu ngày -> Cho quick reply: [Hôm nay] [Ngày mai]
    
    # BƯỚC 3: Có đủ thì lookup DB
    # result = get_flight_status(extracted_code, extracted_date)
    
    # BƯỚC 4: Lấy result đưa lại vào prompt cho LLM để tạo Response
    # system_prompt = f"Diễn đạt lại đoạn JSON {result} này bằng giọng điệu hỗ trợ khách hàng của bot hàng không thật lịch sự"
    
    # *Phần này đang mock luôn câu trả lời để minh họa*:
    return "Chuyến bay VN245 ngày 10/04 hiện đang bị Delay (Chậm giờ), dự kiến khởi hành lúc 14:30. Cổng ra máy bay là A4."

# 3. Streamlit UI (Giao diện Chatbot)
st.title("✈️ NEO 2.0 - Demo Tra Cứu Chuyến Bay")

# Khởi tạo history memory ngắn hạn
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# user input
if prompt := st.chat_input("VD: Chuyến VN123 bay ngày 10/4 hạ cánh mấy giờ?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # AI response
    with st.chat_message("assistant"):
        response = process_chat(prompt)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
```

---

## Đề xuất Cấu trúc thư mục Code (Folder Structure)

Để triển khai dự án rõ ràng, code dễ chia task trong suốt quá trình Hackathon cũng như dễ gộp code, bạn nên thiết lập cấu trúc theo dạng module hóa thay vì nhồi tất cả vào `app.py`.

```text
Nhom21-403-Day06/
├── data/
│   └── mock_flights.json   # Database tĩnh (thay vì code cứng dict trong app.py)
├── src/
│   ├── __init__.py
│   ├── llm_engine.py       # Tích hợp LLM (OpenAI API) chuyên lo việc trích xuất Slot và sinh câu trả lời
│   ├── database.py         # Các module gọi DB để lấy thông tin (VD: get_flight_status)
│   └── prompts.py          # Tách biệt các system prompt phức tạp ra đây cho đỡ vướng UI
├── app.py                  # File chạy giao diện chat Streamlit (Render UI và quản lý session)
├── requirements.txt        # Danh sách thư viện (streamlit, langchain, openai...)
└── .env                    # Chứa mã bảo mật (OPENAI_API_KEY). LƯU Ý: Không bao giờ commit file này lên Git!
```

---
### Checklist Cần Bàn Bạc / Mở Rộng
- [ ] Xác nhận việc xài Stack công nghệ: **Python + Streamlit + LangChain (OpenAI)** là được nhất để làm MVP chưa? (Nếu muốn đổi sang Gradio hay v0.dev front-end thì báo lại).
- [ ] Phần NLU trích xuất ở Bước 1 Pipeline: Sẽ dùng Function Calling/Structured Output của OpenAI model (như gpt-4o-mini vì rẻ và bắt intent tốt). 
- [ ] Cần tạo thêm luồng để user bấm nút chứ không bắt gõ 100% text không?

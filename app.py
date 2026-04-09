import streamlit as st
import os
from dotenv import load_dotenv

# Provide an informative message if there's module mismatch
try:
    from src.llm_engine import process_chat
except ImportError as e:
    st.error(f"Lỗi khởi tạo: {e}")
    st.stop()

# Load env variables (OPENAI_API_KEY)
load_dotenv()

# Cấu hình giao diện Streamlit
st.set_page_config(page_title="NEO 2.0 - Vietnam Airlines", page_icon="✈️", layout="centered")

st.title("✈️ Chatbot NEO 2.0")
st.subheader("Trợ lý tra cứu thông tin chuyến bay")

# Kiểm tra xem User đã cài đặt OpenRouter API Key chưa
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    st.warning("⚠️ CHÚ Ý: Chưa tìm thấy biến môi trường `OPENROUTER_API_KEY`. Bạn cần tạo tệp `.env` ở thư mục gốc chứa API key của bạn, hoặc dùng sidebar để nhập.")
    user_api_key = st.text_input("Nhập OpenRouter API Key của bạn để tiếp tục:", type="password")
    if user_api_key:
        os.environ["OPENROUTER_API_KEY"] = user_api_key
        st.success("Đã ghi nhận khoá máy chủ, vui lòng reload hoặc dùng bot.")
        
# Khởi tạo history memory
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Lời chào mồi của Bot
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Xin chào! Tôi là trợ lý ảo tinh chỉnh **NEO 2.0**. Tôi có thể giúp bạn kiểm tra trạng thái cực nhanh. Hãy cho tôi biết mã chuyến bay và ngày bạn khởi hành (VD: Chuyến VN245 ngày 10/4)."
    })

# Render lại chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input Box
if prompt := st.chat_input("VD: Chuyến VN123 hôm nay mấy giờ bay?"):
    # Append & hiển thị tin của khách
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process AI logic & hiển thị câu trả lời
    with st.chat_message("assistant"):
        with st.spinner("NEO đang rà soát hệ thống..."):
            if not os.environ.get("OPENROUTER_API_KEY"):
                response = "Xin lỗi, hệ thống chưa được kết nối cấu hình API Key. Neo chưa thể phục vụ."
            else:
                response = process_chat(prompt)
        
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# Cột dọc Sidebar - Chức năng Debug
with st.sidebar:
    st.header("🛠 Cấu hình nhanh / Debug")
    if st.button("🗑 Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()
    st.info("💡 **Gợi ý Mock Data sẵn có:** \n- VN123 ngày 2026-04-10 \n- VN245 ngày 2026-04-10")
    st.markdown("---")
    st.caption("AI Product Lab - Day 06")

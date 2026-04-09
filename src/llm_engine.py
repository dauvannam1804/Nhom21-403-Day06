import os
import json
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.prompts import SYSTEM_PROMPT
from src.database import get_flight_status

load_dotenv()

# Define the Pydantic schema for information extraction
class FlightSlot(BaseModel):
    flight_code: Optional[str] = Field(default=None, description="Mã chuyến bay, rỗng nếu người dùng chưa cung cấp. Ví dụ: VN245, VN123")
    date: Optional[str] = Field(default=None, description="Ngày khởi hành theo định dạng YYYY-MM-DD. Rỗng nếu chưa cung cấp. Quy đổi từ ngữ cảnh như 'hôm nay', 'ngày mai' ra ngày cụ thể.")

def extract_slots(user_message: str) -> FlightSlot:
    """Uses LLM with Structured Outputs to extract slots from user message."""
    llm = ChatOpenAI(
        model="openai/gpt-4o-mini", 
        temperature=0,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )
    structured_llm = llm.with_structured_output(FlightSlot)
    
    # Calculate today's date so LLM knows the context for "today", "tomorrow"
    today = datetime.now().strftime("%Y-%m-%d")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"Bạn là hệ thống NLU trích xuất thông tin hành khách. Hãy xác định mã chuyến bay và ngày bay. Nếu khách hàng không đề cập, trả về None. Ngày hôm nay là (theo tham chiếu: {today}). Nếu khách nói 'hôm nay' thì trả về {today}, 'ngày mai' thì cộng 1 ngày ra format YYYY-MM-DD."),
        ("user", "{input}")
    ])
    
    chain = prompt | structured_llm
    result = chain.invoke({"input": user_message})
    return result

def draft_final_response(user_message: str, db_result: str) -> str:
    """Uses LLM to draft a friendly conversational response based on JSON data."""
    llm = ChatOpenAI(
        model="openai/gpt-4o-mini", 
        temperature=0.2,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "Câu hỏi của user: {user_input}\n\nDữ liệu trả về từ cấu hình hệ thống (JSON):\n{db_result}\n\nHãy sinh ra một câu trả lời mượt mà, định dạng rõ ràng.")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"user_input": user_message, "db_result": db_result})
    return response.content

def process_chat(user_message: str) -> str:
    # 1. Trích xuất slots (Slot filling)
    try:
        slots = extract_slots(user_message)
    except Exception as e:
        return f"Xin lỗi, hệ thống AI đang gặp sự cố kết nối bộ xử lý. Chi tiết lỗi: {str(e)}"
    
    f_code = slots.flight_code
    f_date = slots.date
    
    # 2. Kiểm tra điều kiện (Rule-based condition check - The Augmentation logic)
    if not f_code and not f_date:
        return "Để tra cứu một cách chính xác, bạn vui lòng cung cấp **mã chuyến bay** và **ngày bay** nhé (VD: chuyến VN123 ngày hôm nay)."
    
    if not f_code:
        return f"Neo đã nhận được ngày bay là {f_date}. Xin vui lòng cho biết **mã chuyến bay** của bạn."
        
    if not f_date:
        return f"Neo đã nhận được mã chuyến {f_code.upper()}. Bạn muốn tra cứu chuyến bay này vào **ngày nào**? (VD: hôm nay, ngày mai)."
        
    # 3. Lookup Database (Data Retrieval)
    flight_data = get_flight_status(f_code, f_date)
    
    if flight_data:
        db_result = json.dumps(flight_data, ensure_ascii=False)
    else:
        db_result = json.dumps({"error": "Không tìm thấy chuyến bay", "flight_code": f_code, "query_date": f_date}, ensure_ascii=False)
        
    # 4. Generate AI formulation final response
    try:
        final_answer = draft_final_response(user_message, db_result)
        return final_answer
    except Exception as e:
        return f"Có lỗi phụ tải khi xuất câu trả lời: {str(e)}"

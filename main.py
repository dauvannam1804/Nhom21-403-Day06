import os
import json
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage
from state import AgentState
from tools.flight_tools import get_flight_info
from tools.ticket_tools import get_ticket_details
from tools.fare_tools import search_fares
from tools.baggage_tools import get_baggage_policy

load_dotenv()

# Khởi tạo LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# Pydantic struct cho Extraction Node
class Entities(BaseModel):
    flight_code: Optional[str] = Field(default=None, description="Mã chuyến bay, ví dụ VN123")
    ticket_number: Optional[str] = Field(default=None)
    passenger_name: Optional[str] = Field(default=None)
    departure: Optional[str] = Field(default=None)
    arrival: Optional[str] = Field(default=None)
    date: Optional[str] = Field(default=None, description="Ngày khởi hành theo định dạng YYYY-MM-DD")
    cabin_class: Optional[str] = Field(default=None)
    baggage_type: Optional[str] = Field(default=None)

class ExtractionResult(BaseModel):
    intent: str = Field(description="general, flight_info, ticket_info, fare_search, hoặc baggage_info")
    entities: Entities

def read_prompt(file_name):
    """Đọc nội dung file prompt từ thư mục prompts/."""
    full_path = os.path.join("prompts", file_name)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def manage_memory_and_cache(state: AgentState):
    """Giữ 5 lượt chat gần nhất và kiểm tra Cache."""
    messages = state["messages"]
    
    # 1. Cắt tỉa memory (giữ 5 lượt = 10 messages)
    if len(messages) > 10:
        messages = messages[-10:]
    
    # 2. Kiểm tra Cache
    current_user_msg = messages[-1].content.strip().lower()
    for i in range(len(messages) - 2, -1, -1):
        msg = messages[i]
        if isinstance(msg, HumanMessage) and msg.content.strip().lower() == current_user_msg:
            if i + 1 < len(messages) and isinstance(messages[i+1], AIMessage):
                cached_response = messages[i+1].content
                return {
                    "messages": messages, 
                    "query_results": cached_response, 
                    "is_cached": True
                }
    
    return {"messages": messages, "is_cached": False}

def intent_classifier(state: AgentState):
    """Node phân loại ý định người dùng."""
    if state.get("is_cached"):
        return state

    last_message = state["messages"][-1].content
    intent = "general"
    if "chuyến bay" in last_message.lower() or "vn" in last_message.lower():
        intent = "flight_info"
    elif "vé" in last_message.lower() and "giá" not in last_message.lower():
        intent = "ticket_info"
    elif "giá vé" in last_message.lower() or "tìm vé" in last_message.lower():
        intent = "fare_search"
    elif "hành lý" in last_message.lower():
        intent = "baggage_info"
        
    return {"current_intent": intent}

def tool_node(state: AgentState):
    """Node gọi các hàm Python để truy vấn dữ liệu thực tế từ Entities trích xuất được."""
    if state.get("is_cached"):
        return state

    intent = state.get("current_intent")
    entities = state.get("extracted_data", {})
    query_results = "Không tìm thấy thông tin phù hợp."
    
    if intent == "flight_info":
        query_results = get_flight_info(flight_code="VN123")
    elif intent == "ticket_info":
        query_results = get_ticket_details(
            ticket_number=entities.get("ticket_number"),
            passenger_name=entities.get("passenger_name")
        )
    elif intent == "fare_search":
        query_results = search_fares(
            departure=entities.get("departure"),
            arrival=entities.get("arrival"),
            cabin_class=entities.get("cabin_class")
        )
    elif intent == "baggage_info":
        query_results = get_baggage_policy(
            cabin_class=entities.get("cabin_class"),
            baggage_type=entities.get("baggage_type", "checked")
        )
        
    return {"query_results": query_results}

def responder(state: AgentState):
    """Node tạo câu trả lời cuối cùng dùng response_prompt.txt."""
    if state.get("is_cached"):
        return {"messages": [AIMessage(content=state["query_results"])]}

    results = state.get("query_results")
    prompt = f"Dựa trên dữ liệu sau: {results}, hãy trả lời câu hỏi của người dùng một cách chuyên nghiệp."
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"messages": [response]}

# Xây dựng Graph
workflow = StateGraph(AgentState)

workflow.add_node("memory_and_cache", manage_memory_and_cache)
workflow.add_node("classifier", intent_classifier)
workflow.add_node("tools", tool_node)
workflow.add_node("responder", responder)

workflow.set_entry_point("memory_and_cache")

def route_after_cache(state: AgentState):
    if state.get("is_cached"):
        return "responder"
    return "classifier"

workflow.add_conditional_edges("memory_and_cache", route_after_cache)
workflow.add_edge("classifier", "tools")
workflow.add_edge("tools", "responder")
workflow.add_edge("responder", END)

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    print("--- Chatbot Hàng Không (NEO 2.0) đã sẵn sàng! (Gõ 'exit' để thoát) ---")
    
    # Khởi tạo state ban đầu
    state = {
        "messages": [],
        "extracted_data": {},
        "query_results": "",
        "current_intent": "general",
        "is_cached": False
    }
    
    while True:
        user_input = input("\nKhách hàng: ")
        if user_input.lower() in ["exit", "quit", "thoát"]:
            print("Cảm ơn bạn đã sử dụng dịch vụ. Tạm biệt!")
            break
            
        # Thêm tin nhắn của user vào state
        state["messages"].append(HumanMessage(content=user_input))
        
        # Chạy Graph
        # Lưu ý: Mỗi lần invoke sẽ trả về state mới
        config = {"configurable": {"thread_id": "user_session_1"}}
        state = app.invoke(state, config=config)
        
        final_response = state["messages"][-1].content
        print(f"NEO 2.0: {final_response}")
        
        if state.get("is_cached"):
            print("(Phản hồi từ Cache)")

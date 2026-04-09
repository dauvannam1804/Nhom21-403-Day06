import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage, AIMessage
from state import AgentState
from tools.flight_tools import get_flight_info
from tools.ticket_tools import get_ticket_details
from tools.fare_tools import search_fares
from tools.baggage_tools import get_baggage_policy

load_dotenv()

# Khởi tạo LLM
llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0,
    api_key=os.environ.get("OPENROUTER_API_KEY", "not_provided"),
    base_url="https://openrouter.ai/api/v1"
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

def manage_memory_and_cache(state: AgentState):
    """Giữ 5 lượt chat gần nhất và kiểm tra Cache."""
    messages = state["messages"]
    
    # 1. Cắt tỉa memory (giữ 5 lượt = 10 messages)
    if len(messages) > 10:
        messages = messages[-10:]
    
    # 2. Kiểm tra Cache
    # Lấy câu hỏi hiện tại
    current_user_msg = messages[-1].content.strip().lower()
    
    # Tìm trong lịch sử các HumanMessage cũ (trừ cái cuối cùng)
    for i in range(len(messages) - 2, -1, -1):
        msg = messages[i]
        if isinstance(msg, HumanMessage) and msg.content.strip().lower() == current_user_msg:
            # Nếu tìm thấy câu hỏi trùng, lấy câu trả lời (AIMessage) ngay sau nó
            if i + 1 < len(messages) and not isinstance(messages[i+1], HumanMessage):
                cached_response = messages[i+1].content
                return {
                    "messages": messages, 
                    "query_results": cached_response, 
                    "is_cached": True
                }
    
    return {"messages": messages, "is_cached": False}

def intent_classifier(state: AgentState):
    """Node phân loại ý định người dùng và trích xuất thực thể có Memory."""
    if state.get("is_cached"):
        return state
        
    try:
        with open("prompts/extraction_prompt.txt", "r", encoding="utf-8") as f:
            sys_prompt = f.read()
    except Exception:
        sys_prompt = "Bạn là hệ thống Trích xuất."

    # Lấy thông tin ngày hiện tại để làm base time
    from datetime import datetime
    sys_prompt += f"\nLưu ý Context: Hôm nay là {datetime.now().strftime('%Y-%m-%d')}."
    
    structured_llm = llm.with_structured_output(ExtractionResult)
    
    try:
        # Pass toàn bộ lịch sử trò chuyện (messages) để AI tự nhớ Context (Ví dụ khách nói VN123 từ trước)
        messages_to_pass = [SystemMessage(content=sys_prompt)] + state["messages"]
        result = structured_llm.invoke(messages_to_pass)
        
        intent = result.intent
        extracted_data = result.entities.dict()
    except Exception as e:
        intent = "general"
        extracted_data = {}

    return {"current_intent": intent, "extracted_data": extracted_data}

def tool_node(state: AgentState):
    """Node gọi các hàm Python để truy vấn dữ liệu."""
    if state.get("is_cached"):
        return state

    intent = state.get("current_intent")
    entities = state.get("extracted_data", {})
    query_results = "Không tìm thấy thông tin phù hợp."
    
    if intent == "flight_info":
        f_code = entities.get("flight_code")
        f_date = entities.get("date")
        
        if not f_code and not f_date:
            query_results = "SYSTEM_NOTE: Vui lòng yêu cầu khách hàng cung cấp mã chuyến bay và ngày bay để kiểm tra."
        elif not f_code:
            query_results = f"SYSTEM_NOTE: Vui lòng yêu cầu khách hàng bổ sung mã chuyến bay cho ngày {f_date}."
        elif not f_date:
            query_results = f"SYSTEM_NOTE: Vui lòng hỏi khách hàng xem chuyến {f_code} dự định cất cánh vào ngày nào."
        else:
            data = get_flight_info(flight_code=f_code, date=f_date)
            query_results = str(data) if data else "SYSTEM_NOTE: Không tìm thấy chuyến bay theo mã và ngày cung cấp. Khuyên khách hàng kiểm tra lại."
            
    elif intent == "ticket_info":
        # Sử dụng logic Nam mới viết
        query_results = get_ticket_details(passenger_name="NGUYEN/DUNG BP")
    elif intent == "fare_search":
        query_results = search_fares(departure="HAN", arrival="SGN")
    elif intent == "baggage_info":
        query_results = get_baggage_policy(cabin_class="Economy")
        
    return {"query_results": query_results}

def responder(state: AgentState):
    """Node tạo câu trả lời cuối cùng."""
    if state.get("is_cached"):
        # Trả về kết quả từ cache dưới dạng AIMessage
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content=state["query_results"])]}

    results = state.get("query_results")
    
    try:
        with open("prompts/response_prompt.txt", "r", encoding="utf-8") as f:
            sys_prompt = f.read()
    except Exception:
        sys_prompt = "Bạn là trợ lý giải đáp của Vietnam Airlines."

    prompt_content = f"Dựa trên dữ liệu sau (hoặc lưu ý điều hướng từ hệ thống): {results}\nHãy đưa ra câu trả lời trực tiếp cho khách hàng một cách tự nhiên dựa trên câu hỏi sau: {state['messages'][-1].content}."
    
    chat_llm = ChatOpenAI(
        model="openai/gpt-4o-mini",
        temperature=0.3,
        api_key=os.environ.get("OPENROUTER_API_KEY", "not_provided"),
        base_url="https://openrouter.ai/api/v1"
    )
    
    response = chat_llm.invoke([
        SystemMessage(content=sys_prompt), 
        HumanMessage(content=prompt_content)
    ])
    return {"messages": [response]}

# Xây dựng Graph
workflow = StateGraph(AgentState)

workflow.add_node("memory_and_cache", manage_memory_and_cache)
workflow.add_node("classifier", intent_classifier)
workflow.add_node("tools", tool_node)
workflow.add_node("responder", responder)

workflow.set_entry_point("memory_and_cache")

# Điều hướng: Nếu là cache thì đi thẳng tới responder, nếu không thì đi tới classifier
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
    
    # Thiết lập ID phiên để MemorySaver có thể lưu vết hội thoại
    config = {"configurable": {"thread_id": "session_1"}}
    
    while True:
        user_input = input("\nKhách hàng: ")
        if user_input.lower() in ["exit", "quit", "thoát"]:
            print("Cảm ơn bạn đã sử dụng dịch vụ. Tạm biệt!")
            break
            
        # Chạy Graph với dữ liệu mới và truyền config state vào
        # Chú ý: LangGraph dùng reducer nên {"messages": [HumanMessage(content=user_input)]} sẽ tự append thay vì ghi đè!
        state = app.invoke({"messages": [HumanMessage(content=user_input)]}, config)
        
        # Lấy tin nhắn phản hồi cuối cùng từ Assistant
        final_response = state["messages"][-1].content
        print(f"NEO 2.0: {final_response}")
        
        # Kiểm tra xem có phải từ cache không để thông báo (Tùy chọn)
        if state.get("is_cached"):
            print("(Phản hồi từ Cache)")

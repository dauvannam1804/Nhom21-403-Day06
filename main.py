import os
import json
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from state import AgentState
from tools.flight_tools import get_flight_info
from tools.ticket_tools import get_ticket_details
from tools.fare_tools import search_fares
from tools.baggage_tools import get_baggage_policy

load_dotenv()

# Khởi tạo LLM với OpenAI
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def load_prompt(file_name: str) -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", file_name)
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

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
    """Node phân loại ý định người dùng và trích xuất thực thể."""
    if state.get("is_cached"):
        return state

    last_message = state["messages"][-1].content
    extraction_prompt = load_prompt("extraction_prompt.txt")
    
    # Yêu cầu LLM trích xuất JSON
    response = llm.invoke([
        SystemMessage(content=extraction_prompt),
        HumanMessage(content=f"User query: {last_message}")
    ])
    
    # Parse cấu trúc JSON từ LLM
    try:
        content = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        intent = data.get("intent", "general")
        entities = data.get("entities", {})
    except Exception as e:
        intent = "general"
        entities = {}
        
    return {"current_intent": intent, "extracted_data": entities}

def tool_node(state: AgentState):
    """Node gọi các hàm Python để truy vấn dữ liệu."""
    if state.get("is_cached"):
        return state

    intent = state.get("current_intent")
    entities = state.get("extracted_data", {})
    
    query_results = "Không nhận diện được yêu cầu cụ thể."
    
    if intent == "flight_info":
        flight_code = entities.get("flight_code")
        if flight_code:
            query_results = get_flight_info(flight_code=flight_code)
    elif intent == "ticket_info":
        passenger_name = entities.get("passenger_name")
        ticket_number = entities.get("ticket_number")
        if ticket_number:
            query_results = get_ticket_details(ticket_number=ticket_number)
        elif passenger_name:
            query_results = get_ticket_details(passenger_name=passenger_name)
    elif intent == "fare_search":
        departure = entities.get("departure")
        arrival = entities.get("arrival")
        if departure and arrival:
            query_results = search_fares(departure=departure, arrival=arrival)
    elif intent == "baggage_info":
        cabin_class = entities.get("cabin_class")
        baggage_type = entities.get("baggage_type") or "checked"
        if cabin_class:
            query_results = get_baggage_policy(cabin_class=cabin_class, baggage_type=baggage_type)
        else:
            query_results = {"error": "Thiếu thông tin hạng ghế (Economy hoặc Business)."}
            
    return {"query_results": query_results}

def responder(state: AgentState):
    """Node tạo câu trả lời cuối cùng sử dụng System Prompt."""
    if state.get("is_cached"):
        # Trả về kết quả từ cache dưới dạng AIMessage
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content=state["query_results"])]}

    results = state.get("query_results")
    last_message = state["messages"][0].content if state["messages"] else ""
    
    response_prompt = load_prompt("response_prompt.txt")
    
    prompt = f"Dữ liệu tra cứu: {json.dumps(results, ensure_ascii=False)}\nCâu hỏi gốc của người dùng: {last_message}"
    
    response = llm.invoke([
        SystemMessage(content=response_prompt),
        HumanMessage(content=prompt)
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

app = workflow.compile()

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
        state = app.invoke(state)
        
        # Lấy tin nhắn phản hồi cuối cùng từ Assistant
        final_response = state["messages"][-1].content
        print(f"NEO 2.0: {final_response}")
        
        # Kiểm tra xem có phải từ cache không để thông báo (Tùy chọn)
        if state.get("is_cached"):
            print("(Phản hồi từ Cache)")

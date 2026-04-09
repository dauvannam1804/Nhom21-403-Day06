from utils import get_tickets

def get_ticket_details(ticket_number: str = None, passenger_name: str = None):
    """
    NHIỆM VỤ CỦA NAM:
    - Tìm kiếm vé dựa trên ticket_number HOẶC passenger_name.
    - Lưu ý: passenger_name có thể cần chuẩn hóa (in hoa, không dấu) để tìm đúng.
    - Trả về thông tin: Mã hiệu chuyến bay, hạng ghế, số ghế, ngày bay.
    """
    tickets = get_tickets()
    results = []
    
    if ticket_number:
        # ticket_number trong JSON là một danh sách các chuỗi
        results = [t for t in tickets if any(ticket_number == tn for tn in t.get("ticket_number", []))]
    
    elif passenger_name:
        # Chuẩn hóa tên để tìm kiếm (In hoa)
        search_name = passenger_name.upper()
        results = [t for t in tickets if search_name in t.get("passenger_name", "").upper()]
        
    return results

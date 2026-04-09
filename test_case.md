# Hướng dẫn Kiểm thử (Test Cases) cho NEO 2.0



## 1. Tính năng: Tra cứu chuyến bay (Flight Info)

Bản demo cho thấy Chatbot có khả năng hiểu ngữ cảnh ngày tháng tương đối và bộ lọc thông tin thông minh.

**Test Case 1.1: Luồng chuẩn (Happy Path)**
- **Khách hàng**: `Cho tôi thông tin chuyến bay VN123 ngày 10/4.`
- **Kỳ vọng**: Bot trả về thông tin chi tiết của chuyến bay VN123 (Giờ đi, giờ đến, trạng thái) với format Bullet points dễ đọc.

**Test Case 1.2: Xử lý ngữ cảnh "Hôm đó" (Relative Date / Memory)**
- (Ngay sau câu hỏi ở Test Case 1.1)
- **Khách hàng**: `Thế vé chuyến bay hạng thương gia hôm đó giá bao nhiêu?`
- **Kỳ vọng**: Bot tự động hiểu "hôm đó" là ngày 10/4 và trả về giá vé Thương gia của chuyến bay ngày 10/4. 

**Test Case 1.3: Sai mã chuyến bay (Pre-check Lỗi)**
- **Khách hàng**: `Tìm chuyến bay VN9999.`
- **Kỳ vọng**: Bot lập tức báo lỗi "Mã chuyến bay không tồn tại" mà KHÔNG hạch hỏi hay bắt bẻ khách phải cung cấp thêm ngày đi (Tiết kiệm thời gian, UX tốt).

---

## 2. Tính năng: Tìm vé & Báo giá (Fare Search)

Bản demo cho thấy khả năng "Slot-Filling" - tự động nhận biết thông tin bị thiếu và khéo léo yêu cầu khách bổ sung.

**Test Case 2.1: Thiếu thông tin (Slot-Filling)**
- **Khách hàng**: `Tôi muốn mua vé từ Đà Nẵng đi Hà Nội.`
- **Kỳ vọng**: Bot không vội báo giá (tránh lấy dữ liệu sai lệch) mà sẽ hỏi lại: "Vui lòng cung cấp thêm thông tin về **ngày bay**".

**Test Case 2.2: Bổ sung thông tin**
- (Ngay sau câu hỏi ở Test Case 2.1)
- **Khách hàng**: `Ngày 10/4 nhé.`
- **Kỳ vọng**: Bot kết hợp Đầu đi, Đầu đến và Ngày bay để in ra danh sách các các mức giá phù hợp.

**Test Case 2.3: Bộ lọc đa điều kiện phức tạp**
- **Khách hàng**: `Tìm chuyến bay rẻ nhất từ Hà Nội đi TP.HCM sáng ngày mai.`
- **Kỳ vọng**: Bot tự lấy ngày hôm nay cộng lên (ngày mai), lọc riêng buổi sáng (morning) và chỉ trả ra 1 kết quả rẻ nhất.

---

## 3. Tính năng: Tra cứu vé cá nhân (Ticket Info)

Bản demo cho thấy hệ thống bảo mật chặt chẽ: chỉ tra cứu vé bằng MÃ VÉ thay vì tên riêng để bảo vệ quyền riêng tư.

**Test Case 3.1: Nhập tên riêng (Từ chối khéo léo)**
- **Khách hàng**: `Nguyễn Văn A` hoặc `Tra vé cho DUNG NGUYEN.`
- **Kỳ vọng**: Bot nhắc nhở khách hàng: "Hệ thống chỉ hỗ trợ tra cứu thông tin vé bằng mã vé. Vui lòng cung cấp mã vé."

**Test Case 3.2: Luồng chuẩn bằng mã vé**
- **Khách hàng**: `Tra mã vé 0905262286.`
- **Kỳ vọng**: Bot liệt kê đầy đủ thông tin: Họ tên hành khách (IN HOA chuẩn format), Chuyến bay, Giờ bay, Hạng cabin và Số ghế.

---

## 4. Tính năng: Tra cứu quy định hành lý (Baggage Info)

**Test Case 4.1: Hỏi chung chung**
- **Khách hàng**: `Hạng phổ thông được mang bao nhiêu kg hành lý?`
- **Kỳ vọng**: Bot liệt kê chính xác số cân của hành lý xách tay (Carry-on) và ký gửi (Checked) của hạng Phổ thông (Economy).

**Test Case 4.2: Hỏi cụ thể (Ví dụ Thương gia)**
- **Khách hàng**: `Hành lý xách tay hạng thương gia là mấy cân?`
- **Kỳ vọng**: Bot lọc ra đúng thông tin của hành lý xách tay cho hạng Business.

---
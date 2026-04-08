# SPEC - AI Product Hackathon

**Nhóm:Nhóm 21-403**

**Track:** ☐ VinFast · ☐ Vinmec · ☐ VinUni-VinSchool · ☐ XanhSM · ☑ Open

**Problem statement (1 câu):** Hành khách Vietnam Airlines mất nhiều thời gian tra cứu giá vé, thông tin chuyến bay và các policy áp dụng cho đúng trường hợp của mình; NEO phiên bản cải thiện giúp hiểu câu hỏi tự nhiên tốt hơn, giảm loop/lệch flow và điều hướng user tới đúng thông tin hoặc đúng kênh hỗ trợ nhanh hơn.

> Lưu ý: Đây là SPEC đề xuất cho phiên bản cải thiện của NEO hiện tại, không phải mô tả nguyên trạng chatbot đang chạy.

---

## 1. AI Product Canvas

|   | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| **Câu hỏi** | User nào? Pain gì? AI giải gì? | Khi AI sai thì sao? User sửa bằng cách nào? | Cost/latency bao nhiêu? Risk chính? |
| **Trả lời** | *User chính là hành khách nội địa/quốc tế, khách sắp bay, khách cần tra cứu gấp ngoài giờ hành chính, và hội viên Lotusmiles. Pain hiện tại là khó tìm đúng thông tin trên website, dễ bị lạc giữa nhiều flow tra cứu, chờ tổng đài lâu, và phải tự diễn giải policy chung cho case riêng của mình. NEO 2.0 giúp user hỏi bằng ngôn ngữ tự nhiên, hiểu rõ hơn ý định truy vấn, giữ ngữ cảnh trong phiên chat và dẫn tới đúng thông tin/đúng bước tiếp theo nhanh hơn.* | *Khi AI sai, user có thể bị trả lời lệch ý, bị kéo về flow cũ, hoặc nhận phản hồi lặp khiến mất thời gian và mất niềm tin. User sửa bằng cách đổi cách diễn đạt, chọn lại quick reply, hoặc bấm gặp nhân viên hỗ trợ. Thiết kế cần làm cho việc “thoát bot” và “thử flow khác” dễ thấy, không để user mắc kẹt trong dead-end.* | *Giả định hackathon: cost thấp vì hệ thống core dùng intent classification + retrieval + API lookup, chỉ dùng LLM nhẹ hoặc không dùng LLM cho mọi request. Latency mục tiêu <2s cho tra cứu cơ bản. Risk chính là trả lời sai policy, trả lời sai context áp dụng, retrieval sai hoặc không đủ thông tin, loop phản hồi, hoặc user over-trust bot trong các case nhạy cảm như đổi vé/hoàn vé/giấy tờ.* |

**Automation hay augmentation?** ☐ Automation · ☑ Augmentation

Justify: *Với các truy vấn thông tin cơ bản như giá vé, tình trạng chuyến bay, tra cứu theo mã đặt chỗ, NEO có thể trả lời gần như tự động. Nhưng với các case có nhiều biến số hoặc liên quan giao dịch thật như đổi vé, hoàn vé, thay đổi booking, AI chỉ nên đóng vai trò hướng dẫn luồng xử lý và tóm tắt policy. Quyết định cuối cùng và thao tác xác nhận vẫn thuộc về user hoặc nhân viên hỗ trợ.*

**Learning signal:**

1. User correction đi vào đâu?  
   *Đi vào chat logs và event logs. Các tín hiệu quan trọng gồm: user hỏi lại nhiều lần, đổi cách diễn đạt, bấm `Gặp nhân viên hỗ trợ`, bỏ dở giữa chừng, hoặc bị lặp trong cùng một flow. Các transcript này được gắn cờ để review luồng gãy và intent sai.*

2. Product thu signal gì để biết tốt lên hay tệ đi?  
   *CSAT sau chat, Deflection Rate, tỷ lệ hand-off sang người thật, tỷ lệ re-ask trong cùng session, tỷ lệ loop flow, và tỷ lệ hoàn tất tra cứu thành công.*

3. Data thuộc loại nào? ☑ User-specific · ☑ Domain-specific · ☐ Real-time · ☑ Human-judgment · ☐ Khác: ___  
   Có marginal value không?  
   *Có. Model chung không biết policy nội bộ, giá vé theo thời điểm, logic tra cứu booking cụ thể, hoặc các luồng user thường bị kẹt trong hệ sinh thái Vietnam Airlines. Dữ liệu hội thoại thật giúp xây “data moat” về support flow và error patterns.*

---

## 2. User Stories - 4 paths

### Feature: Trợ lý tra cứu giá vé và thông tin chuyến bay

**Trigger:** *User mở khung chat NEO trên web và hỏi: “Giá vé từ Hà Nội đến TP.HCM trong tuần này là bao nhiêu?” hoặc “Cho tôi thông tin chuyến bay Hà Nội - Milan từ 1/8”.*

| Path | Câu hỏi thiết kế | Mô tả |
|------|-------------------|-------|
| Happy - AI đúng, tự tin | User thấy gì? Flow kết thúc ra sao? | *Bot hiểu đúng ý định tra cứu, hỏi bổ sung đúng 1-2 biến nếu còn thiếu như ngày đi hoặc chiều bay, rồi trả về khoảng giá/chuyến bay liên quan kèm link tới trang tra cứu chính thức. User tiếp tục tra cứu hoặc chuyển sang đặt vé.* |
| Low-confidence - AI không chắc | System báo “không chắc” bằng cách nào? User quyết thế nào? | *Bot không đoán bừa mà nói rõ đang thiếu dữ liệu, sau đó hiển thị quick replies như [Chọn ngày đi], [Xem giá rẻ nhất], [Tra cứu theo mã đặt chỗ], [Gặp nhân viên hỗ trợ]. User chọn hướng phù hợp thay vì phải gõ lại từ đầu.* |
| Failure - AI sai | User biết AI sai bằng cách nào? Recover ra sao? | *Bot trả lời lệch ý, kéo user về flow cũ, hoặc lặp phản hồi “chưa có thông tin” dù user đang hỏi một intent khác. User nhận ra sai khi câu trả lời không khớp với điều mình hỏi hoặc bot không giúp tiến thêm bước nào. Recovery là bấm `Thử cách tra cứu khác` hoặc `Gặp nhân viên hỗ trợ`.* |
| Correction - user sửa | User sửa bằng cách nào? Data đó đi vào đâu? | *User đổi cách diễn đạt, chọn lại quick reply đúng hơn, hoặc hand-off sang người thật. Những session này được lưu thành correction/failure log để team cập nhật intent map, câu hỏi làm rõ và fallback policy.* |

---

## 3. Eval metrics + threshold

**Optimize precision hay recall?** ☑ Precision · ☐ Recall

Tại sao?  
*Trong domain hàng không, trả lời sai nhưng nghe có vẻ đúng nguy hiểm hơn nhiều so với việc bot nói “tôi chưa đủ thông tin”. Nếu bot bịa hoặc áp sai policy, user có thể mất tiền, lỡ chuyến hoặc chuẩn bị sai giấy tờ. Vì vậy cần ưu tiên precision và fallback sớm khi không chắc.*

Nếu sai ngược lại thì chuyện gì xảy ra?  
*Nếu tối ưu recall quá mức, bot sẽ cố trả lời dù không chắc, làm tăng tỷ lệ hallucination hoặc kéo user vào flow sai. Nếu precision quá cao mà recall quá thấp, bot sẽ chuyển người thật quá sớm và giá trị tự động hóa không còn nhiều.*

| Metric | Threshold | Red flag (dừng khi) |
|--------|-----------|---------------------|
| *Intent routing accuracy* | *>= 85%* | *< 75% trong 2 tuần test liên tiếp* |
| *Loop rate (bị lặp flow/phản hồi)* | *<= 10% session* | *> 20% session* |
| *Deflection Rate* | *>= 35%* | *< 20% sau giai đoạn pilot* |
| *CSAT* | *>= 3.8/5* | *< 3.0/5 trong 1 tháng* |

---

## 4. Top 3 failure modes

| # | Trigger | Hậu quả | Mitigation |
|---|---------|---------|------------|
| 1 | *User hỏi có nhiều biến số trong một câu: tuyến bay + thời gian + ưu đãi + ngữ cảnh trước đó* | *Bot bắt sai intent hoặc trả lời theo policy chung, user phải tự đoán câu trả lời có áp dụng không* | *Tách intent trước, hỏi làm rõ bằng quick replies, không trả lời đầy đủ nếu thiếu biến quan trọng* |
| 2 | *Bot giữ nhầm ngữ cảnh cũ và kéo user quay lại flow tra cứu trước đó* | *User bị mắc kẹt trong dead-end, thấy bot “ngu” hoặc spam* | *Session memory có TTL ngắn, cho phép reset flow, thêm nút `Thử cách tra cứu khác`* |
| 3 | *Policy/giá thay đổi nhưng knowledge base hoặc nguồn tra cứu chưa cập nhật* | *Bot đưa thông tin cũ, gây mất niềm tin hoặc rủi ro vận hành* | *Ràng buộc chỉ trả lời từ nguồn chính thức, timestamp nguồn dữ liệu, và fallback sang trang tra cứu/live agent nếu nguồn chưa chắc chắn* |

---

## 5. ROI 3 kịch bản

> Các số dưới đây là giả định order-of-magnitude để ước lượng nhanh cho hackathon.

|   | Conservative | Realistic | Optimistic |
|---|-------------|-----------|------------|
| **Assumption** | *3,000 session/ngày, deflection 20%* | *8,000 session/ngày, deflection 35%* | *15,000 session/ngày, deflection 50%* |
| **Cost** | *~$300/tháng hạ tầng + vận hành* | *~$800/tháng* | *~$1,800/tháng* |
| **Benefit** | *Giảm tải một phần cho CSKH giờ cao điểm, giảm câu hỏi lặp* | *Giảm đáng kể volume FAQ lặp, tăng tốc xử lý cho tổng đài* | *Giảm tải mạnh cho CSKH, tăng self-service completion, tạo cơ hội upsell dịch vụ phụ trợ* |
| **Net** | *Dương nhẹ* | *Khả thi rõ ràng* | *Rất hấp dẫn nếu adoption cao* |

**Kill criteria:** *Nếu loop rate cao kéo dài, CSAT dưới 3.0/5, hoặc deflection rate dưới 15-20% sau pilot dù đã tinh chỉnh nhiều vòng, nên dừng hoặc thu hẹp scope về các intent đơn giản hơn.*

---

## 6. Mini AI spec (1 trang)

NEO 2.0 là phiên bản cải thiện của chatbot hỗ trợ khách hàng Vietnam Airlines theo hướng “web-first support agent” cho các nhu cầu tra cứu thông tin trước chuyến bay. Bài toán sản phẩm không phải là làm một AI biết mọi thứ, mà là giảm ma sát trong những câu hỏi lặp có volume cao như giá vé, thông tin chuyến bay, tra cứu theo mã đặt chỗ/số vé, đồng thời tránh để user bị kẹt trong các flow sai hoặc phản hồi lặp.
G
Về bản chất sản phẩm, NEO 2.0 thiên về augmentation hơn là automation. Với các truy vấn tra cứu cơ bản, bot có thể trả lời gần như tự động nếu đã có dữ liệu đúng từ nguồn chính thức. Nhưng với những nghiệp vụ nhạy cảm như thay đổi booking, hoàn vé, hoặc các case có nhiều biến số áp dụng, bot chỉ nên đóng vai trò hướng dẫn: hỏi làm rõ, tóm tắt policy, đưa link chính xác, và chuyển sang nhân viên hỗ trợ khi rủi ro tăng cao.

Về kỹ thuật, phiên bản hackathon không cần xây full agent phức tạp. Core hợp lý nhất là hybrid architecture gồm: intent classifier, session memory ngắn hạn, retrieval từ knowledge base chính thức, API/tool lookup cho các dữ liệu tra cứu được, và một response layer để diễn giải kết quả theo ngôn ngữ tự nhiên. Nếu dùng LLM thì LLM chỉ nên là lớp hiểu câu hỏi và diễn đạt câu trả lời, không phải nguồn chân lý. Source of truth luôn là policy chính thức, dữ liệu tra cứu chuyến bay và booking.

Về chất lượng, hệ thống cần optimize precision trước recall. Trong hàng không, “trả lời sai nhưng tự tin” nguy hiểm hơn “không chắc nên xin thêm dữ liệu hoặc chuyển người thật”. UX lý tưởng là: nếu bot tự tin thì trả lời ngắn gọn, có link nguồn và bước tiếp theo; nếu bot không chắc thì hỏi làm rõ bằng quick replies; nếu bot có dấu hiệu lệch intent hoặc loop thì chủ động cho user thoát sang một flow khác hoặc hand-off sang nhân viên.

Rủi ro lớn nhất của NEO 2.0 không phải latency, mà là trust erosion: bot lặp phản hồi, giữ nhầm ngữ cảnh, áp sai policy, hoặc không cho user một lối thoát rõ ràng. Vì vậy, ngoài intent accuracy, sản phẩm phải theo dõi loop rate, hand-off rate, re-ask rate và CSAT. Đây là các chỉ số phản ánh trải nghiệm thật hơn là chỉ nhìn accuracy đơn thuần.

Data flywheel của sản phẩm hoạt động như sau: user đặt câu hỏi -> bot xử lý và trả lời hoặc hand-off -> session được log lại với các tín hiệu như hỏi lại, bấm gặp nhân viên, đổi cách diễn đạt, bỏ dở giữa chừng -> team dùng các session lỗi để cập nhật intent map, câu hỏi làm rõ và fallback flow -> bot xử lý tốt hơn ở các lượt sau -> nhiều user hoàn tất self-service hơn -> hệ thống thu được thêm dữ liệu hội thoại thực tế để tiếp tục cải thiện. Giá trị lớn nhất ở đây là hiểu được các “support flow” thực tế của khách hàng Vietnam Airlines, chứ không chỉ có một chatbot trả lời FAQ.

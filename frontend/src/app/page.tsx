"use client";

import { useState, useRef, useEffect } from 'react';

type Message = {
  id: string;
  role: 'user' | 'bot';
  content: string;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'bot',
      content: 'Xin chào, tôi là NEO - Trợ lý ảo của Vietnam Airlines. Rất vui được hỗ trợ bạn!\n\nDưới đây là một số việc tôi có thể giúp:\n Tra cứu chuyến bay: Kiểm tra tình trạng, giờ cất/hạ cánh (VD: Chuyến VN123 có đúng giờ không?)\n Quản lý vé: Xem lại thông tin đặt chỗ cá nhân.\n Tra cứu giá vé: Tham khảo giá tốt nhất giữa các chặng.\n Quy định hành lý: Tư vấn chi tiết số kiện, số cân xách tay/ký gửi cho từng hạng vé.\n\nBạn cần tôi hỗ trợ vấn đề gì?'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput('');
    
    // Thêm tin nhắn user vào UI
    const newUserMsg: Message = { id: Date.now().toString(), role: 'user', content: userMsg };
    setMessages(prev => [...prev, newUserMsg]);
    setIsLoading(true);

    try {
      // Gọi API FastAPI
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });

      if (!res.ok) throw new Error('Network response was not ok');
      
      const data = await res.json();
      
      let botText = '';
      if (data.error) {
        botText = `Lỗi Backend: ${data.error}`;
      } else {
        botText = data.response;
      }
      
      // Thêm tin nhắn bot vào UI
      const newBotMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: botText || 'Xin lỗi, hệ thống đang gặp gián đoạn nhỏ.'
      };
      
      setMessages(prev => [...prev, newBotMsg]);
    } catch (error) {
      console.error('Error fetching chat:', error);
      setMessages(prev => [
        ...prev, 
        { id: Date.now().toString(), role: 'bot', content: 'Có lỗi xảy ra khi kết nối máy chủ. Vui lòng kiểm tra xem Backend (FastAPI) đã được bật chưa.' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Render markdown đơn giản (chỉ bôi đậm và xuống dòng)
  const renderMessageContent = (content: string) => {
    // Chuyển \n thành <br/>, đổi **text** thành <strong>text</strong> (đơn giản hoá markdown)
    const formatted = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br/>');
        
    return <div dangerouslySetInnerHTML={{ __html: formatted }} />;
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="avatar">✈️</div>
        <div>
          <h1>NEO Assistant</h1>
          <p>Vietnam Airlines AI Agent</p>
        </div>
      </div>

      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            {renderMessageContent(msg.content)}
          </div>
        ))}
        
        {isLoading && (
          <div className="message bot">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="message-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Hỏi về chuyến bay, hành lý, giá vé..."
          className="message-input"
          disabled={isLoading}
        />
        <button type="submit" disabled={!input.trim() || isLoading} className="send-button">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </form>
    </div>
  );
}

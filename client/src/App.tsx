import React, { useState, useRef, useEffect } from 'react';
import QueryInput from './components/QueryInput';
import ChatMessages from './components/ChatMessages';
import { sendChatMessage } from './services/api';
import { Message } from './types/chat';
import { useChatScroll } from './hooks/useChatScroll';

const simulateTyping = (
  text: string,
  onProgress: (partial: string) => void,
  onComplete: () => void,
  speedMs: number = 15
) => {
  let index = 0;
  const interval = setInterval(() => {
    if (index < text.length) {
      onProgress(text.slice(0, index + 1));
      index++;
    } else {
      clearInterval(interval);
      onComplete();
    }
  }, speedMs);

  return () => clearInterval(interval);
};

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  useChatScroll(messages, !loading);

  const handleSendMessage = async (query: string) => {
    if (loading) return;

    // Добавляем сообщение пользователя
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Заглушка для ответа ассистента
    const assistantMessageId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      },
    ]);

    setLoading(true);
    abortControllerRef.current = new AbortController();

    try {
      const fullAnswer = await sendChatMessage(query);

      // Симуляция печатания
      let currentContent = '';
      const stopTyping = simulateTyping(
        fullAnswer,
        (partial) => {
          currentContent = partial;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId ? { ...msg, content: partial } : msg
            )
          );
        },
        () => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId ? { ...msg, content: currentContent } : msg
            )
          );
        }
      );

      return () => stopTyping();
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Запрос отменён');
        return;
      }

      console.error('Ошибка:', error);
      const errorMessage = error.message || '❌ Не удалось связаться с бэкендом';
      
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId ? { ...msg, content: errorMessage } : msg
        )
      );
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleClearChat = () => {
    setMessages([]);
  };

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return (
    <div
      style={{
        backgroundColor: '#0F121A',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        fontFamily: 'Inter, -apple-system, sans-serif',
      }}
    >
      {/* Хедер */}
      <div
        style={{
          padding: '16px 32px',
          backgroundColor: 'rgba(20, 25, 40, 0.9)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <h1
          style={{
            fontSize: '24px',
            margin: 0,
            background: 'linear-gradient(90deg, #6C75FF, #9E4BFF)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontWeight: 'bold',
          }}
        >
          AI Land Analyzer
        </h1>
        {messages.length > 0 && (
          <button
            onClick={handleClearChat}
            style={{
              background: 'rgba(108, 117, 255, 0.15)',
              border: '1px solid rgba(108, 117, 255, 0.3)',
              color: '#6C75FF',
              padding: '6px 12px',
              borderRadius: '8px',
              fontSize: '14px',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(108, 117, 255, 0.2)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(108, 117, 255, 0.15)')}
          >
            Очистить чат
          </button>
        )}
      </div>

      {/* Основной контейнер чата */}
      <div
        style={{
          maxWidth: '800px',
          width: '100%',
          margin: '0 auto',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          height: 'calc(100vh - 140px)', // ← Вычисляем высоту с учетом хедера и футера
        }}
      >
        <ChatMessages messages={messages} isLoading={loading} />
        
        {/* КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: блок ввода прилипает к низу */}
        <div style={{ marginTop: 'auto' }}>
          <QueryInput onSubmit={handleSendMessage} disabled={loading} />
        </div>
      </div>

      {/* Футер с дисклеймером */}
      <div
        style={{
          padding: '16px 32px',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          textAlign: 'center',
          color: '#666',
          fontSize: '13px',
          position: 'relative', // ← Чтобы не перекрывался
        }}
      >
        Бэкенд: http://localhost:8000 • Данные: Государственный кадастр недвижимости РБ
      </div>
    </div>
  );
}
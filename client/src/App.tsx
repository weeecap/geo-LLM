// App.tsx
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
  speedMs: number = 10
): (() => void) => {
  console.log('⌨️ Начинаем печать, длина текста:', text.length);
  
  let index = 0;
  const interval = setInterval(() => {
    if (index < text.length) {
      index++;
      const partial = text.slice(0, index);
      onProgress(partial);
    } else {
      clearInterval(interval);
      console.log('✅ Печать завершена');
      onComplete();
    }
  }, speedMs);

  return () => {
    console.log('🛑 Остановка печати');
    clearInterval(interval);
  };
};

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const stopTypingRef = useRef<(() => void) | null>(null); // ← храним функцию остановки

  useChatScroll(messages, !loading);

  const handleSendMessage = async (query: string) => {
    if (loading || !query.trim()) return;

    console.log('📤 Отправка запроса:', query);

    // 1. Сообщение пользователя
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      message: query.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // 2. Пустое сообщение ассистента
    const assistantMessageId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMessageId,
        role: 'assistant',
        message: '',
        timestamp: new Date(),
      },
    ]);

    setLoading(true);
    abortControllerRef.current = new AbortController();

    try {
      // 3. Получаем ответ
      const fullAnswer = await sendChatMessage(query, abortControllerRef.current?.signal);
      console.log('📥 Получен ответ, длина:', fullAnswer.length);

      if (!fullAnswer || fullAnswer.trim() === '') {
        throw new Error('Пустой ответ от сервера');
      }

      let currentContent = '';

      // 4. Запускаем печать
      stopTypingRef.current = simulateTyping(
        fullAnswer,
        (partial) => {
          currentContent = partial;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, message: partial }
                : msg
            )
          );
        },
        () => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, message: currentContent }
                : msg
            )
          );
          // 🔧 Печать завершена — сбрасываем ссылку
          stopTypingRef.current = null;
        }
      );
      
      // 🔧 УБРАЛИ finally с stopTyping()! Печать должна завершиться сама.
      
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('🔄 Запрос отменён');
        // При отмене тоже останавливаем печать
        if (stopTypingRef.current) {
          stopTypingRef.current();
          stopTypingRef.current = null;
        }
        return;
      }

      console.error('❌ Ошибка:', error);
      const errorMessage = error.message || '❌ Не удалось получить ответ';

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, message: errorMessage }
            : msg
        )
      );
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
      // 🔧 НЕ вызываем stopTyping() здесь!
    }
  };

  const handleClearChat = () => {
    // 🔧 Остановить печать при очистке
    if (stopTypingRef.current) {
      stopTypingRef.current();
      stopTypingRef.current = null;
    }
    setMessages([]);
    console.log('🗑️ Чат очищен');
  };

  // 🔧 Остановка при размонтировании компонента
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (stopTypingRef.current) {
        stopTypingRef.current();
        stopTypingRef.current = null;
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
      <header
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
            }}
          >
            Очистить чат
          </button>
        )}
      </header>

      <main
        style={{
          maxWidth: '800px',
          width: '100%',
          margin: '0 auto',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          height: 'calc(100vh - 140px)',
        }}
      >
        <ChatMessages messages={messages} isLoading={loading} />
        <div style={{ marginTop: 'auto' }}>
          <QueryInput onSubmit={handleSendMessage} disabled={loading} />
        </div>
      </main>

      <footer
        style={{
          padding: '16px 32px',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          textAlign: 'center',
          color: '#666',
          fontSize: '13px',
        }}
      >
        Бэкенд: http://localhost:8000 • Данные: Государственный кадастр недвижимости РБ
      </footer>
    </div>
  );
}
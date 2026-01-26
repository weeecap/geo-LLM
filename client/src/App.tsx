import React, { useState } from 'react';
import QueryInput from './components/QueryInput';
import ResponsePanel from './components/ResponsePanel';
import { sendChatMessage } from './services/api';

const simulateTyping = (text: string, onChar: (char: string) => void, speedMs: number = 15) => {
  let index = 0;
  const interval = setInterval(() => {
    if (index < text.length) {
      onChar(text[index]);
      index++;
    } else {
      clearInterval(interval);
    }
  }, speedMs);
};

export default function App() {
  const [input, setInput] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!input.trim()) return;

    setLoading(true);
    setResponse('');

    try {
      const fullAnswer = await sendChatMessage(input);
      // Имитируем streaming
      simulateTyping(fullAnswer, (char) => {
        setResponse(prev => prev + char);
      });
    } catch (error: any) {
      console.error('Ошибка:', error);
      setResponse(
        error.message ||
        '❌ Не удалось связаться с бэкендом. Проверьте, запущен ли он на порту 8000.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        backgroundColor: '#0F121A',
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '20px',
        boxSizing: 'border-box',
        fontFamily: 'Inter, -apple-system, sans-serif',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '600px',
          backgroundColor: 'rgba(30, 35, 48, 0.7)',
          backdropFilter: 'blur(10px)',
          borderRadius: '16px',
          padding: '32px',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <h1
          style={{
            textAlign: 'center',
            fontSize: '28px',
            marginBottom: '8px',
            background: 'linear-gradient(90deg, #6C75FF, #9E4BFF)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontWeight: 'bold',
          }}
        >
          AI Land Suitability Analyzer
        </h1>
        <p style={{ textAlign: 'center', color: '#aaa', fontSize: '14px', marginBottom: '24px' }}>
          Опишите желаемый участок на естественном языке
        </p>

        <QueryInput
          input={input}
          onInputChange={setInput}
          onSubmit={handleSubmit}
          disabled={loading}
        />

        <ResponsePanel response={response} />

        {/* Подсказка */}
        <div
          style={{
            marginTop: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: '#888',
          }}
        >
          <span>💡</span>
          <span>
            Бэкенд должен быть запущен на{' '}
            <code style={{ backgroundColor: '#1e293b', padding: '2px 6px', borderRadius: '4px' }}>
              http://localhost:8000
            </code>
          </span>
        </div>
      </div>
    </div>
  );
}
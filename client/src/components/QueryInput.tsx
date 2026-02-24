import React, { useState, KeyboardEvent } from 'react';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  disabled: boolean;
}

const QueryInput: React.FC<QueryInputProps> = ({ onSubmit, disabled }) => {
  const [input, setInput] = useState('');

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (trimmed && !disabled) {
      onSubmit(trimmed);
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div
      style={{
        // Убран внешний контейнер — теперь всё в одном блоке
        display: 'flex',
        gap: '12px',
        backgroundColor: 'rgba(40, 45, 60, 0.7)',
        border: '1px solid rgba(108, 117, 255, 0.3)', // ← Синяя обводка
        borderRadius: '24px', // ← Скругление всех 4 углов
        padding: '8px 16px',
        alignItems: 'center',
        backdropFilter: 'blur(10px)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
      }}
    >
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Опишите желаемый участок на естественном языке..."
        rows={1}
        disabled={disabled}
        style={{
          flex: 1,
          backgroundColor: 'transparent',
          border: 'none',
          color: '#fff',
          fontSize: '16px',
          resize: 'none',
          outline: 'none',
          maxHeight: '120px',
          overflowY: 'auto',
          lineHeight: 1.5,
          borderRadius: '18px',
          padding: '8px 12px',
        }}
        onInput={(e) => {
          const el = e.target as HTMLTextAreaElement;
          el.style.height = 'auto';
          el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
        }}
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !input.trim()}
        style={{
          width: '40px',
          height: '40px',
          borderRadius: '12px',
          background: disabled || !input.trim()
            ? 'rgba(108, 117, 255, 0.3)'
            : 'linear-gradient(to right, #3b82f6, #8b5cf6)',
          border: 'none',
          color: '#fff',
          cursor: disabled || !input.trim() ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.2s',
        }}
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M22 2L11 13" />
          <path d="M22 2L15 22L11 13L2 9L22 2Z" />
        </svg>
      </button>
    </div>
  );
};

export default QueryInput;
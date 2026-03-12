// components/Message.tsx
import React from 'react';
import { Message as MessageType } from '../types/chat';

interface MessageProps {
  message: MessageType;
}

const Message: React.FC<MessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  // 🔧 УБРАЛИ проверку на пустоту! Иначе текст не появится во время печати
  
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '16px',
        maxWidth: '100%',
      }}
    >
      <div
        style={{
          maxWidth: '85%',
          backgroundColor: isUser ? '#2563eb' : '#2a2a2a',
          color: isUser ? '#fff' : '#e0e0e0',
          borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
          padding: '14px 18px',
          lineHeight: 1.6,
          whiteSpace: 'pre-line',
          wordBreak: 'break-word',
          fontSize: '15px',
          // 🔧 Добавили минимальную высоту, чтобы блок не схлопывался
          minHeight: message.message ? 'auto' : '44px',
        }}
      >
        {message.message || (isUser ? '' : 'Печатает...')}
      </div>
    </div>
  );
};

export default Message;
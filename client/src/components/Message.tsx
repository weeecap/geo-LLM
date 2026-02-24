import React from 'react';
import { Message as MessageType } from '../types/chat';

interface MessageProps {
  message: MessageType;
}

const Message: React.FC<MessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
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
          whiteSpace: 'pre-line', // ← КЛЮЧЕВОЕ: переносы строк работают!
          wordBreak: 'break-word',
          fontSize: '15px',
        }}
      >
        {message.content}
      </div>
    </div>
  );
};

export default Message;
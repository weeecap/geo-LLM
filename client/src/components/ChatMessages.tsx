import React from 'react';
import Message from './Message';
import { Message as MessageType } from '../types/chat';

interface ChatMessagesProps {
  messages: MessageType[];
  isLoading: boolean;
}

const ChatMessages: React.FC<ChatMessagesProps> = ({ messages, isLoading }) => {
  if (messages.length === 0) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '200px',
          color: '#666',
          textAlign: 'center',
          padding: '20px',
        }}
      >
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>💬</div>
        <p style={{ fontSize: '18px', fontWeight: '500' }}>
          Задайте вопрос о земельных участках
        </p>
        <p style={{ color: '#888', marginTop: '8px' }}>
          Например: «Покажи участки с электричеством площадью 0.25 га»
        </p>
      </div>
    );
  }

  return (
    <div
      data-chat-scroll
      style={{
        flex: 1,
        overflowY: 'auto',
        maxHeight: 'calc(100vh - 280px)',
        paddingRight: '8px',
        marginBottom: '24px',
      }}
    >
      {messages.map((msg) => (
        <Message key={msg.id} message={msg} />
      ))}
      
      {isLoading && (
        <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '16px' }}>
          <div
            style={{
              backgroundColor: '#2a2a2a',
              borderRadius: '16px 16px 16px 4px',
              padding: '14px 18px',
              color: '#888',
            }}
          >
            <div style={{ display: 'flex', gap: '4px' }}>
              <span style={{ animation: 'pulse 1.5s infinite' }}>•</span>
              <span style={{ animation: 'pulse 1.5s 0.3s infinite' }}>•</span>
              <span style={{ animation: 'pulse 1.5s 0.6s infinite' }}>•</span>
            </div>
            <style>{`
              @keyframes pulse {
                0%, 100% { opacity: 0.3; }
                50% { opacity: 1; }
              }
            `}</style>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatMessages; 
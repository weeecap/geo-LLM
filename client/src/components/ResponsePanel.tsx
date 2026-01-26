// src/components/ResponsePanel.tsx
import React from 'react';

interface ResponsePanelProps {
  response: string;
}

const ResponsePanel: React.FC<ResponsePanelProps> = ({ response }) => {
  if (!response) return null;

  return (
    <div
      style={{
        marginTop: '24px',
        padding: '16px',
        backgroundColor: 'rgba(40, 45, 60, 0.7)',
        borderRadius: '12px',
        border: '1px solid rgba(108, 117, 255, 0.3)',
        color: '#e0e0e0',
        fontSize: '15px',
        lineHeight: 1.6,
        maxHeight: '300px',
        overflowY: 'auto',
      }}
    >
      <strong style={{ color: '#6C75FF', display: 'block', marginBottom: '8px' }}>
        Ответ ИИ:
      </strong>
      <div>{response}</div>
    </div>
  );
};

export default ResponsePanel;
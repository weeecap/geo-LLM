import React from 'react';

interface ResponseDisplayProps {
  response: string;
}

const ResponseDisplay: React.FC<ResponseDisplayProps> = ({ response }) => {
  if (!response) return null;

  return (
    <div
      style={{
        marginTop: '24px',
        padding: '16px',
        backgroundColor: '#252525',
        borderRadius: '10px',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        color: '#ccc',
      }}
    >
      <strong>Response:</strong>
      <div style={{ marginTop: '8px' }}>{response}</div>
    </div>
  );
};

export default ResponseDisplay;
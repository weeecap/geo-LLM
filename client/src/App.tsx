import React, { useState } from 'react';
import QueryInput from './components/QueryInput';

export default function App() {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!input.trim()) return;

    setLoading(true);
    try {
      // Replace this with your actual API call later
      await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate delay
      alert('✅ Request sent to backend. Check console for response.');
    } catch (error) {
      console.error(error);
      alert('❌ Error: Could not reach backend.');
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
          maxWidth: '80≠0px',
          backgroundColor: 'rgba(30, 35, 48, 0.7)',
          backdropFilter: 'blur(10px)',
          borderRadius: '16px',
          padding: '32px',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
          border: '2px solid rgba(255, 255, 255, 0.1)',
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
        <p
          style={{
            textAlign: 'center',
            color: '#aaa',
            fontSize: '14px',
            marginBottom: '24px',
          }}
        >
          Describe your ideal plot in natural language
        </p>

        <QueryInput
          input={input}
          onInputChange={setInput}
          onSubmit={handleSubmit}
          disabled={loading}
        />

        <div
          style={{
            marginTop: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: '#888',
          }}
        >
          <span>💡</span>
          <span>
            Make sure your FastAPI backend is running on{' '}
            <code
              style={{
                backgroundColor: '#1e293b',
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '12px',
              }}
            >
              http://localhost:8000
            </code>
          </span>
        </div>
      </div>
    </div>
  );
}
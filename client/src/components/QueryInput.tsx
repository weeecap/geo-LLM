import React from 'react';

interface QueryInputProps {
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
}

const QueryInput: React.FC<QueryInputProps> = ({ input, onInputChange, onSubmit, disabled }) => {
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(); }}>
      <textarea
        value={input}
        onChange={(e) => onInputChange(e.target.value)}
        placeholder="e.g., Quiet residential area near schools in Logoysk, >500 m²..."
        rows={4}
        style={{
          width: '100%',
          padding: '16px',
          marginBottom: '16px',
          backgroundColor: 'rgba(40, 45, 60, 0.7)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '10px',
          color: '#fff',
          fontSize: '16px',
          resize: 'vertical',
          outline: 'none',
          transition: 'border-color 0.2s',
        }}
        onFocus={(e) => (e.target.style.borderColor = 'rgba(108, 117, 255, 0.5)')}
        onBlur={(e) => (e.target.style.borderColor = 'rgba(255, 255, 255, 0.1)')}
      />
      <button
        type="submit"
        disabled={disabled}
        style={{
          width: '100%',
          padding: '12px',
          background: disabled
            ? 'linear-gradient(to right, #333, #444)'
            : 'linear-gradient(to right, #3b82f6, #8b5cf6)',
          color: '#fff',
          border: 'none',
          borderRadius: '10px',
          fontSize: '16px',
          fontWeight: '600',
          cursor: disabled ? 'not-allowed' : 'pointer',
          transition: 'opacity 0.2s, transform 0.1s',
        }}
        onMouseDown={(e) => !disabled && (e.currentTarget.style.transform = 'scale(0.98)')}
        onMouseUp={(e) => !disabled && (e.currentTarget.style.transform = 'scale(1)')}
      >
        {disabled ? 'Analyzing...' : 'Analyze'}
      </button>
    </form>
  );
};

export default QueryInput;
// src/main.tsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles/global.css'; // ← Add this line

createRoot(document.getElementById('root')!).render(<App />);
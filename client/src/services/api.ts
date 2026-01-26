// src/services/api.ts
export const sendChatMessage = async (userMessage: string): Promise<string> => {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages: [{ role: 'user', content: userMessage.trim() }]
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Ошибка сервера');
  }

  return await response.text();
};
export interface BackendChatResponse {
  response?: string;
  message?: string;
  text?: string;
  [key: string]: any;
}

export const sendChatMessage = async (
  query: string, 
  signal?: AbortSignal
): Promise<string> => {
  try {
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: query }),
      signal, // ← Поддержка отмены запроса
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      throw new Error(`HTTP ${response.status}: ${response.statusText} ${errorText}`);
    }

    const data = (await response.json()) as BackendChatResponse;
    console.log('Ответ от бэкенда:', data);
    
    // 🔧 Извлекаем строку из любого формата ответа
    const result = 
      typeof data.response === 'string' ? data.response :
      typeof data.message === 'string' ? data.message :
      typeof data.text === 'string' ? data.text :
      String(data.response || data.message || data.text || '');
    
    console.log('Возвращаем строку длиной:', result.length);
    return result;
    
  } catch (error) {
    console.error('Ошибка в API:', error);
    throw error;
  }
};
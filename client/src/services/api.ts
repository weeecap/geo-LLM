import axios from 'axios';
import { ChatResponse } from '../types';

const API_BASE_URL = 'http://localhost:8000';

export const sendChatMessage = async (query: string) => {
  const response = await axios.post<ChatResponse>(`${API_BASE_URL}/chat`, {
    messages: query,
  });
  return response.data.response;
};
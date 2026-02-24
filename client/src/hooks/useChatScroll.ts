import { useEffect } from 'react';

export const useChatScroll = (messages: any[], shouldScroll: boolean) => {
  useEffect(() => {
    if (shouldScroll) {
      const scrollable = document.querySelector('[data-chat-scroll]');
      if (scrollable) {
        scrollable.scrollTop = scrollable.scrollHeight;
      }
    }
  }, [messages, shouldScroll]);
};
// src/components/Chat/Chat.tsx
import React, { useState, useRef, useEffect } from 'react';
import { useUserProfile } from '@/hooks/useUserProfile';
import { fetchWithAuth } from '@/utils/api';
import { Button } from '../components/ui/button';
import { Send, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/useToast';
import { ScrollArea } from '../components/ui/scroll-area';
import Sidebar from '@/components/Layout/Sidebar';
import { GlobalLoading } from '@/components/Layout/GlobalLoading';
import Header from '@/components/Layout/Header';
import { useLocation } from 'react-router-dom';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  iso?: string;
};

const Chat: React.FC = () => {
  const { userProfile } = useUserProfile();
  const { toast } = useToast();
  const location = useLocation();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

    // Load initial state
  useEffect(() => {
    const savedSession = localStorage.getItem('chatSession');
    const initialSessionId = localStorage.getItem('currentChatSession');

    if (savedSession) {
      const { sessionId: savedId, messages: savedMsgs } = JSON.parse(savedSession);
      setSessionId(savedId);
      setMessages(savedMsgs);
    } else if (initialSessionId) {
      setSessionId(initialSessionId);
    }
  }, []);

  // Save to localStorage
  useEffect(() => {
    if (messages.length > 0 || sessionId) {
      localStorage.setItem('chatSession', JSON.stringify({
        sessionId,
        messages
      }));
    }
  }, [messages, sessionId]);

  // Load backend history
  useEffect(() => {
    const loadHistory = async () => {
      if (!sessionId) return;

      try {
        const response = await fetchWithAuth(`/chat/${sessionId}/history`);
        if (!response.ok) return;

        const data = await response.json();
        setMessages(data.messages);
      } catch (error) {
        console.error('Failed to load history:', error);
      }
    };

    loadHistory();
  }, [sessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => scrollToBottom(), [messages]);

  // Handle initial message from navigation state
  useEffect(() => {
    const initialMessage = location.state?.initialMessage;
    if (initialMessage && !messages.length) {
      setInputMessage(initialMessage);
      setTimeout(() => handleSend(), 100);
    }
  }, [location.state]);

  const handleSend = async (message?: string) => {
    const finalMessage = message || inputMessage.trim();
    if (!finalMessage || isLoading) return;

    const newMessage: Message = { role: 'user', content: finalMessage };
    setMessages(prev => [...prev, newMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetchWithAuth('/chat/', {
        method: 'POST',
        body: JSON.stringify({
          message: finalMessage,
          session_id: sessionId || undefined,
        }),
      });

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';

      const processStream = async () => {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n').filter(line => line.trim());

          for (const line of lines) {
            try {
              const data = JSON.parse(line);
              if (data.complete) {
                setSessionId(data.session_id);
                setIsLoading(false);
              } else if (data.response) {
                assistantMessage += data.response;
                setMessages(prev => {
                  const last = prev[prev.length - 1];
                  if (last?.role === 'assistant') {
                    return [...prev.slice(0, -1), { ...last, content: assistantMessage }];
                  }
                  return [...prev, { role: 'assistant', content: assistantMessage }];
                });
              }
            } catch (error) {
              console.error('Error parsing chunk:', error);
            }
          }
        }
      };

      await processStream();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to send message', variant: 'destructive' });
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar role={userProfile?.role || 'GUEST'} />

      <main className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <Header userName={userProfile?.name} />

          <GlobalLoading />

          <div className="flex flex-col h-[calc(100vh-180px)] border  rounded-lg bg-card">
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-3xl p-4 rounded-lg border border-primary  ${
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-foreground'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">
                        {message.content.split(/(\*\*.*?\*\*)/g).map((part, index) => {
                          const isBold = part.startsWith('**') && part.endsWith('**');
                          if (isBold) {
                            return <strong key={index}>{part.slice(2, -2)}</strong>;
                          }
                          return part;
                        })}
                      </p>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="max-w-3xl p-4 rounded-lg bg-muted text-foreground">
                      <Loader2 className="animate-spin h-5 w-5" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            <div className="flex gap-2 p-4 border-t border-muted">
              <input
                ref={inputRef}
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask about ISO certifications..."
                className="flex-1 p-2 rounded-lg border border-primary bg-card text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                disabled={isLoading}
              />
              <Button onClick={() => handleSend()} disabled={isLoading}>
                {isLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Chat;
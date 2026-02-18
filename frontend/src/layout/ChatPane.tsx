import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Send, Bot, User, Loader2, MessageSquare, X } from 'lucide-react';
import { chatApi } from '@/api/client';
import { useAppStore } from '@/store/appStore';
import { cn, generateId, formatDateTime } from '@/lib/utils';
import type { ChatMessage } from '@/types';

export function ChatPane() {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { 
    messages, 
    addMessage, 
    chatLoading, 
    setChatLoading,
    chatOpen,
    toggleChat
  } = useAppStore();

  const chatMutation = useMutation({
    mutationFn: (message: string) => chatApi.sendMessage(message),
    onSuccess: (response) => {
      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: response.data.data.response,
        actions: response.data.data.actions,
        timestamp: new Date().toISOString(),
      };
      addMessage(assistantMessage);
      setChatLoading(false);
    },
    onError: () => {
      const errorMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      };
      addMessage(errorMessage);
      setChatLoading(false);
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || chatLoading) return;

    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    addMessage(userMessage);
    setInput('');
    setChatLoading(true);

    chatMutation.mutate(userMessage.content);
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <aside
      className={cn(
        'bg-white border-l border-gray-200 flex flex-col transition-all duration-300',
        chatOpen ? 'w-96' : 'w-0 overflow-hidden'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-primary-600" />
          <h3 className="font-semibold text-gray-800">Assistant</h3>
        </div>
        <button
          onClick={toggleChat}
          className="p-1 hover:bg-gray-200 rounded-lg transition-colors"
        >
          <X className="w-4 h-4 text-gray-500" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex gap-3',
              message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
            )}
          >
            <div
              className={cn(
                'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
                message.role === 'user' ? 'bg-primary-100' : 'bg-gray-100'
              )}
            >
              {message.role === 'user' ? (
                <User className="w-4 h-4 text-primary-600" />
              ) : (
                <Bot className="w-4 h-4 text-gray-600" />
              )}
            </div>
            <div
              className={cn(
                'max-w-[80%] rounded-lg px-4 py-2',
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-800'
              )}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              
              {/* Actions */}
              {message.actions && message.actions.length > 0 && (
                <div className="mt-2 space-y-1">
                  {message.actions.map((action, idx) => (
                    <div
                      key={idx}
                      className={cn(
                        'text-xs px-2 py-1 rounded',
                        action.success
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      )}
                    >
                      {action.success ? '✓' : '✗'} {action.message}
                    </div>
                  ))}
                </div>
              )}
              
              <span className="text-xs opacity-50 mt-1 block">
                {formatDateTime(message.timestamp)}
              </span>
            </div>
          </div>
        ))}
        
        {chatLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center">
              <Bot className="w-4 h-4 text-gray-600" />
            </div>
            <div className="bg-gray-100 rounded-lg px-4 py-2 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm text-gray-600">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            disabled={chatLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || chatLoading}
            className="px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2 text-center">
          Press Enter to send
        </p>
      </form>
    </aside>
  );
}

// Chat toggle button for when chat is closed
export function ChatToggle() {
  const { toggleChat, chatOpen } = useAppStore();
  
  if (chatOpen) return null;
  
  return (
    <button
      onClick={toggleChat}
      className="fixed bottom-4 right-4 w-12 h-12 bg-primary-600 text-white rounded-full shadow-lg hover:bg-primary-700 transition-colors flex items-center justify-center z-50"
    >
      <MessageSquare className="w-5 h-5" />
    </button>
  );
}

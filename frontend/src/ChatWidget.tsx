import { useState, useRef, useEffect } from 'react';
import { IoChatbubbles, IoClose, IoSend } from 'react-icons/io5';

const API_BASE_URL = 'http://localhost:8000/api';

export const ChatWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<{ user: string, ai: string }[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to the latest message.
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    const userMessage = question;

    // Show user message and a "thinking" bubble immediately.
    setMessages(prev => [...prev, { user: userMessage, ai: '...' }]);
    setQuestion('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/rag/queryTranscripts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage })
      });
      const data = await response.json();
      
      // Update the "thinking" bubble with the real answer.
      setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1].ai = data.answer;
          return newMessages;
      });
    } catch (error) {
        console.error("RAG query failed:", error);
        setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1].ai = "Sorry, I couldn't connect to the AI. Please try again.";
            return newMessages;
        });
    } finally {
        setIsLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button onClick={() => setIsOpen(true)} className="fixed bottom-8 right-8 bg-green-500 text-white p-4 
      rounded-full shadow-lg text-3xl hover:bg-green-600 transition-transform hover:scale-110">
        <IoChatbubbles />
      </button>
    );
  }

  return (
    <div className="fixed bottom-8 right-8 w-96 h-[600px] bg-gray-800 rounded-xl shadow-2xl flex flex-col">
      <div className="p-4 bg-gray-900 flex justify-between items-center rounded-t-xl">
        <h3 className="font-bold text-lg">Ask Me Anything!</h3>
        <button onClick={() => setIsOpen(false)} className="text-2xl hover:text-gray-400"><IoClose /></button>
      </div>
      <div className="flex-grow p-4 overflow-y-auto space-y-4">
        {messages.map((msg, i) => (
          <div key={i}>
            <p className="flex justify-end"><span className="bg-green-500 text-black max-w-xs p-3 rounded-lg 
            inline-block">{msg.user}</span></p>
            <p className="flex justify-start mt-2"><span className="bg-gray-700 max-w-xs p-3 rounded-lg 
            inline-block">{msg.ai}</span></p>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-700 flex">
        <input type="text" value={question} onChange={e => setQuestion(e.target.value)} className="flex-grow 
        bg-gray-700 rounded-l-lg p-2 focus:outline-none" placeholder="Ask about transcripts..." />
        <button type="submit" disabled={isLoading} className="bg-green-500 p-2 rounded-r-lg text-2xl text-black 
        disabled:bg-gray-500"><IoSend /></button>
      </form>
    </div>
  );
};

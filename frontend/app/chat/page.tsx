// frontend/app/chat/page.tsx
"use client";
import { useState, useRef, useEffect } from "react";

type Message = {
  sender: "user" | "bot";
  text: string;
  sources?: string[];
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "bot",
      text: "Hello! 👋 I am your Bank of Maharashtra Loan Assistant. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMessage: Message = { sender: "user", text: input };
    setMessages((msgs) => [...msgs, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: input }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response from server.");
      }

      const data = await response.json();
      setMessages((msgs) => [
        ...msgs,
        {
          sender: "bot",
          text: data.answer,
          sources: data.source_chunks,
        },
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        {
          sender: "bot",
          text: "Sorry, I couldn't process your request. Please try again.",
        },
      ]);
    }
    setLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") sendMessage();
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-blue-100">
      <header className="py-6 bg-blue-900 text-white text-center shadow-lg">
        <h1 className="text-3xl font-bold tracking-tight">Bank of Maharashtra Loan Assistant</h1>
        <p className="text-blue-200 mt-2">Ask me anything about loans, eligibility, documents, and more!</p>
      </header>
      <main className="flex-1 flex flex-col max-w-2xl mx-auto w-full p-4">
        <div className="flex-1 overflow-y-auto bg-white rounded-lg shadow p-6 mb-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`mb-4 flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              <div className={`max-w-[75%]`}>
                <div
                  className={`px-4 py-2 rounded-2xl shadow ${
                    msg.sender === "user"
                      ? "bg-blue-600 text-white rounded-br-none"
                      : "bg-gray-100 text-gray-900 rounded-bl-none"
                  }`}
                >
                  {msg.text}
                </div>
                {msg.sender === "bot" && msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 text-xs text-gray-500">
                    <span className="font-semibold">Sources:</span>
                    <ul className="list-disc ml-5">
                      {msg.sources.map((src, i) => (
                        <li key={i} className="break-words">{src}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div className="flex gap-2">
          <input
            className="flex-1 border border-blue-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            type="text"
            placeholder="Type your question about loans..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button
            className="bg-blue-700 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-800 disabled:opacity-50"
            onClick={sendMessage}
            disabled={loading}
          >
            {loading ? (
              <span className="animate-spin inline-block w-5 h-5 border-2 border-white border-t-blue-700 rounded-full"></span>
            ) : (
              "Send"
            )}
          </button>
        </div>
      </main>
      <footer className="py-4 text-center text-blue-900 text-sm bg-blue-50 border-t">
        &copy; {new Date().getFullYear()} Bank of Maharashtra Loan Assistant
      </footer>
    </div>
  );
}

// frontend/app/chat/page.tsx
"use client";
import { useState, useRef, useEffect } from "react";
import { FaUserCircle, FaRobot, FaPaperPlane, FaPaperclip } from "react-icons/fa";
import ReactMarkdown from "react-markdown";

type Message = {
  sender: "user" | "bot";
  text: string;
  sources?: string[];
  timestamp?: string; // Add timestamp
};

function fixBullets(text: string) {
  // Add a newline before each dash or star that is used as a bullet (not already at line start)
  return text.replace(/(\s)?([*-])\s+/g, '\n$2 ');
}

function cleanMarkdown(text: string) {
  // Remove stray bullets and fix list formatting
  let cleaned = text;

  // Replace "•" with nothing (or with a newline if needed)
  cleaned = cleaned.replace(/•/g, '');

  // Ensure every "- " or "* " at the start of a line is a real list item
  cleaned = cleaned.replace(/(\S)\s*-\s+/g, '$1\n- '); // Add newline before dash if missing

  // Remove empty list items
  cleaned = cleaned.replace(/^- *$/gm, '');

  // Optionally, fix double newlines
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n');

  return cleaned.trim();
}

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
    const userMessage: Message = { 
      sender: "user", 
      text: input, 
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    };
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
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
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
    <div className="h-screen flex flex-col bg-gradient-to-br from-blue-100 to-blue-200 overflow-hidden">
      {/* Header */}
      <header className="py-6 bg-blue-900 text-white text-center shadow-lg flex flex-col items-center">
        <div className="flex items-center gap-3 justify-center">
          <img src="/file.svg" alt="Logo" className="w-10 h-10" />
          <h1 className="text-3xl font-bold tracking-tight">Bank of Maharashtra Loan Assistant</h1>
        </div>
        <p className="text-blue-200 mt-1 text-sm font-light">Ask me anything about loans, eligibility, documents, and more!</p>
      </header>

      {/* Centered Chat Card */}
      <main className="flex-1 flex flex-col items-center justify-center">
        <div className="
          flex flex-col
          rounded-2xl
          shadow-2xl
          w-full
          max-w-lg
          sm:max-w-xl
          md:max-w-2xl
          bg-white/80
          backdrop-blur-xl
          h-[80vh]
          overflow-hidden
          mx-2
        ">
            {/* Scrollable messages area */}
            <div className="flex-1 overflow-y-auto p-6">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`mb-4 flex items-end ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                >
                  {/* Avatar */}
                  {msg.sender === "bot" && (
                    <FaRobot className="text-blue-700 w-8 h-8 mr-2" />
                  )}
                  {msg.sender === "user" && (
                    <FaUserCircle className="text-gray-400 w-8 h-8 ml-2 order-2" />
                  )}

                  {/* Message Bubble */}
                  <div className={`max-w-[75%]`}>
                    <div
                      className={`px-4 py-2 rounded-2xl shadow transition-all duration-200 ${
                        msg.sender === "user"
                          ? "bg-blue-600 text-white rounded-br-none"
                          : "bg-gray-100 text-gray-900 rounded-bl-none border border-blue-100"
                      }`}
                    >
                      {msg.sender === "bot" ? (
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown
                            components={{
                              // Optional: customize rendering of certain markdown elements
                              strong: ({node, ...props}) => <strong className="text-blue-700" {...props} />,
                              li: ({node, ...props}) => <li className="ml-2 list-disc" {...props} />,
                              // Add more customizations if needed
                            }}
                          >
                            {cleanMarkdown(msg.text)}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        msg.text
                      )}
                      {/* Timestamp (optional, static for now) */}
                      {msg.timestamp && (
                        <div className="text-xs text-gray-400 mt-1 text-right">
                          {msg.timestamp}
                        </div>
                      )}
                    </div>
                    {/* Sources */}
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
            {/* Input area (always at the bottom) */}
            <div className="flex gap-2 items-center bg-white/90 rounded-b-2xl shadow px-3 py-2">
              <button
                className="text-blue-400 hover:text-blue-600 transition"
                title="Attach file (coming soon)"
                disabled
              >
                <FaPaperclip size={20} />
              </button>
              <input
                className="flex-1 border-none bg-transparent px-2 py-2 focus:outline-none text-gray-800"
                type="text"
                placeholder="Type your question about loans..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
              />
              <button
                className="bg-gradient-to-r from-blue-600 via-cyan-400 to-fuchsia-600 text-white p-3 rounded-full font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200 flex items-center justify-center"
                onClick={sendMessage}
                disabled={loading}
                aria-label="Send"
              >
                {loading ? (
                  <span className="animate-spin inline-block w-5 h-5 border-2 border-white border-t-blue-700 rounded-full"></span>
                ) : (
                  <FaPaperPlane size={18} />
                )}
              </button>
            </div>
          </div>
        </main>

      {/* Footer */}
      <footer className="py-3 text-center text-blue-900 text-xs bg-blue-50 border-t font-light">
        &copy; {new Date().getFullYear()} Bank of Maharashtra Loan Assistant<br />
        Developed by Saurabh Wani
      </footer>
    </div>
  );
}

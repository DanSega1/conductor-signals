import { type FormEvent, useRef, useState } from "react";
import { api } from "../api/client";
import ChatMessage from "../components/ChatMessage";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "I can answer questions about your observability data. What would you like to know?",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollDown = () => bottomRef.current?.scrollIntoView({ behavior: "smooth" });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || sending) return;

    const userMsg: Message = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const res = await api.chat(trimmed);
      const asstMsg: Message = { role: "assistant", content: res.response };
      setMessages((prev) => [...prev, asstMsg]);
    } catch {
      const errMsg: Message = {
        role: "assistant",
        content: "Sorry, I couldn't process that request. The backend may be unavailable.",
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setSending(false);
      setTimeout(scrollDown, 0);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      <h1 className="text-2xl font-bold mb-4 shrink-0">Chat</h1>

      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        {messages.map((m, i) => (
          <ChatMessage key={i} role={m.role} content={m.content} />
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-2xl rounded-bl-md px-4 py-2.5">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0.1s]" />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0.2s]" />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="mt-4 shrink-0 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your data..."
          className="flex-1 bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm outline-none focus:border-blue-500 transition-colors"
          disabled={sending}
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="px-5 py-3 bg-blue-600 rounded-xl text-sm font-medium hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  );
}

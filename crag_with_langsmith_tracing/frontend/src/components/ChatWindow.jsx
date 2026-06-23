import React, { useState, useEffect, useRef } from "react";
import { Send, Sparkles, User, MessageSquare } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { SourceModal } from "./SourceModal";

export const ChatWindow = ({ threadId }) => {
  const { user, apiFetch } = useAuth();
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedSource, setSelectedSource] = useState("");
  const messagesEndRef = useRef(null);

  const fetchHistory = async () => {
    if (!threadId) return;
    setLoadingHistory(true);
    try {
      const data = await apiFetch(`/api/history/${threadId}`);
      const formatted = [];
      (data.history || []).forEach((item) => {
        formatted.push({ sender: "user", text: item.user_query });
        formatted.push({ sender: "ai", text: item.ai_response, sources: [] }); // backend history doesn't store source chunks list, only content
      });
      setMessages(formatted);
    } catch (err) {
      console.error("Failed to load history:", err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [threadId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!query.trim() || sending || !threadId || !user?.id) return;

    const userQueryText = query.trim();
    setQuery("");
    setMessages((prev) => [...prev, { sender: "user", text: userQueryText }]);
    setSending(true);

    try {
      const data = await apiFetch("/api/query", {
        method: "POST",
        body: JSON.stringify({
          query: userQueryText,
          thread_id: threadId,
          user_id: user.id
        })
      });
      setMessages((prev) => [
        ...prev,
        { sender: "ai", text: data.answer, sources: data.sources || [] }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: "ai", text: "Error: " + err.message, sources: [] }
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleSourceClick = (src) => {
    setSelectedSource(src);
    setModalOpen(true);
  };

  if (!threadId) {
    return (
      <div className="welcome-screen">
        <h1>Welcome to cRAG Assistant</h1>
        <p>
          Select an existing conversation from the sidebar or click "New Chat" to start a new corrected RAG session.
        </p>
      </div>
    );
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-header-title">
          <h2>Active Conversation</h2>
        </div>
      </div>

      <div className="chat-messages">
        {loadingHistory ? (
          <div style={{ textAlign: "center", padding: "40px", color: "var(--text-secondary)" }}>
            Loading message logs...
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`message-bubble ${msg.sender}`}>
              <div className="message-avatar">
                {msg.sender === "user" ? <User size={18} /> : <Sparkles size={18} />}
              </div>
              <div className="message-content-wrapper">
                <div className="message-content">
                  {msg.text}
                </div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="sources-container">
                    <div className="sources-title">Cited Sources</div>
                    <div className="sources-list">
                      {msg.sources.map((src, i) => (
                        <div
                          key={i}
                          className="source-tag"
                          title="Click to view full reference"
                          onClick={() => handleSourceClick(src)}
                        >
                          Source chunk {i + 1}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {sending && (
          <div className="message-bubble ai">
            <div className="message-avatar">
              <Sparkles size={18} />
            </div>
            <div className="loading-bubble">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <form onSubmit={handleSend} className="chat-input-form">
          <input
            type="text"
            className="chat-input"
            placeholder="Ask a question..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={sending}
          />
          <button type="submit" className="send-btn" disabled={!query.trim() || sending}>
            <Send size={18} />
          </button>
        </form>
      </div>

      <SourceModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        sourceContent={selectedSource}
      />
    </div>
  );
};

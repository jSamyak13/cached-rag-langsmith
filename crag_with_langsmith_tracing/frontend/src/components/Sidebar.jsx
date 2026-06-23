import React, { useEffect, useState } from "react";
import { MessageSquare, Plus, LogOut, Trash2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export const Sidebar = ({ activeThreadId, onSelectThread, refreshTrigger, setRefreshTrigger }) => {
  const { logout, apiFetch } = useAuth();
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchThreads = async () => {
    try {
      const data = await apiFetch("/api/chat/threads");
      setThreads(data.threads || []);
    } catch (err) {
      console.error("Failed to load threads:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchThreads();
  }, [refreshTrigger]);

  const handleCreateThread = async () => {
    const title = prompt("Enter chat session title:") || "New Chat";
    try {
      const data = await apiFetch(`/api/chat/thread?title=${encodeURIComponent(title)}`, {
        method: "POST",
      });
      setRefreshTrigger(prev => prev + 1);
      onSelectThread(data.thread_id);
    } catch (err) {
      alert("Failed to create thread: " + err.message);
    }
  };

  const handleDeleteThread = async (e, threadId) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat session and its entire history?")) return;
    try {
      await apiFetch(`/api/chat/thread/${threadId}`, {
        method: "DELETE",
      });
      setRefreshTrigger(prev => prev + 1);
      if (activeThreadId === threadId) {
        onSelectThread(null);
      }
    } catch (err) {
      alert("Failed to delete thread: " + err.message);
    }
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-brand">cRAG Agent</span>
      </div>

      <button className="new-chat-btn" onClick={handleCreateThread}>
        <Plus size={16} />
        New Chat
      </button>

      <div className="thread-list">
        {loading ? (
          <div style={{ textAlign: "center", padding: "20px", color: "var(--text-secondary)" }}>Loading chats...</div>
        ) : threads.length === 0 ? (
          <div style={{ textAlign: "center", padding: "20px", color: "var(--text-secondary)", fontSize: "14px" }}>
            No chat history
          </div>
        ) : (
          threads.map((t) => (
            <div
              key={t.thread_id}
              className={`thread-item ${activeThreadId === t.thread_id ? "active" : ""}`}
              onClick={() => onSelectThread(t.thread_id)}
            >
              <div className="thread-info">
                <MessageSquare size={16} />
                <span className="thread-title">{t.title}</span>
              </div>
              <button
                className="delete-thread-btn"
                title="Delete chat"
                onClick={(e) => handleDeleteThread(e, t.thread_id)}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        <div className="user-profile">
          <span>Active Session</span>
        </div>
        <button className="logout-btn" title="Log out" onClick={logout}>
          <LogOut size={18} />
        </button>
      </div>
    </div>
  );
};

import React, { useState } from "react";
import { useAuth } from "./context/AuthContext";
import { Sidebar } from "./components/Sidebar";
import { ChatWindow } from "./components/ChatWindow";

function App() {
  const { user, token, loading, login, signup } = useAuth();
  const [view, setView] = useState("login"); // login, signup, forgot, reset
  const [activeThreadId, setActiveThreadId] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const clearMessages = () => {
    setError("");
    setSuccess("");
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    clearMessages();
    setSubmitting(true);
    try {
      await login(email, password);
      // Clean form states
      setEmail("");
      setPassword("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSignupSubmit = async (e) => {
    e.preventDefault();
    clearMessages();
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      await signup(email, password, fullName);
      setSuccess("Account created successfully! Please log in.");
      setView("login");
      // Clean form states
      setPassword("");
      setConfirmPassword("");
      setFullName("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleForgotPasswordSubmit = async (e) => {
    e.preventDefault();
    clearMessages();
    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Request failed");
      }
      setSuccess("If an account exists, a reset instruction has been sent.");
      setView("reset");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleResetPasswordSubmit = async (e) => {
    e.preventDefault();
    clearMessages();
    if (newPassword !== confirmNewPassword) {
      setError("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: resetToken,
          new_password: newPassword,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Reset failed");
      }
      setSuccess("Password reset successfully! Please log in.");
      setView("login");
      // Clean form states
      setResetToken("");
      setNewPassword("");
      setConfirmNewPassword("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flex: 1, alignItems: "center", justifyContent: "center", minHeight: "100vh", backgroundColor: "var(--bg-primary)" }}>
        <div style={{ color: "var(--accent-primary)", fontSize: "20px", fontWeight: "600" }}>Loading cRAG application...</div>
      </div>
    );
  }

  // If user is authenticated, render the chat application layout
  if (token && user) {
    return (
      <div className="app-container">
        <Sidebar
          activeThreadId={activeThreadId}
          onSelectThread={setActiveThreadId}
          refreshTrigger={refreshTrigger}
          setRefreshTrigger={setRefreshTrigger}
        />
        <ChatWindow threadId={activeThreadId} />
      </div>
    );
  }

  // Non-authenticated flows (Login, Signup, Forgot, Reset)
  return (
    <div className="auth-container">
      {view === "login" && (
        <div className="auth-card">
          <div className="auth-header">
            <h1>Welcome Back</h1>
            <p>Access your isolated cRAG workspace</p>
          </div>
          {error && <div className="auth-error">{error}</div>}
          {success && <div className="auth-success">{success}</div>}
          <form onSubmit={handleLoginSubmit}>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                className="form-input"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                className="form-input"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Logging in..." : "Login"}
            </button>
          </form>
          <div className="auth-footer">
            <p>
              Don't have an account?{" "}
              <span className="auth-link" onClick={() => { setView("signup"); clearMessages(); }}>
                Sign Up
              </span>
            </p>
            <p style={{ marginTop: "10px" }}>
              <span className="auth-link" onClick={() => { setView("forgot"); clearMessages(); }}>
                Forgot Password?
              </span>
            </p>
          </div>
        </div>
      )}

      {view === "signup" && (
        <div className="auth-card">
          <div className="auth-header">
            <h1>Create Account</h1>
            <p>Sign up to query documents securely</p>
          </div>
          {error && <div className="auth-error">{error}</div>}
          <form onSubmit={handleSignupSubmit}>
            <div className="form-group">
              <label>Full Name</label>
              <input
                type="text"
                className="form-input"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                className="form-input"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Password (min 12 characters)</label>
              <input
                type="password"
                className="form-input"
                required
                minLength={12}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Confirm Password</label>
              <input
                type="password"
                className="form-input"
                required
                minLength={12}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Creating Account..." : "Register"}
            </button>
          </form>
          <div className="auth-footer">
            <p>
              Already have an account?{" "}
              <span className="auth-link" onClick={() => { setView("login"); clearMessages(); }}>
                Log In
              </span>
            </p>
          </div>
        </div>
      )}

      {view === "forgot" && (
        <div className="auth-card">
          <div className="auth-header">
            <h1>Forgot Password</h1>
            <p>Enter your email to receive a reset token</p>
          </div>
          {error && <div className="auth-error">{error}</div>}
          <form onSubmit={handleForgotPasswordSubmit}>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                className="form-input"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Sending..." : "Request Reset"}
            </button>
          </form>
          <div className="auth-footer">
            <p>
              Remember password?{" "}
              <span className="auth-link" onClick={() => { setView("login"); clearMessages(); }}>
                Log In
              </span>
            </p>
          </div>
        </div>
      )}

      {view === "reset" && (
        <div className="auth-card">
          <div className="auth-header">
            <h1>Reset Password</h1>
            <p>Enter reset token and your new password</p>
          </div>
          {error && <div className="auth-error">{error}</div>}
          {success && <div className="auth-success">{success}</div>}
          <form onSubmit={handleResetPasswordSubmit}>
            <div className="form-group">
              <label>Reset Token</label>
              <input
                type="text"
                className="form-input"
                required
                placeholder="Paste token here"
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>New Password (min 12 characters)</label>
              <input
                type="password"
                className="form-input"
                required
                minLength={12}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Confirm New Password</label>
              <input
                type="password"
                className="form-input"
                required
                minLength={12}
                value={confirmNewPassword}
                onChange={(e) => setConfirmNewPassword(e.target.value)}
              />
            </div>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Resetting Password..." : "Submit Reset"}
            </button>
          </form>
          <div className="auth-footer">
            <p>
              Back to{" "}
              <span className="auth-link" onClick={() => { setView("login"); clearMessages(); }}>
                Log In
              </span>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

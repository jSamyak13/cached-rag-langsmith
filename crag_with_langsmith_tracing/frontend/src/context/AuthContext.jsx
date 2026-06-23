import React, { createContext, useState, useEffect, useContext } from "react";

const AuthContext = createContext(null);
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("access_token"));
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem("refresh_token"));
  const [loading, setLoading] = useState(true);

  // Decode JWT sub (user_id) safely
  const getUserIdFromToken = (t) => {
    if (!t) return null;
    try {
      const base64Url = t.split(".")[1];
      const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split("")
          .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
          .join("")
      );
      const decoded = JSON.parse(jsonPayload);
      return decoded.sub || null;
    } catch (e) {
      return null;
    }
  };

  useEffect(() => {
    if (token) {
      const userId = getUserIdFromToken(token);
      setUser({ id: userId });
    } else {
      setUser(null);
    }
    setLoading(false);
  }, [token]);

  const handleAuthSuccess = (accessToken, refToken) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refToken);
    setToken(accessToken);
    setRefreshToken(refToken);
    const userId = getUserIdFromToken(accessToken);
    setUser({ id: userId });
  };

  const login = async (email, password) => {
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Login failed");
    }
    handleAuthSuccess(data.access_token, data.refresh_token);
    return data;
  };

  const signup = async (email, password, full_name) => {
    const res = await fetch(`${API_URL}/api/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Signup failed");
    }
    return data;
  };

  const logout = async () => {
    try {
      if (refreshToken) {
        await fetch(`${API_URL}/api/auth/logout`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      }
    } catch (e) {
      console.error("Logout request error:", e);
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      setToken(null);
      setRefreshToken(null);
      setUser(null);
    }
  };

  const refreshSession = async () => {
    if (!refreshToken) {
      logout();
      throw new Error("No refresh token available");
    }
    const res = await fetch(`${API_URL}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    const data = await res.json();
    if (!res.ok) {
      logout();
      throw new Error(data.detail || "Session expired");
    }
    handleAuthSuccess(data.access_token, data.refresh_token);
    return data.access_token;
  };

  // Helper fetch method with JWT headers and automatic token refresh
  const apiFetch = async (endpoint, options = {}) => {
    let currentToken = token;
    
    // Set headers
    const headers = {
      ...options.headers,
      "Content-Type": "application/json",
    };
    if (currentToken) {
      headers["Authorization"] = `Bearer ${currentToken}`;
    }

    let res = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401 && refreshToken) {
      try {
        const newAccessToken = await refreshSession();
        headers["Authorization"] = `Bearer ${newAccessToken}`;
        res = await fetch(`${API_URL}${endpoint}`, {
          ...options,
          headers,
        });
      } catch (err) {
        throw new Error("Session expired, please log in again.");
      }
    }

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Request failed");
    }
    return data;
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, signup, logout, apiFetch, refreshSession }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

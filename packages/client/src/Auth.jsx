import React, { useState } from "react";

function Auth({ setToken }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");


  const AUTH_BASE_URL = "https://poly-place-client-i6hu.vercel.app";

  async function handleRegister(e) {
    e.preventDefault();
    try {
      const res = await fetch(`${AUTH_BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, email }),
      });
      const data = await res.json();
      if (data.success) {
        setIsRegister(false);
      } else {
        alert(data.error || "Registration failed");
      }
    } catch (err) {
      console.error("Register error:", err);
    }
  }

  async function handleLogin(e) {
    e.preventDefault();
    try {
      const res = await fetch(`${AUTH_BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (data.success) {
        // Save token in localStorage
        localStorage.setItem("token", data.token);
        setToken(data.token);
      } else {
        alert(data.error || "Login failed");
      }
    } catch (err) {
      console.error("Login error:", err);
    }
  }

  return (
    <div style={{ margin: "20px" }}>
      <button onClick={() => setIsRegister(false)}>Login</button>
      <button onClick={() => setIsRegister(true)}>Register</button>

      {isRegister ? (
        <div>
          <h2>Register</h2>
          <form onSubmit={handleRegister}>
            <div>
              <label>Username: </label>
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div>
              <label>Email: </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label>Password: </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <button type="submit">Register</button>
          </form>
        </div>
      ) : (
        <div>
          <h2>Login</h2>
          <form onSubmit={handleLogin}>
            <div>
              <label>Username: </label>
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div>
              <label>Password: </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <button type="submit">Login</button>
          </form>
        </div>
      )}
    </div>
  );
}

export default Auth;

import React, { useState } from "react";

function LoginRegister({ setToken }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  async function handleLogin(e) {
    e.preventDefault();
    try {
      const res = await fetch("http://localhost:3000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (data.success) {
        const { token } = data;
        localStorage.setItem("token", token);
        setToken(token);
      } else {
        alert(data.error || "Login failed");
      }
    } catch (err) {
      console.error("Login error:", err);
      alert("Something went wrong");
    }
  }


  return (
    <div style={{ margin: "20px" }}>
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
  );
}

export default LoginRegister;

import React, { useState } from "react";
import Chat from "./Chat";
import Register from "./Register";

function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState(null);

  const handleLogin = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/token/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (data.access) {
        setToken(data.access);
        setUsername(username); // сохраняем имя для чата
      } else {
        alert("Ошибка логина: " + (data.detail || "неизвестно"));
      }
    } catch (err) {
      console.error(err);
      alert("Сервер недоступен");
    }
  };

  if (!token) {
    return (
      <div style={{ padding: "2rem" }}>
        <h2>Вход</h2>
        <input
          type="text"
          placeholder="Имя пользователя"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        /><br/>
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        /><br/>
        <button onClick={handleLogin}>Войти</button>
      </div>
    );
  }

  return <Chat username={username} token={token} />;
}

export default App;
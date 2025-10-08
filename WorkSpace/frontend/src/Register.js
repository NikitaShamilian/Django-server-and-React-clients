import React, { useState } from "react";
import { generateDHKeys } from "./crypto"; // ✅ заменили generateKeyPair → generateDHKeys

function Register({ onRegistered }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = async () => {
    if (!username || !password) {
      alert("Введите имя пользователя и пароль.");
      return;
    }

    try {
      // 🔑 Генерация пары DH‑ключей
      const { public: publicKey, private: privateKey } = await generateDHKeys();

      const res = await fetch("http://127.0.0.1:8000/api/register/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          password,
          public_key: publicKey, // сохраняем публичный ключ на сервере
        }),
      });

      if (!res.ok) {
        alert("Ошибка сети: " + res.status);
        return;
      }

      const data = await res.json();
      if (data.success) {
        alert("✅ Пользователь зарегистрирован!");
        // сохраняем приватный ключ локально; это только демонстрация
        localStorage.setItem("privateKey", JSON.stringify(privateKey, null, 2));
        onRegistered(username);
      } else {
        alert("Ошибка регистрации: " + (data.error || "неизвестно"));
      }
    } catch (err) {
      console.error("[Register error]", err);
      alert("Ошибка регистрации: " + err.message);
    }
  };

  return (
    <div style={{ padding: "1rem", fontFamily: "sans-serif" }}>
      <h2>🔐 Регистрация</h2>

      <div style={{ marginBottom: "0.5rem" }}>
        <input
          type="text"
          placeholder="Имя пользователя"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{
            width: "100%",
            padding: "6px",
            borderRadius: "5px",
            border: "1px solid #ccc",
          }}
        />
      </div>

      <div style={{ marginBottom: "0.5rem" }}>
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{
            width: "100%",
            padding: "6px",
            borderRadius: "5px",
            border: "1px solid #ccc",
          }}
        />
      </div>

      <button
        onClick={handleRegister}
        style={{
          width: "100%",
          padding: "8px",
          borderRadius: "5px",
          border: "none",
          background: "#007BFF",
          color: "white",
          fontWeight: "bold",
          cursor: "pointer",
        }}
      >
        Зарегистрироваться
      </button>
    </div>
  );
}

export default Register;
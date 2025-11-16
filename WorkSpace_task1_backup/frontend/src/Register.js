import React, { useState } from "react";
import { generateKeyPair } from "./crypto";

function Register({ onRegistered }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = async () => {
    if (!username || !password) return;

    const { publicKey, privateKey } = await generateKeyPair();

    const res = await fetch("http://127.0.0.1:8000/api/register/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username,
        password,
        public_key: publicKey,
      }),
    });

    const data = await res.json();
    if (data.success) {
      alert("Пользователь зарегистрирован!");
      localStorage.setItem("privateKey", privateKey);
      onRegistered(username);
    } else {
      alert("Ошибка регистрации: " + (data.error || "неизвестно"));
    }
  };

  return (
    <div style={{ padding: "1rem" }}>
      <h2>Регистрация</h2>
      <input
        type="text"
        placeholder="Имя пользователя"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      /><br />
      <input
        type="password"
        placeholder="Пароль"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      /><br />
      <button onClick={handleRegister}>Зарегистрироваться</button>
    </div>
  );
}

export default Register;
import React, { useState, useEffect } from "react";
import { generateKeyPair, signMessage } from "./crypto";

const Chat = ({ username, token }) => {
  const [socket, setSocket] = useState(null);
  const [receiver, setReceiver] = useState("");
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);
  const [keys, setKeys] = useState(null);

  // генерируем ключи при первом заходе
  useEffect(() => {
    (async () => {
      const { publicKey, privateKey } = await generateKeyPair();
      setKeys({ publicKey, privateKey });
    })();
  }, []);

  // подключение WebSocket
  useEffect(() => {
    if (!keys || !token) return;

    // 🔧 исправлено: без /${username}/
    const ws = new WebSocket(
      `ws://127.0.0.1:8000/ws/chat/?token=${token}`
    );

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setChat((prev) => [...prev, data]);
    };

    ws.onclose = () => {
      console.log("WebSocket closed");
    };

    setSocket(ws);
    return () => ws.close();
  }, [keys, token]);

  // отправка сообщения
  const sendMessage = async () => {
    if (socket && receiver && message && keys) {
      const signature = await signMessage(keys.privateKey, message);

      const payload = {
        receiver,
        content: message,
        signature,
        sender: username,
      };

      // отправляем по WebSocket
      socket.send(JSON.stringify(payload));

      // отправляем на API для логирования/хранения
      try {
        await fetch("http://127.0.0.1:8000/api/send/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify({
            receiver,
            content: message,
            signature,
          }),
        });
      } catch (err) {
        console.error("API send error", err);
      }

      setMessage("");
    }
  };

  return (
    <div style={{ border: "1px solid gray", padding: "1rem", width: "320px" }}>
      <h3>Чат ({username})</h3>
      <input
        type="text"
        placeholder="Кому (username)"
        value={receiver}
        onChange={(e) => setReceiver(e.target.value)}
      />
      <br />
      <input
        type="text"
        placeholder="Сообщение"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />
      <button onClick={sendMessage}>Отправить</button>

      <ul style={{ marginTop: "1rem" }}>
        {chat.map((msg, i) => (
          <li key={i}>
            <b>{msg.sender}:</b> {msg.message || msg.content}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Chat;
import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  signMessage,
  generateDHKeys,
  computeShared,
  encryptMessage,
} from "./crypto";

let socket = null;
let sharedSecret = null;

export default function Chat({ token, username }) {
  const [receiver, setReceiver] = useState("");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const chatRef = useRef(null);

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight });
  }, [messages]);

  const connectWS = useCallback(() => {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING))
      return;
    if (!token) return;

    console.log("[WS] 🔄 connecting...");
    socket = new WebSocket(`ws://127.0.0.1:8000/ws/chat/?token=${token}`);

    socket.onopen = async () => {
      console.log("[WS] ✅ connected");
      setConnected(true);
      try {
        const keys = await generateDHKeys();
        const secret = await computeShared(keys.private, keys.public);
        sharedSecret = secret;
      } catch (e) {
        console.error("[DH init]", e);
      }
    };

    socket.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (!data.content) return;
        setMessages((prev) => {
          const dup = prev.find(
            (m) => m.from === data.sender && m.text === data.content
          );
          return dup ? prev : [...prev, { from: data.sender, text: data.content }];
        });
      } catch (err) {
        console.error("[WS onmessage]", err);
      }
    };

    socket.onclose = () => {
      console.warn("[WS] 🔌 closed");
      setConnected(false);
      sharedSecret = null;
      socket = null;
      setTimeout(connectWS, 2000); // мягкий реконнект
    };

    socket.onerror = () => {
      console.error("[WS] error");
      socket.close();
    };
  }, [token]);

  useEffect(() => {
    connectWS();
    return () => {
      if (socket) socket.close();
    };
  }, [connectWS]);

  const sendMessage = async () => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      alert("WebSocket not connected");
      return;
    }
    if (!receiver || !message) return;

    try {
      if (sharedSecret) {
        const sig = await signMessage(message);
        const enc = await encryptMessage(sharedSecret, message);
        const sharedBase64 = btoa(String.fromCharCode(...sharedSecret));

        socket.send(
          JSON.stringify({
            type: "encrypted-message",
            receiver,
            signature: sig,
            shared_secret: sharedBase64,
            nonce: enc.nonce,
            ciphertext: enc.ciphertext,
            tag: enc.tag,
          })
        );
      } else {
        socket.send(
          JSON.stringify({
            type: "plaintext-message",
            receiver,
            content: message,
          })
        );
      }
      setMessages((p) => [...p, { from: username, text: message }]);
      setMessage("");
    } catch (err) {
      console.error("[sendMessage]", err);
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: "0 auto", fontFamily: "sans-serif" }}>
      <h2>🔐 Secure Chat</h2>
      <div>
        <b>User:</b> {username}
      </div>
      <div style={{ marginBottom: 5 }}>
        <b>Status:</b>{" "}
        <span style={{ color: connected ? "green" : "red" }}>
          {connected ? "Ready" : "Disconnected"}
        </span>
      </div>

      <input
        type="text"
        placeholder="Receiver username"
        value={receiver}
        onChange={(e) => setReceiver(e.target.value)}
        style={{
          width: "100%",
          margin: "10px 0",
          padding: "6px",
          borderRadius: "6px",
          border: "1px solid #ccc",
        }}
      />

      <div
        ref={chatRef}
        style={{
          border: "1px solid #ccc",
          height: 300,
          overflowY: "auto",
          padding: 8,
          marginBottom: 10,
          borderRadius: "6px",
          background: "#f9f9f9",
        }}
      >
        {messages.map((m, i) => {
          const mine = m.from === username;
          return (
            <div
              key={i}
              style={{
                display: "flex",
                justifyContent: mine ? "flex-end" : "flex-start",
                marginBottom: 8,
              }}
            >
              <div
                style={{
                  background: mine ? "#DCF8C6" : "#E6F0FF",
                  color: mine ? "black" : "#003399",
                  borderRadius: "10px",
                  padding: "6px 10px",
                  maxWidth: "70%",
                  textAlign: mine ? "right" : "left",
                }}
              >
                {!mine && (
                  <div
                    style={{
                      color: "#0074D9",
                      fontWeight: "bold",
                      marginBottom: 2,
                    }}
                  >
                    {m.from}
                  </div>
                )}
                {m.text}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ display: "flex", gap: "6px" }}>
        <input
          type="text"
          placeholder="Message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          style={{
            flexGrow: 1,
            padding: "6px",
            borderRadius: "6px",
            border: "1px solid #ccc",
          }}
        />
        <button
          onClick={sendMessage}
          style={{
            width: "90px",
            background: "#007BFF",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
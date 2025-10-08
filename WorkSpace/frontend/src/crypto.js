// crypto.js – Diffie–Hellman + AES‑GCM + подпись

// Генерация пары DH‑ключей (ECDH на Curve25519)
export async function generateDHKeys() {
  const keyPair = await window.crypto.subtle.generateKey(
    { name: "X25519", namedCurve: "X25519" },
    true,
    ["deriveKey", "deriveBits"]
  );
  const publicKeyRaw = await crypto.subtle.exportKey("raw", keyPair.publicKey);
  return {
    public: new Uint8Array(publicKeyRaw),
    private: keyPair.privateKey,
  };
}

// Выработка общего секрета
export async function computeShared(privateKey, peerPublicRaw) {
  const peerKey = await crypto.subtle.importKey(
    "raw",
    peerPublicRaw,
    { name: "X25519", namedCurve: "X25519" },
    false,
    []
  );
  const secret = await crypto.subtle.deriveBits(
    { name: "X25519", public: peerKey },
    privateKey,
    256
  );
  return new Uint8Array(secret);
}

// Подпись сообщения
export async function signMessage(message) {
  const keyPair = await crypto.subtle.generateKey(
    { name: "Ed25519" },
    true,
    ["sign", "verify"]
  );
  const signature = await crypto.subtle.sign(
    { name: "Ed25519" },
    keyPair.privateKey,
    new TextEncoder().encode(message)
  );
  return btoa(String.fromCharCode(...new Uint8Array(signature)));
}

// AES‑GCM шифрование
export async function encryptMessage(sharedSecret, message) {
  const key = await crypto.subtle.importKey(
    "raw",
    sharedSecret,
    { name: "AES-GCM" },
    false,
    ["encrypt"]
  );
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encoded = new TextEncoder().encode(message);
  const cipherBuf = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    key,
    encoded
  );
  const cipher = new Uint8Array(cipherBuf);
  const tag = cipher.slice(-16);
  const ciphertext = cipher.slice(0, -16);
  return {
    nonce: btoa(String.fromCharCode(...iv)),
    ciphertext: btoa(String.fromCharCode(...ciphertext)),
    tag: btoa(String.fromCharCode(...tag)),
  };
}

// AES‑GCM дешифрование
export async function decryptMessage(sharedSecret, nonceB64, ctB64, tagB64) {
  const key = await crypto.subtle.importKey(
    "raw",
    sharedSecret,
    { name: "AES-GCM" },
    false,
    ["decrypt"]
  );
  const iv = Uint8Array.from(atob(nonceB64), (c) => c.charCodeAt(0));
  const ciphertext = Uint8Array.from(atob(ctB64), (c) => c.charCodeAt(0));
  const tag = Uint8Array.from(atob(tagB64), (c) => c.charCodeAt(0));
  const full = new Uint8Array([...ciphertext, ...tag]);
  const plainBuf = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, key, full);
  return new TextDecoder().decode(plainBuf);
}
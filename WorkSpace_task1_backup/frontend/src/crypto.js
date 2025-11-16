// Генерация пары ключей RSA
export async function generateKeyPair() {
  const keyPair = await window.crypto.subtle.generateKey(
    {
      name: "RSASSA-PKCS1-v1_5",
      modulusLength: 2048, // длина ключа
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: "SHA-256",
    },
    true, // ключи извлекаемые (можем экспортировать)
    ["sign", "verify"]
  );

  const publicKey = await window.crypto.subtle.exportKey("spki", keyPair.publicKey);
  const privateKey = await window.crypto.subtle.exportKey("pkcs8", keyPair.privateKey);

  // в PEM формате (удобно хранить на сервере)
  const publicKeyPem = convertToPem(publicKey, "PUBLIC KEY");
  const privateKeyPem = convertToPem(privateKey, "PRIVATE KEY");

  return { publicKey: publicKeyPem, privateKey: privateKeyPem };
}

// перевод ArrayBuffer -> PEM
function convertToPem(buffer, label) {
  const base64 = window.btoa(String.fromCharCode(...new Uint8Array(buffer)));
  let pem = `-----BEGIN ${label}-----\n`;
  for (let i = 0; i < base64.length; i += 64) {
    pem += base64.slice(i, i + 64) + "\n";
  }
  pem += `-----END ${label}-----\n`;
  return pem;
}

// ArrayBuffer -> hex
function arrayBufferToHex(buffer) {
  const byteArray = new Uint8Array(buffer);
  return Array.from(byteArray)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

// Подпись сообщения приватным ключом
export async function signMessage(privateKeyPem, message) {
  // чистим PEM и превращаем в бинарный DER
  const binaryDerString = window.atob(
    privateKeyPem.replace(/-----.* PRIVATE KEY-----/g, "").replace(/\s+/g, "")
  );
  const binaryDer = new Uint8Array(binaryDerString.length);
  for (let i = 0; i < binaryDerString.length; i++) {
    binaryDer[i] = binaryDerString.charCodeAt(i);
  }

  // импорт приватного ключа
  const privateKey = await window.crypto.subtle.importKey(
    "pkcs8",
    binaryDer.buffer,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"]
  );

  // подписываем само сообщение
  const encoder = new TextEncoder();
  const data = encoder.encode(message);
  const signature = await window.crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5",
    privateKey,
    data
  );

  // возвращаем hex-строку
  return arrayBufferToHex(signature);
}
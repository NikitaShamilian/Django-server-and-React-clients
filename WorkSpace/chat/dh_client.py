import socket
import secrets
import struct
from Crypto.Cipher import AES
from Crypto.Hash import SHA256

p = 23
g = 5

def derive_key(shared_secret: int) -> bytes:
    return SHA256.new(str(shared_secret).encode()).digest()

def send_with_length(conn, data: bytes):
    conn.sendall(struct.pack("!I", len(data)))
    conn.sendall(data)

def recv_with_length(conn) -> bytes:
    raw_len = conn.recv(4)
    if not raw_len:
        return b""
    length = struct.unpack("!I", raw_len)[0]
    data = b""
    while len(data) < length:
        packet = conn.recv(length - len(data))
        if not packet:
            break
        data += packet
    return data

def start_client():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 5050))
    print("[*] Подключение к серверу...")

    # DH
    a = secrets.randbelow(p)
    A = pow(g, a, p)

    s.send(str(A).encode())
    B = int(s.recv(1024).decode())

    shared_secret = pow(B, a, p)
    key = derive_key(shared_secret)
    print("[*] Сессионный ключ установлен.")

    # Отправка сообщения
    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    message = "Привет сервер, это клиент!".encode()
    ciphertext, tag = cipher.encrypt_and_digest(message)

    send_with_length(s, nonce)
    send_with_length(s, ciphertext)

    # Получаем ответ сервера
    server_nonce = recv_with_length(s)
    server_ciphertext = recv_with_length(s)

    cipher = AES.new(key, AES.MODE_EAX, nonce=server_nonce)
    response = cipher.decrypt(server_ciphertext)
    print(f"[*] Ответ сервера: {response.decode()}")

    s.close()

if __name__ == "__main__":
    start_client()
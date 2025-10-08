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
    # Отправляем длину (4 байта) + данные
    conn.sendall(struct.pack("!I", len(data)))
    conn.sendall(data)

def recv_with_length(conn) -> bytes:
    # Сначала принимаем 4 байта длины
    raw_len = conn.recv(4)
    if not raw_len:
        return b""
    length = struct.unpack("!I", raw_len)[0]
    # Потом читаем ровно length байт
    data = b""
    while len(data) < length:
        packet = conn.recv(length - len(data))
        if not packet:
            break
        data += packet
    return data

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('localhost', 5050))
    s.listen(1)
    print("[*] Сервер запущен на порту 5050, ожидание клиента...")

    conn, addr = s.accept()
    print(f"[*] Подключен клиент {addr}")

    # DH
    b = secrets.randbelow(p)
    B = pow(g, b, p)

    A = int(conn.recv(1024).decode())
    conn.send(str(B).encode())

    shared_secret = pow(A, b, p)
    key = derive_key(shared_secret)
    print("[*] Сессионный ключ установлен.")

    # Получаем nonce и сообщение
    nonce = recv_with_length(conn)
    ciphertext = recv_with_length(conn)

    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    plaintext = cipher.decrypt(ciphertext)
    print(f"[*] Сообщение от клиента: {plaintext.decode()}")

    # Ответ клиенту
    cipher = AES.new(key, AES.MODE_EAX)
    server_nonce = cipher.nonce
    response = "Привет от сервера! Соединение защищено.".encode()
    ciphertext, tag = cipher.encrypt_and_digest(response)

    send_with_length(conn, server_nonce)
    send_with_length(conn, ciphertext)

    conn.close()
    print("[*] Соединение завершено.")

if __name__ == "__main__":
    start_server()
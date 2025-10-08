from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256

# derive 32‑byte key from hex‑string shared_secret
def derive_aes_key(shared_secret: str) -> bytes:
    if not isinstance(shared_secret, (bytes, bytearray)):
        shared_secret = shared_secret.encode()
    salt = b"salt"
    key = PBKDF2(shared_secret, salt, dkLen=32, count=1000, hmac_hash_module=SHA256)
    return key

def decrypt_message(shared_secret: str, nonce_hex: str, cipher_hex: str, tag_hex: str) -> str:
    key = derive_aes_key(shared_secret)
    nonce = bytes.fromhex(nonce_hex)
    ciphertext = bytes.fromhex(cipher_hex)
    tag = bytes.fromhex(tag_hex)

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode("utf-8", errors="ignore")

def encrypt_message(shared_secret: str, plaintext: str) -> dict:
    key = derive_aes_key(shared_secret)
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
    return {
        "nonce": cipher.nonce.hex(),
        "ciphertext": ciphertext.hex(),
        "tag": tag.hex(),
    }
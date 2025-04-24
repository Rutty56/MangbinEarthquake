import os
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

KEY = os.getenv("ENCRYPTION_KEY", "1234567890123456").encode("utf-8")
IV = b"ThisIsAnIV123456"
DATA_FILE = "registered_users.txt"

def encrypt(text):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    ct_bytes = cipher.encrypt(pad(text.encode("utf-8"), AES.block_size))
    return base64.b64encode(ct_bytes).decode("utf-8")

def decrypt(cipher_text):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    pt = unpad(cipher.decrypt(base64.b64decode(cipher_text)), AES.block_size)
    return pt.decode("utf-8")

def get_registered_users():
    users = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    users.append(decrypt(line.strip()))
                except:
                    continue
    return users

def save_registered_user(user_id):
    users = get_registered_users()
    if user_id in users:
        return False
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(encrypt(user_id) + "\n")
    return True

def remove_registered_user(user_id):
    users = get_registered_users()
    if user_id not in users:
        return False
    users.remove(user_id)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for u in users:
            f.write(encrypt(u) + "\n")
    return True

import os
import requests
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://data.tmd.go.th/api/DailySeismicEvent/v1/?uid=api&ukey=api12345"
REGISTERED_USERS_FILE = "registered_users.txt"

KEY = os.getenv("ENCRYPTION_KEY", "thisisaverysecretkey2025")[:32]
BLOCK_SIZE = 16

def encrypt_data(data):
    cipher = AES.new(KEY.encode('utf-8'), AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode('utf-8'), BLOCK_SIZE))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return iv + ct

def decrypt_data(enc_data):
    iv = base64.b64decode(enc_data[:24])
    ct = base64.b64decode(enc_data[24:])
    cipher = AES.new(KEY.encode('utf-8'), AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), BLOCK_SIZE).decode('utf-8')
    return pt

def fetch_earthquakes():
    try:
        res = requests.get(API_URL)
        if res.status_code == 200:
            data = res.json()
            return data.get("Data", [])
        else:
            print(f"Error fetching data, status code: {res.status_code}")
            return []
    except Exception as e:
        print("Error fetching data:", e)
        return []

def get_recent_earthquakes(data, count=3):
    today = datetime.utcnow().date()
    significant = []
    for quake in data:
        try:
            mag = float(quake.get("Magnitude", 0))
            timestamp = datetime.strptime(quake["DateTime"], "%Y-%m-%dT%H:%M:%S")
            if mag >= 5.0 and timestamp.date() == today:
                significant.append(quake)
        except:
            continue
    return significant[:count]

def get_registered_users():
    if not os.path.exists(REGISTERED_USERS_FILE):
        return []
    with open(REGISTERED_USERS_FILE, "r") as f:
        encrypted_data = f.read()
    try:
        decrypted_data = decrypt_data(encrypted_data)
        return list(set([line.strip() for line in decrypted_data.splitlines() if line.strip()]))
    except Exception as e:
        print("Error decrypting data:", e)
        return []

def save_registered_user(user_id):
    current_data = ""
    if os.path.exists(REGISTERED_USERS_FILE):
        with open(REGISTERED_USERS_FILE, "r") as f:
            encrypted_data = f.read()
        current_data = decrypt_data(encrypted_data)

    current_data += user_id + "\n"

    encrypted_data = encrypt_data(current_data)

    with open(REGISTERED_USERS_FILE, "w") as f:
        f.write(encrypted_data)

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
    encrypted = cipher.iv + ct_bytes
    return base64.b64encode(encrypted).decode('utf-8')

def decrypt_data(enc_data):
    raw = base64.b64decode(enc_data)
    iv = raw[:16]
    ct = raw[16:]
    cipher = AES.new(KEY.encode('utf-8'), AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), BLOCK_SIZE).decode('utf-8')
    return pt

def fetch_earthquakes():
    try:
        res = requests.get(API_URL)
        data = res.json()
        return data.get("Data", [])
    except Exception as e:
        print("Error fetching data:", e)
        return []

def filter_significant_quakes(data, magnitude_threshold=5.0):
    today = datetime.utcnow().date()
    significant = []
    for quake in data:
        try:
            mag = float(quake.get("Magnitude", 0))
            timestamp = datetime.strptime(quake["DateTime"], "%Y-%m-%dT%H:%M:%S")
            if mag >= magnitude_threshold and timestamp.date() == today:
                significant.append(quake)
        except:
            continue
    return significant

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
        try:
            current_data = decrypt_data(encrypted_data)
        except Exception as e:
            print("Error decrypting current data:", e)

    lines = set(current_data.strip().splitlines())
    lines.add(user_id)

    new_data = "\n".join(lines) + "\n"
    encrypted_data = encrypt_data(new_data)

    with open(REGISTERED_USERS_FILE, "w") as f:
        f.write(encrypted_data)

def send_alert(quakes):
    if not quakes:
        return

    from linebot import LineBotApi
    from linebot.models import TextSendMessage
    line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
    user_ids = get_registered_users()

    for quake in quakes:
        msg = (
            f"🌏 แจ้งเตือนแผ่นดินไหว!\n"
            f"สถานที่: {quake.get('Location')}\n"
            f"ขนาด: {quake.get('Magnitude')} ML\n"
            f"วันที่: {quake.get('DateTime')}\n"
        )
        for user_id in user_ids:
            try:
                line_bot_api.push_message(user_id, TextSendMessage(text=msg))
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")

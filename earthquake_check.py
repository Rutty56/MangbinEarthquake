import requests
from datetime import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

API_URL = "https://data.tmd.go.th/api/DailySeismicEvent/v1/?uid=api&ukey=api12345"
REGISTERED_USERS_FILE = "registered_users.txt"  # เปลี่ยนชื่อไฟล์ที่เก็บ user_id

# ขนาดของ key และ block ขนาด 16 bytes สำหรับ AES
KEY = os.getenv("ENCRYPTION_KEY", "thisisaverysecretkey1234")[:32]  # ควรเปลี่ยนเป็นคีย์ที่ปลอดภัยมากขึ้น
BLOCK_SIZE = 16

# เข้ารหัส
def encrypt_data(data):
    cipher = AES.new(KEY.encode('utf-8'), AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode('utf-8'), BLOCK_SIZE))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return iv + ct  # ส่ง iv + ciphertext

# ถอดรหัส
def decrypt_data(enc_data):
    iv = base64.b64decode(enc_data[:24])  # ขนาด iv คือ 16 bytes เข้ารหัสเป็น base64 ใช้ 24 ตัวอักษร
    ct = base64.b64decode(enc_data[24:])
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
        # ถอดรหัสข้อมูล
        decrypted_data = decrypt_data(encrypted_data)
        return list(set([line.strip() for line in decrypted_data.splitlines() if line.strip()]))
    except Exception as e:
        print("Error decrypting data:", e)
        return []

def save_registered_user(user_id):
    # อ่านข้อมูลเก่า
    current_data = ""
    if os.path.exists(REGISTERED_USERS_FILE):
        with open(REGISTERED_USERS_FILE, "r") as f:
            encrypted_data = f.read()
        current_data = decrypt_data(encrypted_data)

    # เพิ่ม user_id ใหม่
    current_data += user_id + "\n"

    # เข้ารหัสข้อมูลใหม่
    encrypted_data = encrypt_data(current_data)

    # เขียนข้อมูลเข้ารหัสลงไฟล์
    with open(REGISTERED_USERS_FILE, "w") as f:
        f.write(encrypted_data)

def send_alert(quakes):
    if not quakes:
        return

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
            line_bot_api.push_message(user_id, TextSendMessage(text=msg))

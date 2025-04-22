import requests

def get_latest_earthquake():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson"
    try:
        response = requests.get(url)
        data = response.json()

        if not data["features"]:
            return "ขณะนี้ไม่มีแผ่นดินไหวที่สำคัญในรอบชั่วโมงที่ผ่านมา"

        quake = data["features"][0]
        place = quake["properties"]["place"]
        mag = quake["properties"]["mag"]

        return f"🌍 แผ่นดินไหวที่ {place}\nขนาด {mag} แมกนิจูด\nข้อมูลจาก USGS"
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการดึงข้อมูลแผ่นดินไหว: {str(e)}"

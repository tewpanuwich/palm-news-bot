import requests
import time
import os
from datetime import datetime


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
LINE_TOKEN     = os.environ.get("LINE_TOKEN")
LINE_USER_ID   = os.environ.get("LINE_USER_ID")

def fetch_and_summarize(max_retries=3):
    today = datetime.now().strftime("%d/%m/%Y")
    prompt = f"""ค้นหาข้อมูลราคาปาล์มน้ำมันสำหรับวันที่ {today} ผ่าน Google Search
ใช้ข้อมูลที่หาได้จาก search results ทั้งหมด แม้ข้อมูลจะไม่ครบหรือไม่ใช่ real-time
ห้ามบอกว่าไม่สามารถเข้าถึงข้อมูลแบบ real-time ได้
หากข้อมูลบางส่วนไม่มี ให้ข้ามหัวข้อนั้นไป แล้วเติมในส่วนที่มีข้อมูล
สรุปให้ครบถ้วนละเอียด แต่ละหัวข้ออธิบายอย่างน้อย 2-3 ประโยค

🌴 ราคาปาล์มน้ำมันวันที่ {today}
──────────────────

💰 ราคารับซื้อปาล์มทะลาย:
(ราคากิโลกรัมละเท่าไหร่ แยกตามภูมิภาคถ้ามี)

🏭 ราคาน้ำมันปาล์มดิบ (CPO):
(ราคาตลาดในประเทศ และราคาตลาดโลก)

📈 แนวโน้มราคา:
(วิเคราะห์ทิศทางราคาระยะสั้น)

⚠️ ปัจจัยที่ต้องจับตา:
(อย่างน้อย 3 ข้อ พร้อมอธิบายว่าทำไมถึงสำคัญ)"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        f"/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {"maxOutputTokens": 3000, "temperature": 0.3}
    }

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 ความพยายามที่ {attempt}/{max_retries}...")
            resp = requests.post(url, json=payload, timeout=60)
            data = resp.json()
            print("status:", resp.status_code)

            candidate = data["candidates"][0]
            finish_reason = candidate.get("finishReason", "")

            if finish_reason not in ["STOP", "MAX_TOKENS"]:
                raise ValueError(f"finishReason: {finish_reason}")

            parts = candidate.get("content", {}).get("parts", [])
            if not parts:
                raise ValueError("parts ว่างเปล่า")

            return parts[0]["text"]

        except Exception as e:
            print(f"⚠️ attempt {attempt} ล้มเหลว: {e}")
            if attempt < max_retries:
                time.sleep(5)

    return "⚠️ ดึงข้อมูลราคาปาล์มไม่สำเร็จ กรุณาลองใหม่"

def send_line_message(text):
    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_TOKEN}"
        },
        json={
            "to": LINE_USER_ID,
            "messages": [{"type": "text", "text": text}]
        },
        timeout=10
    )
    return resp.status_code == 200

def main():
    print("🌴 กำลังดึงราคาปาล์ม...")
    summary = fetch_and_summarize()
    
    if summary.startswith("⚠️"):
        print(summary)
        print("❌ ไม่ส่ง LINE เพราะดึงข้อมูลไม่สำเร็จ")
        return
    
    print(summary)
    print("📲 กำลังส่ง LINE...")
    ok = send_line_message(summary)
    print("✅ ส่งสำเร็จ!" if ok else "❌ ส่งไม่สำเร็จ")

if __name__ == "__main__":
    main()
import asyncio
import logging
import os
import threading
from datetime import datetime
from aiogram import Bot
from flask import Flask
from google import genai
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ቶከኖች እና ከባቢ አየር (Environment Variables)
TELEGRAM_TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

ai_client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Halaale Tech Solutions Automated Bot is running live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# የቴክኖሎጂ እና አውቶሜሽን መረጃዎችን አዘጋጅቶ ወደ ቻናል/ግሩፕ የሚልከው ዋናው ተግባር
async def send_tech_insight_message(time_label: str):
    if not GROUP_CHAT_ID:
        print("ስህተት: GROUP_CHAT_ID አልተሰጠም!")
        return
    
    try:
        prompt = (
            f"Write an engaging, professional, and insightful tech tip, programming advice (Python, Telegram Mini Apps, AI automation), "
            f"or software engineering insight in Amharic (with standard English tech terms) for this time: {time_label}. "
            f"Make it inspiring, beautifully formatted with emojis, clear headings, and actionable for developers or tech enthusiasts. "
            f"Always end the message cleanly with: 'Halaale Tech Solutions 🩷'"
        )

        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        message_text = response.text.strip()
        
        # ወደ ግሩፕ ወይም ቻናል መላክ
        await bot.send_message(chat_id=GROUP_CHAT_ID, text=message_text, parse_mode='Markdown')
        print(f"የ{time_label} ቴክኖሎጂ መረጃ ተልኳል!")
        
    except Exception as e:
        print(f"መልእክት በመላክ ላይ ስህተት ተፈጥሯል: {e}")

async def main() -> None:
    # Flask ሰርቨርን በጀርባ ማስጀመር (ለ Render ዌብ ሰርቨር ቼክ)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Scheduler ማዋቀር
    scheduler = AsyncIOScheduler()
    
    # 1ኛ ሰዓት፦ ማለዳ (07:00 UTC)
    scheduler.add_job(
        send_tech_insight_message, 
        'cron', 
        hour=7, 
        minute=0, 
        args=["Morning Tech Insight (ማለዳ)"]
    )
    
    # 2ኛ ሰዓት፦ ማምሻ (18:00 UTC)
    scheduler.add_job(
        send_tech_insight_message, 
        'cron', 
        hour=18, 
        minute=0, 
        args=["Evening Tech Insight (ማምሻ)"]
    )
    
    scheduler.start()
    print("Halaale Tech Solutions አውቶሜሽን ቦት በቀን ሁለት ጊዜ መረጃዎችን እንዲልክ ተዋቅሯል...")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

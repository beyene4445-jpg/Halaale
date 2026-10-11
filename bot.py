import asyncio
import logging
import os
import random
import threading
from aiogram import Bot
from flask import Flask
from google import genai
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ================= ቶከኖች እና ከባቢ አየር =================
TELEGRAM_TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")   # የChannel ወይም Group ID (-100...)

ai_client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Halaale Tech Solutions Automated Bot is running live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# ============ 🎲 የተለያዩ ርዕሶች (Daily Variety) ============
TECH_TOPICS = [
    "Artificial Intelligence & Machine Learning",
    "Python programming tips & clean code practices",
    "Telegram Mini Apps development",
    "Cybersecurity & online privacy",
    "Space technology & astronomy science",
    "Biotechnology & medical science breakthroughs",
    "Physics, Quantum computing & energy",
    "Robotics & IoT (Internet of Things)",
    "Cloud computing & DevOps automation",
    "Data Science & Big Data analytics",
    "Web & Mobile app development",
    "Blockchain & future of digital finance",
    "Green tech & climate innovation",
    "Neuroscience & brain-computer interfaces",
    "Software engineering career & productivity",
    "Health science and medicine",
    "hitsory of most known scientists like albert,nicolas tesla,...",
    "how the great scientists find and solve complex problems", 
]

TECH_STYLES = [
    "a quick actionable tech tip",
    "a mind-blowing science fact with tech application",
    "a short inspiring tech idea to build",
    "a common mistake developers make and how to fix it",
    "a future-tech concept that will change the world",
    "a productivity hack using technology",
    "a curious science + tech connection",
]


# ============ ዋናው የመልእክት መላኪያ ተግባር ============
async def send_tech_insight_message(time_label: str):
    if not GROUP_CHAT_ID:
        logging.error("ስህተት: GROUP_CHAT_ID አልተሰጠም!")
        return

    # በየሩን የተለያየ ርዕስ እና ስታይል ይመርጣል
    topic = random.choice(TECH_TOPICS)
    style = random.choice(TECH_STYLES)

    try:
        prompt = (
            f"You are writing for a Telegram channel called 'Halaale Tech'. "
            f"Write {style} on the topic: '{topic}' for this time: {time_label}. "
            f"Language: Amharic (with standard English tech terms). "
            f"Tone: motivational, inspiring, attractive, and engaging for tech enthusiasts and developers. "
            f"Style rules:\n"
            f"1. STRICT word count: between 100 and 150 words maximum.\n"
            f"2. Concise and easy to read on a mobile phone.\n"
            f"3. Use emojis to make it visually attractive but do NOT overuse them.\n"
            f"4. Use plain text only — NO markdown symbols like **, *, #, or _.\n"
            f"5. Add one clear actionable takeaway at the end.\n"
            f"6. Draw from science AND technology (any field: AI, space, bio, physics, robotics, etc.).\n"
            f"7. Motivate members to learn, build, or think bigger.\n"
            f"8. End the message EXACTLY with this line on a new line: '(💻) Halaale Tech'"
        )

        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        message_text = response.text.strip()

        # ✅ ማረጋገጫ: መልእክቱ በ (💻) Halaale Tech መጨረሱን አረጋግጥ
        if "(💻) Halaale Tech" not in message_text:
            message_text += "\n\n(💻) Halaale Tech"

        # ወደ Channel / Group መላክ
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message_text,
            disable_web_page_preview=True,
        )
        logging.info(f"✅ የ{time_label} ቴክ ኢንሳይት ተልኳል! (Topic: {topic})")

    except Exception as e:
        logging.error(f"❌ መልእክት በመላክ ላይ ስህተት ተፈጥሯል: {e}")


# ================= ዋናው ፕሮግራም =================
async def main() -> None:
    # Flask ሰርቨርን በጀርባ ማስጀመር (Render ሄልዝ ቼክ)
    threading.Thread(target=run_flask, daemon=True).start()

    scheduler = AsyncIOScheduler()

    # ⏰ 1ኛ ሰዓት — 3:00 UTC (ኢትዮጵያ 6:00 ጠዋት) ☀️
    scheduler.add_job(
        send_tech_insight_message,
        'cron',
        hour=3,
        minute=0,
        args=["Morning Tech Insight (ማለዳ)"],
    )

    # ⏰ 2ኛ ሰዓት — 15:00 UTC (ኢትዮጵያ 6:00 ከሰዓት) 🌙
    scheduler.add_job(
        send_tech_insight_message,
        'cron',
        hour=15,
        minute=0,
        args=["Afternoon Tech Insight (ከሰዓት)"],
    )

    scheduler.start()
    logging.info("🚀 Halaale Tech Solutions ቦት ተጀመረ — 3:00 UTC እና 15:00 UTC ላይ ይልካል።")

    # 🧪 የሙከራ መስመር — ከተረጋገጠ በኋላ አጥፋው
    # await send_tech_insight_message("Test Run 🧪")

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    asyncio.run(main())

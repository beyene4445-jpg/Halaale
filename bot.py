import asyncio
import logging
import os
import random
import threading
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from flask import Flask
from google import genai
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ================= ቶከኖች እና ከባቢ አየር =================
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


# ============ 🎲 ርዕሶች እና ስታይሎች ============
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
    "History of famous scientists like Albert Einstein, Nikola Tesla",
    "How great scientists solved complex problems",
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


# ============ 🔄 Topic Rotator (no-repeat engine) ============
class TopicRotator:
    """
    ሁሉንም ርዕሶች አንድ ጊዜ ጠቅልሎ ከጨረሰ በኋላ ብቻ ይደግማል።
    የአሁኑ ርዕስ ከቀዳሚው ጋር እንዳይመሳሰል ያረጋግጣል።
    """
    def __init__(self, topics: list):
        self.topics = list(topics)
        self.pool = []
        self.last_topic = None

    def next_topic(self) -> str:
        if not self.pool:
            self.pool = self.topics[:]
            random.shuffle(self.pool)
            if self.last_topic and self.pool[0] == self.last_topic and len(self.pool) > 1:
                self.pool[0], self.pool[1] = self.pool[1], self.pool[0]
        topic = self.pool.pop(0)
        self.last_topic = topic
        return topic

    def remaining(self) -> int:
        return len(self.pool)


rotator = TopicRotator(TECH_TOPICS)


# ============ ⏰ ቀጣዩን ሰዓት ማስላት ============
def get_next_schedule_times():
    """ቀጣዩን የ2:59 UTC እና 14:49 UTC ሰዓት ይመልሳል።"""
    now = datetime.now(timezone.utc)
    candidates = []
    # 2:59 UTC እና 14:49 UTC
    schedule_hours_minutes = [(2, 59), (14, 49)]
    for h, m in schedule_hours_minutes:
        for d in (0, 1):
            t = (now + timedelta(days=d)).replace(
                hour=h, minute=m, second=0, microsecond=0
            )
            if t > now:
                candidates.append(t)
    candidates.sort()
    return candidates  # [next1, next2]


def format_eat(dt_utc: datetime) -> str:
    """UTC ን ወደ ኢትዮጵያ ሰዓት (EAT, UTC+3) ይቀይራል።"""
    eat = dt_utc + timedelta(hours=3)
    return eat.strftime("%I:%M %p").lstrip("0")


def format_utc(dt_utc: datetime) -> str:
    return dt_utc.strftime("%H:%M")


# ============ ዋናው የመልእክት መላኪያ ተግባር ============
async def send_tech_insight_message(time_label: str):
    if not GROUP_CHAT_ID:
        logging.error("ስህተት: GROUP_CHAT_ID አልተሰጠም!")
        return

    topic = rotator.next_topic()
    style = random.choice(TECH_STYLES)

    logging.info(f"📝 የተመረጠው ርዕስ: {topic} (ቀሪ: {rotator.remaining()})")

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

        if "(💻) Halaale Tech" not in message_text:
            message_text += "\n\n(💻) Halaale Tech"

        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message_text,
            disable_web_page_preview=True,
        )
        logging.info(f"✅ የ{time_label} ቴክ ኢንሳይት ተልኳል! (Topic: {topic})")

    except Exception as e:
        logging.error(f"❌ መልእክት በመላክ ላይ ስህተት ተፈጥሯል: {e}")


# ============ 🎉 /start Handler ============
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    next_times = get_next_schedule_times()
    n1, n2 = next_times[0], next_times[1]

    user_name = message.from_user.first_name or "ወዳጄ"

    welcome_text = (
        f"🎉 እንኳን ደህና መጡ {user_name}!\n\n"
        f"🚀 Welcome to Halaale Tech Automation Bot\n"
        f"የቴክኖሎጂ እና የሳይንስ ዕውቀት በየቀኑ ወደ ግሩፓችን የሚላክበት አውቶሜሽን ቦት ነኝ።\n\n"
        f"📌 በቀን ሁለት ጊዜ አዲስ ይዘት አቀርባለሁ፦\n"
        f"   ☀️ 2:59 UTC (5:59 ጠዋት በኢትዮጵያ) — Morning Tech Insight\n"
        f"   🌙 14:49 UTC (5:49 ከሰዓት በኢትዮጵያ) — Afternoon Tech Insight\n\n"
        f"⏰ ቀጣዩ መልእክት ይላካል፦\n"
        f"   🟢 በ{format_eat(n1)} EAT ({format_utc(n1)} UTC)\n"
        f"   🟡 ከዛም በ{format_eat(n2)} EAT ({format_utc(n2)} UTC)\n\n"
        f"📚 የምሰጣቸው ዘርፎች (rotating):\n"
        f"   • AI & Machine Learning\n"
        f"   • Python & Software Engineering\n"
        f"   • Telegram Mini Apps\n"
        f"   • Cybersecurity\n"
        f"   • Space & Astronomy\n"
        f"   • Biotech & Medical Science\n"
        f"   • Physics & Quantum Computing\n"
        f"   • Robotics & IoT\n"
        f"   • እና ተጨማሪ...\n\n"
        f"💡 ሁልጊዜም አዲስ እና የተለየ ይዘት እንዲደርስህ በ rotation ስርዓት እሰራለሁ።\n\n"
        f"እንኳን በደህና መጣህ! 🩷\n\n"
        f"(💻) Halaale Tech"
    )

    try:
        await message.answer(welcome_text, disable_web_page_preview=True)
        logging.info(f"👋 /start ከ {user_name} (ID: {message.from_user.id})")
    except Exception as e:
        logging.error(f"❌ /start ላይ ስህተት: {e}")


@dp.message()
async def fallback(message: Message):
    """ሌላ ጽሑፍ ከተላከ — አጭር መመሪያ ይሰጣል።"""
    try:
        await message.answer(
            "🤖 እኔ አውቶሜሽን ቦት ነኝ። /start ብቻ ተጠቀም።\n\n(💻) Halaale Tech"
        )
    except Exception:
        pass


# ================= ዋናው ፕሮግራም =================
async def main() -> None:
    # Flask ሰርቨርን በጀርባ (Render health check)
    threading.Thread(target=run_flask, daemon=True).start()

    # Scheduler
    scheduler = AsyncIOScheduler()

    # ሰዓቶቹ ወደ 2:59 UTC እና 14:49 UTC ተስተካክለዋል
    scheduler.add_job(
        send_tech_insight_message,
        'cron',
        hour=2,
        minute=59,
        args=["Morning Tech Insight (ማለዳ)"],
    )
    scheduler.add_job(
        send_tech_insight_message,
        'cron',
        hour=14,
        minute=49,
        args=["Afternoon Tech Insight (ከሰዓት)"],
    )

    scheduler.start()
    logging.info("🚀 Halaale Tech Bot ተጀመረ — 2:59 UTC እና 14:49 UTC ላይ ይልካል።")
    logging.info("🤖 /start command ዝግጁ ነው።")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    asyncio.run(main())

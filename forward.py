import os, json, asyncio
import re
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION = os.environ["SESSION"]
TARGET = os.environ["TARGET"]
SOURCES = [s.strip() for s in os.environ["SOURCES"].split(",") if s.strip()]

STATE_FILE = "state.json"

PATTERNS = [
    # Pine Script / TradingView
    r"pine[\s\-_]?script", r"\bpine\s?(v5|v6|editor|developer|programmer|coder|coding)\b",
    r"trading\s?view", r"\btv\s(script|indicator)\b", r"//@version",

    # اندیکاتور و استراتژی (انگلیسی)
    r"\bindicators?\b", r"\bstrategy\s?\(", r"\bplot\s?\(",
    r"strategy\s(tester|development|script|coding)",
    r"(custom|coding|programming)\s(indicator|script)",
    r"(indicator|script)\s(developer|development|coding|project)",
    r"\bdebug\s(pine|indicator|script)", r"non[\s\-]?repaint\w*", r"\brepaint\w*",

    # توابع و کلمات فنی پاین
    r"\bta\.\w+", r"request\.security", r"strategy\.(entry|exit|close)",
    r"\balertcondition\b", r"\bplotshape\b", r"\bplotchar\b", r"\bbarstate\.\w+",

    # درخواست پروژه
    r"(need|build|create|looking for|hire)\b.{0,25}\b(indicator|pine|script developer)",

    # فارسی
    r"پاین\s?اسکریپت", r"\bپاین\b", r"تریدینگ\s?ویو",
    r"اندیکاتور", r"استراتژی\s?نویسی",
    r"تبدیل\s(استراتژی|اندیکاتور)", r"کدنویسی\s(اندیکاتور|پاین)",
    r"برنامه\s?نویس\s(پاین|اندیکاتور)", r"پروژه\s(پاین|اندیکاتور)",
]
REGEX = re.compile("|".join(PATTERNS))

def normalize(t):
    t = t.lower()
    t = t.replace("\u200c", " ").replace("\u00a0", " ")   # نیم‌فاصله و فاصله‌ی غیرمعمول
    t = t.replace("ي", "ی").replace("ك", "ک")             # ی و ک عربی
    t = re.sub(r"[\u064b-\u065f\u0640]", "", t)           # اعراب و کشیده
    return re.sub(r"\s+", " ", t)

def match(text):
    return bool(REGEX.search(normalize(text)))
    
def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

async def main():
    state = load_state()
    async with TelegramClient(StringSession(SESSION), API_ID, API_HASH) as client:
        target = await client.get_entity(TARGET)
        for src in SOURCES:
            last_id = state.get(src)
            if last_id is None:
                # اولین اجرا: فقط آخرین آیدی رو ثبت کن، چیزی فوروارد نکن
                latest = await client.get_messages(src, limit=1)
                state[src] = latest[0].id if latest else 0
                continue

            msgs = []
            async for m in client.iter_messages(src, min_id=last_id, reverse=True, limit=200):
                state[src] = max(state[src], m.id)
                if m.message and match(m.message):
                    msgs.append(m)
            if msgs:
                await client.forward_messages(target, msgs)
                print(f"{src}: forwarded {len(msgs)}")

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

asyncio.run(main())

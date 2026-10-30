import os, json, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION = os.environ["SESSION"]
TARGET = os.environ["TARGET"]
SOURCES = [s.strip() for s in os.environ["SOURCES"].split(",") if s.strip()]

STATE_FILE = "state.json"

KEYWORDS = [
    "pine script", "pinescript", "پاین اسکریپت", "پاین",
    "اندیکاتور", "indicator", "tradingview", "تریدینگ ویو",
    "//@version", "ta.", "plot(", "strategy(",
    # Pine Script
    "pine script", "pinescript", "pine-script",
    "pine v5", "pine v6", "pine editor",
    "pine developer", "pine coding",

    # TradingView
    "tradingview", "trading view",
    "tv script", "tv indicator",

    # Indicators
    "indicator", "indicators",
    "custom indicator", "indicator development",
    "indicator developer", "indicator coding",
    "اندیکاتور", "اندیکاتورنویسی",
    "ساخت اندیکاتور", "سفارش اندیکاتور",

    # Strategies
    "strategy development", "trading strategy",
    "strategy tester", "strategy script",
    "strategy coding", "استراتژی نویسی",
    "تبدیل استراتژی",

    # Programming
    "pine developer", "pine programmer",
    "script developer", "script coding",
    "custom script", "coding indicator",
    "programming indicator", "debug pine",
    "pine script error", "pine script developer",

    # Functions and technical terms
    "request.security", "strategy.entry",
    "alertcondition", "plotshape",
    "plotchar", "barstate.",
    "ta.", "math.",

    # Signals and alerts
    "buy sell signals", "signal indicator",
    "trading alerts", "alert system",
    "non-repainting", "repainting",

    # Freelance / projects
    "need an indicator", "build an indicator",
    "create an indicator", "hire pine script",
    "pine script freelancer", "indicator project",
    "اندیکاتور اختصاصی", "کدنویسی اندیکاتور",
    "برنامه نویس پاین", "پروژه پاین اسکریپت",
    "تبدیل اندیکاتور"
]

def match(text):
    t = text.lower()
    return any(k.lower() in t for k in KEYWORDS)

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

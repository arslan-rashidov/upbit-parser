import asyncio
import logging
from datetime import datetime
import os

import requests
from aiogram import Bot

API_URL = "https://api-manager.upbit.com/api/v1/announcements"
PARAMS = {"os": "web", "page": 1, "per_page": 20, "category": "all"}

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

logging.basicConfig(
    filename="error.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

async def poll_news(bot: Bot) -> None:
    last_trade_id = None
    # Set to -3600 so the first "no news" message is sent immediately if needed
    last_no_news = -3600.0
    while True:
        try:
            resp = await asyncio.to_thread(requests.get, API_URL, params=PARAMS, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            notices = data.get("data", {}).get("notices", [])
            notice = notices[0] if notices else None
            if (
                notice
                and notice.get("category") == "Trade"
                and notice.get("id") != last_trade_id
            ):
                last_trade_id = notice.get("id")
                text = (
                    f"{notice.get('title')}\n"
                    f"Sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                await bot.send_message(CHAT_ID, text)
                last_no_news = asyncio.get_event_loop().time()
            else:
                now = asyncio.get_event_loop().time()
                if now - last_no_news >= 3600:
                    last_no_news = now
                    await bot.send_message(
                        CHAT_ID,
                        f"Новостей нет {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    )
        except Exception:
            logging.exception("Error while processing news")
        await asyncio.sleep(1)

async def main() -> None:
    bot = Bot(token=TOKEN)
    try:
        await poll_news(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

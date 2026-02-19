import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

INACTIVITY_DAYS = 0.01
WARNING_HOURS = 24

groups_data = {}

async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type != "supergroup":
        return

    if chat.id not in groups_data:
        groups_data[chat.id] = {
            "last_activity": datetime.utcnow(),
            "members": set(),
            "warned": False
        }

    groups_data[chat.id]["last_activity"] = datetime.utcnow()
    groups_data[chat.id]["members"].add(user.id)

async def check_groups(application):
    while True:
        now = datetime.utcnow()

        for chat_id, data in list(groups_data.items()):
            inactive_time = now - data["last_activity"]

            if inactive_time > timedelta(days=INACTIVITY_DAYS) - timedelta(hours=WARNING_HOURS) and not data["warned"]:
                try:
                    await application.bot.send_message(chat_id, "⚠️ اگر تا ۲۴ ساعت آینده فعالیتی نشود، گروه پاکسازی می‌شود.")
                    data["warned"] = True
                except:
                    pass

            if inactive_time > timedelta(days=INACTIVITY_DAYS):
                try:
                    await application.bot.send_message(chat_id, "🚨 گروه به دلیل ۷ روز عدم فعالیت پاکسازی می‌شود.")

                    for member_id in data["members"]:
                        try:
                            await application.bot.ban_chat_member(chat_id, member_id)
                        except:
                            pass

                    try:
                        link = await application.bot.export_chat_invite_link(chat_id)
                        await application.bot.revoke_chat_invite_link(chat_id, link)
                    except:
                        pass

                    await application.bot.send_message(ADMIN_ID, f"گروه {chat_id} پاکسازی شد.")

                except Exception as e:
                    print(e)

                del groups_data[chat_id]

        await asyncio.sleep(3600)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL, track_activity))

    asyncio.create_task(check_groups(app))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

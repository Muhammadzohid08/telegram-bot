from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

TOKEN = "8522981079:AAGpbyMteHwm9LbKcxrvIu1WaIexQ7koedU"
GROUP_LINK = "https://t.me/+ZkX_C2jC4eE4ZmIy"
REQUIRED_CHANNELS = [
    "@koreannur",
    "@with_Madinee",
    "@Koreya_Ga",
]

# --- Obuna tekshirish funksiyasi ---
async def is_subscribed(app, user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await app.bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "creator", "administrator"]:
                return False
        except Exception as e:
            print(f"Error checking channel {channel}: {e}")
            # Skip channels where we can't check (don't block users)
            continue
    return True

# --- /start komandasi ---
async def start(update, context):
    user_id = update.effective_user.id
    app = context.application

    subscribed = await is_subscribed(app, user_id)

    if subscribed:
        await update.message.reply_text(
            f"🎉 Siz barcha kanallarga obuna bo‘lgansiz!\nMana guruh havolasi:\n{GROUP_LINK}"
        )
    else:
        buttons = [
            [InlineKeyboardButton("📢 koreannur ", url="https://t.me/koreannur")],
            [InlineKeyboardButton("📢 with_Madinee", url="https://t.me/with_Madinee")],
            [InlineKeyboardButton("📢 Koreya_Ga ", url="https://t.me/Koreya_Ga")],
            [InlineKeyboardButton("♻️ Obunani tekshirish", callback_data="check")]
        ]

        await update.message.reply_text(
            "❗ Guruhga kirish uchun quyidagi kanallarga obuna bo‘ling:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# --- “Obunani tekshirish” tugmasi ---
async def check_callback(update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    app = context.application

    subscribed = await is_subscribed(app, user_id)

    if subscribed:
        await query.edit_message_text(
            f"✔️ Obuna tasdiqlandi!\nMana guruh linki:\n{GROUP_LINK}"
        )
    else:
        await query.edit_message_text(
            "❌ Siz hali barcha kanallarga obuna bo‘lmagansiz. Qayta urinib ko‘ring!"
        )

# --- Botni ishga tushirish ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_callback, pattern="check"))

    print("Bot ishga tushdi...")
    try:
        app.run_polling()
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")

if __name__ == "__main__":
    main()

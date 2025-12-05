import os
import json
import uuid
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# --- Configuration ---
TOKEN = "8522981079:AAGpbyMteHwm9LbKcxrvIu1WaIexQ7koedU"
GROUP_LINK = "https://t.me/+hm27nRWAlYdlYzYy"
REQUIRED_CHANNELS = [
    "@koreannur",
    "@with_Madinee",
    "@Koreya_Ga",
    "@StarTopik",
    "@RahmatovaDilfuzaKoreaworld"
]

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")
 
logging.basicConfig(level=logging.INFO)


def load_data():
    if not os.path.exists(DATA_FILE):
        data = {"codes": {}, "invites": {}}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def is_subscribed(app, user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await app.bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "creator", "administrator"]:
                return False
        except Exception as e:
            logging.warning(f"Error checking channel {channel}: {e}")
            # If we can't check a particular channel, treat as not subscribed
            return False
    return True


def generate_code():
    return uuid.uuid4().hex[:8]


async def send_secret_if_eligible(inviter_id, app, data):
    inviter_key = str(inviter_id)
    inv = data.get("invites", {}).get(inviter_key)
    if not inv:
        return
    contributors = inv.get("contributors", [])
    if len(contributors) >= 5 and not inv.get("reward_sent", False):
        try:
            await app.bot.send_message(inviter_id, f"🎉 Siz 5 do'stingizni qo'shdingiz! Mana maxfiy guruh havolasi:\n{GROUP_LINK}")
            inv["reward_sent"] = True
            save_data(data)
        except Exception as e:
            logging.error(f"Failed to send secret link to {inviter_id}: {e}")


async def invite(update, context):
    user = update.effective_user
    user_id = user.id
    app = context.application

    data = load_data()
    inviter_key = str(user_id)

    inv = data.get("invites", {}).get(inviter_key)
    if inv and inv.get("code"):
        code = inv["code"]
    else:
        code = generate_code()
        # store mapping
        data.setdefault("codes", {})[code] = user_id
        data.setdefault("invites", {})[inviter_key] = {
            "code": code,
            "contributors": [],
            "reward_sent": False
        }
        save_data(data)

    # Build referral link
    bot_username = (await app.bot.get_me()).username
    referral = f"https://t.me/{bot_username}?start={code}"

    await update.message.reply_text(
        f"📣 Do'stlaringizni taklif qiling!\nHar bir do'stingiz bot orqali quyidagi havoladan o'tib, kerakli kanallarga qo'shilsa, sizga hisoblanadi.\n\nSizning havolangiz:\n{referral}\n\nSizga 5 to'g'ri qo'shilgan do'stdan so'ng maxfiy guruh havolasi yuboriladi.")


async def start(update, context):
    user = update.effective_user
    user_id = user.id
    app = context.application
    data = load_data()

    # Check for referral code in /start args
    args = context.args if hasattr(context, "args") else []
    if args:
        code = args[0]
        inviter_id = data.get("codes", {}).get(code)
        if inviter_id and inviter_id != user_id:
            inviter_key = str(inviter_id)
            inv = data.setdefault("invites", {}).setdefault(inviter_key, {"code": code, "contributors": [], "reward_sent": False})

            already = user_id in inv.get("contributors", [])
            if already:
                await update.message.reply_text("✅ Siz allaqachon ushbu taklif orqali hisobga olingansiz.")
                return

            subscribed = await is_subscribed(app, user_id)
            if subscribed:
                inv.setdefault("contributors", []).append(user_id)
                save_data(data)
                await update.message.reply_text("Rahmat! Siz kanallarga qo'shildingiz va taklif qilgan foydalanuvchiga hisoblandi.")
                # notify inviter and check reward
                try:
                    await app.bot.send_message(inviter_id, f"📥 Sizning taklifingiz orqali yangi foydalanuvchi qo'shildi. Hozirgi hisob: {len(inv['contributors'])}/5")
                except Exception:
                    pass
                await send_secret_if_eligible(inviter_id, app, data)
                return
            else:
                # Ask the friend to join channels and provide a check button
                buttons = []
                for ch in REQUIRED_CHANNELS:
                    # convert @channel to t.me link
                    name = ch.lstrip("@")
                    buttons.append([InlineKeyboardButton(f"📢 {name}", url=f"https://t.me/{name}")])
                buttons.append([InlineKeyboardButton("♻️ Men qo'shildim — tekshirish", callback_data=f"check_join:{code}")])
                await update.message.reply_text(
                    "❗ Iltimos kerakli kanallarga qo'shiling, so'ng 'Men qo'shildim' tugmasini bosing.",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
                return

    # No referral flow — original subscription check
    subscribed = await is_subscribed(app, user_id)
    if subscribed:
        # NOTE: Do NOT give the secret group link to users who only subscribed.
        # They must invite 5 friends who join the required channels to receive the link.
        await update.message.reply_text(
            "🎉 Siz barcha kanallarga obuna bo‘lgansiz!\n\n" \
            "Ammo bu maxfiy guruhga kirish uchun yetarli emas. Iltimos, 5 do'stingizni botga taklif qiling — " \
            "har bir taklifchi kerakli kanallarga obuna bo'lgach, hisobga olinadi.\n\n" \
            "Do'stlaringizni taklif qilish uchun /invite buyrug'idan foydalaning."
        )
    else:
        buttons = [
            [InlineKeyboardButton("📢 koreannur", url="https://t.me/koreannur")],
            [InlineKeyboardButton("📢 with_Madinee", url="https://t.me/with_Madinee")],
            [InlineKeyboardButton("📢 Koreya_Ga", url="https://t.me/Koreya_Ga")],
            [InlineKeyboardButton("📢 StarTopik", url="https://t.me/StarTopik")],
            [InlineKeyboardButton("📢 RahmatovaDilfuzaKoreaworld", url="https://t.me/RahmatovaDilfuzaKoreaworld")],
            [InlineKeyboardButton("♻️ Obunani tekshirish", callback_data="check")]
        ]

        await update.message.reply_text(
            "❗ Guruhga kirish uchun quyidagi kanallarga obuna bo‘ling:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


async def check_callback(update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    app = context.application

    subscribed = await is_subscribed(app, user_id)

    if subscribed:
        # Don't reveal the secret link here. Tell user to invite friends.
        await query.edit_message_text(
            "✔️ Obuna tasdiqlandi!\n\n" \
            "Ammo maxfiy guruh havolasini olish uchun siz 5 do'stingizni taklif qilishingiz kerak. " \
            "Har bir taklifchi kerakli kanallarga obuna bo'lgach, sizga hisoblanadi.\n\n" \
            "Do'stlarni taklif qilish uchun /invite buyrug'idan foydalaning."
        )
    else:
        await query.edit_message_text(
            "❌ Siz hali barcha kanallarga obuna bo‘lmagansiz. Qayta urinib ko‘ring!"
        )


async def check_join_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    app = context.application
    data = load_data()

    data_payload = query.data  # e.g., "check_join:abcd1234"
    parts = data_payload.split(":", 1)
    if len(parts) != 2:
        await query.edit_message_text("Xato: noto'g'ri so'rov.")
        return
    code = parts[1]
    inviter_id = data.get("codes", {}).get(code)
    if not inviter_id:
        await query.edit_message_text("Xato: taklif kodi topilmadi.")
        return

    inviter_key = str(inviter_id)
    inv = data.setdefault("invites", {}).setdefault(inviter_key, {"code": code, "contributors": [], "reward_sent": False})

    if user_id in inv.get("contributors", []):
        await query.edit_message_text("✅ Siz allaqachon ushbu taklif orqali hisobga olingansiz.")
        return

    subscribed = await is_subscribed(app, user_id)
    if subscribed:
        inv.setdefault("contributors", []).append(user_id)
        save_data(data)
        await query.edit_message_text("Rahmat! Siz kanallarga qo'shildingiz va taklif qilgan foydalanuvchiga hisoblandi.")
        try:
            await app.bot.send_message(inviter_id, f"📥 Yangi foydalanuvchi qo'shildi. Hozirgi hisob: {len(inv['contributors'])}/5")
        except Exception:
            pass
        await send_secret_if_eligible(inviter_id, app, data)
    else:
        await query.edit_message_text("❌ Siz hali barcha kanalarga obuna bo‘lmagansiz. Iltimos, kanallarga qo'shiling va qayta tekshiring.")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("invite", invite))
    app.add_handler(CallbackQueryHandler(check_callback, pattern=r"^check$"))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern=r"^check_join:.*"))

    print("Bot ishga tushdi...")
    try:
        app.run_polling()
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")


if __name__ == "__main__":
    main()

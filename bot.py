import io
import json
import logging
import os
from datetime import datetime, timedelta
from PIL import Image
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Logging ပြင်ဆင်ခြင်း
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Admin ရဲ့ Telegram Username
ADMIN_USERNAME = "@mgnyo5"

BOT_TOKEN = "8997736032:AAGlEvS0GJ-yeK3OVidC36HRQ-8zQcMQDo8"
DATA_FILE = "users.json"

user_images = {}


# User Database ဖတ်ခြင်း/သိမ်းခြင်း
def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)


# User ရဲ့ VIP သက်တမ်း ရှိ/မရှိ စစ်ဆေးခြင်း
def is_vip(user_id, users_db):
    str_id = str(user_id)
    if str_id not in users_db:
        return False

    expiry_str = users_db[str_id].get("expiry_date")
    if not expiry_str:
        return False

    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
    return datetime.now() < expiry_date


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    str_id = str(chat_id)
    users_db = load_users()

    # User ရဲ့ username ကို lowercase နဲ့ သိမ်းဆည်းခြင်း
    username = update.effective_user.username
    uname_clean = username.lower() if username else None

    if str_id not in users_db:
        users_db[str_id] = {
            "name": update.effective_user.full_name,
            "username": uname_clean,
            "free_used": False,
            "expiry_date": None,
        }
    else:
        # Username ပြောင်းသွားပါက database ထဲတွင် အလိုအလျောက် Update လုပ်ပေးခြင်း
        users_db[str_id]["username"] = uname_clean

    save_users(users_db)
    user_images[chat_id] = []

    msg = (
        "မင်္ဂလာပါ။ 16:9 ပုံ ၃ ပုံကို ဒေါင်လိုက် ဆက်ပေးသည့် Bot ဖြစ်ပါသည်။\n\n"
        "✨ Free Trial: ပထမ ၁ ကြိမ် အခမဲ့ ပေါင်းစပ်ခွင့် ရပါမည်။\n"
        "💳 Premium: ၁ လလျှင် ၅,၀၀၀ ကျပ်ဖြင့် အကန့်အသတ်မရှိ သုံးနိုင်ပါသည်။"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    str_id = str(chat_id)
    users_db = load_users()

    username = update.effective_user.username
    uname_clean = username.lower() if username else None

    if str_id not in users_db:
        users_db[str_id] = {
            "name": update.effective_user.full_name,
            "username": uname_clean,
            "free_used": False,
            "expiry_date": None,
        }
    else:
        users_db[str_id]["username"] = uname_clean

    save_users(users_db)

    user_info = users_db[str_id]
    has_vip = is_vip(chat_id, users_db)

    # Free ၁ ခါ သုံးပြီး၍ VIP သက်တမ်းမရှိပါက ငွေလွှဲအချက်အလက်ပြပြီး တားဆီးခြင်း
    if user_info["free_used"] and not has_vip:
        user_uname_str = f"@{username}" if username else "Username မရှိပါ"
        pay_msg = (
            "❌ သင်၏ Free ၁ ကြိမ် သုံးစွဲခွင့် ကုန်ဆုံးသွားပါပြီ။\n\n"
            "ဆက်လက်သုံးစွဲလိုပါက ၁ လလျှင် ၅,၀၀၀ ကျပ် ဖြင့် ဝယ်ယူနိုင်ပါသည်။\n\n"
            "💳 ငွေလွှဲရန် အချက်အလက်များ:\n"
            "• KPay: 09898878313 (Sein Sein Lwin)\n"

            "• Wave: 09690604402 (Zaw Loon)\n\n"
            f"ငွေလွှဲပြီးပါက Admin ({ADMIN_USERNAME}) ထံသို့ ငွေလွှဲစလစ် နှင့်အတူ မိမိ၏ Username ကို ပို့ပေးပါ။\n\n"
            f"📌 သင်၏ Telegram Username: {user_uname_str}"
        )
        await update.message.reply_text(pay_msg, parse_mode="Markdown")
        return

    if chat_id not in user_images:
        user_images[chat_id] = []

    photo_file = await update.message.photo[-1].get_file()
    image_bytes = await photo_file.download_as_bytearray()
    image = Image.open(io.BytesIO(image_bytes))

    user_images[chat_id].append(image)
    count = len(user_images[chat_id])

    if count < 3:
        await update.message.reply_text(
            f"ပုံ {count} ပုံ ရရှိပြီးပါပြီ။ နောက်ထပ် {3 - count} ပုံ ပို့ပေးပါ။"
        )
    elif count == 3:
        await update.message.reply_text("ပုံ ၃ ပုံ ပြည့်ပါပြီ။ ပေါင်းစပ်နေပါသည်။...")

        imgs = user_images[chat_id]
        target_width = imgs[0].width

        resized_imgs = []
        for img in imgs:
            if img.width != target_width:
                new_height = int(img.height * (target_width / img.width))
                img = img.resize(
                    (target_width, new_height), Image.Resampling.LANCZOS
                )
            resized_imgs.append(img)

        total_height = sum(img.height for img in resized_imgs)
        combined_img = Image.new("RGB", (target_width, total_height))

        y_offset = 0
        for img in resized_imgs:
            combined_img.paste(img, (0, y_offset))
            y_offset += img.height

        output = io.BytesIO()
        combined_img.save(output, format="JPEG", quality=95)
        output.seek(0)

        await update.message.reply_photo(
            photo=output, caption="ပေါင်းစပ်ပြီးသား ပုံဖြစ်ပါသည်။"
        )

        user_images[chat_id] = []

        # VIP မဟုတ်ပါက Free ၁ ကြိမ် သုံးပြီးကြောင်း မှတ်သားခြင်း
        if not has_vip:
            user_info["free_used"] = True
            save_users(users_db)
            await update.message.reply_text(
                "🎉 သင်၏ အခမဲ့ ၁ ကြိမ် သုံးစွဲခွင့် ပြီးဆုံးပါပြီ။ နောက်ထပ် သုံးရန် ၁ လ ၅,၀၀၀ ကျပ်ဖြင့် ဝယ်ယူနိုင်ပါသည်။"
            )


# Admin သုံးရန် VIP ပေးသည့် Command (/addvip @username 30)
async def add_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if f"@{update.effective_user.username}" != ADMIN_USERNAME:
        return

    try:
        raw_target = context.args[0].strip()
        # @ ပါရင် ဖြုတ်ပြီး lowercase ပြောင်းခြင်း
        target_username = raw_target.replace("@", "").lower()
        days = int(context.args[1]) if len(context.args) > 1 else 30

        users_db = load_users()
        found_id = None

        # Username ဖြင့် Database ထဲတွင် လိုက်ရှာခြင်း
        for uid, info in users_db.items():
            if info.get("username") and info["username"].lower() == target_username:
                found_id = uid
                break

        if not found_id:
            await update.message.reply_text(
                f"❌ Username @{target_username} ကို ရှာမတွေ့ပါ။ အဆိုပါ User သည် Bot ကို /start မနှိပ်ရသေးပါ သို့မဟုတ် Username မရှိပါ။",
                parse_mode="Markdown",
            )
            return

        new_expiry = datetime.now() + timedelta(days=days)
        users_db[found_id]["expiry_date"] = new_expiry.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        save_users(users_db)

        await update.message.reply_text(
            f"✅ @{target_username} ကို {days} ရက် VIP သက်တမ်း ပေးလိုက်ပါပြီ။",
            parse_mode="Markdown",
        )

        # User ထံ သက်တမ်းတိုးပြီးကြောင်း အသိပေးစာ ပို့ပေးခြင်း
        await context.bot.send_message(
            chat_id=int(found_id),
            text=f"🎉 သင်၏ Premium သက်တမ်းကို {days} ရက် အောင်မြင်စွာ တိုးပေးလိုက်ပါပြီ။",
        )
    except Exception:
        await update.message.reply_text(
            "အသုံးပြုနည်းမှားယွင်းနေပါသည်။ နမူနာ: /addvip @username 30",
            parse_mode="Markdown",
        )


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addvip", add_vip))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot starting...")
    app.run_polling()
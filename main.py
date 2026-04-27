import os, json, logging
from flask import Flask
from threading import Thread
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from datetime import datetime

# -------- تنظیمات --------
TOKEN = os.environ.get("8765075222:AAFT6p_zeYmEcahPoezxtUeqMlsGz0Ra35o")  # امن
DB_FILE = "data.json"
DEFAULT_ADMINS = [5993860770]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------- وب --------
app = Flask(__name__)

@app.route('/')
def home():
    return "OK", 200

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# -------- دیتابیس --------
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            "users": {},
            "admins": DEFAULT_ADMINS.copy(),
            "bot_enabled": True,
            "test_enabled": True,
            "test_reason": "",
            "wallet_settings": {"amounts":[100000,300000,700000,1500000,2000000]},
            "card":{"number":"0000","name":"NAME"},
            "categories":{
                "VIP":[{"id":1,"name":"20GB","price":80,"volume":"20GB"}]
            },
            "configs":{}
        }

    data.setdefault("admins", DEFAULT_ADMINS.copy())
    data.setdefault("users", {})
    data.setdefault("configs", {})
    return data

def save_db():
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_db()
user_data = {}

# -------- ابزار --------
def is_admin(uid):
    return int(uid) in db["admins"]

def is_owner(uid):
    return int(uid) == db["admins"][0]

# -------- منو --------
def main_menu(uid):
    kb = [
        ['💰 خرید','💳 کیف پول'],
        ['📂 سرویس‌ها','🎁 تست']
    ]
    if is_admin(uid):
        kb.append(['⚙️ مدیریت'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup([
        ['➕ ادمین','➕ کانفیگ'],
        ['💾 بکاپ','📥 ریستور'],
        ['📌 پین پیام'],
        ['🔴 خاموش ربات','🟢 روشن ربات'],
        ['🎁 خاموش تست','🎁 روشن تست'],
        ['🔙 برگشت']
    ], resize_keyboard=True)

# -------- start --------
def start(update, context):
    uid = str(update.effective_user.id)

    if uid not in db["users"]:
        db["users"][uid] = {"wallet":0,"purchases":[],"tests":0}
        save_db()

    update.message.reply_text("خوش آمدید", reply_markup=main_menu(uid))

# -------- پیام --------
def handle_msg(update, context):
    uid = str(update.effective_user.id)
    text = update.message.text
    step = user_data.get(uid, {}).get("step")

    # ربات خاموش
    if not db["bot_enabled"] and not is_admin(uid):
        update.message.reply_text("⛔️ ربات خاموش است")
        return

    # برگشت
    if text == '🔙 برگشت':
        user_data[uid] = {}
        start(update, context)
        return

    # مدیریت
    if text == '⚙️ مدیریت' and is_admin(uid):
        update.message.reply_text("پنل مدیریت", reply_markup=admin_menu())
        return

    # افزودن ادمین
    if text == '➕ ادمین':
        if not is_owner(uid):
            update.message.reply_text("❌ فقط ادمین اصلی")
            return
        user_data[uid] = {"step":"add_admin"}
        update.message.reply_text("آیدی عددی:")
        return

    if step == "add_admin":
        try:
            new_admin = int(text)
            if new_admin not in db["admins"]:
                db["admins"].append(new_admin)
                save_db()
                update.message.reply_text("✅ اضافه شد")
            else:
                update.message.reply_text("قبلاً هست")
        except:
            update.message.reply_text("❌ نامعتبر")
        user_data[uid] = {}
        return

    # پین پیام
    if text == '📌 پین پیام' and is_admin(uid):
        user_data[uid] = {"step":"pin"}
        update.message.reply_text("پیام را ارسال کن")
        return

    if step == "pin":
        try:
            context.bot.pin_chat_message(update.effective_chat.id, update.message.message_id)
            update.message.reply_text("📌 پین شد")
        except:
            update.message.reply_text("❌ خطا")
        user_data[uid] = {}
        return

    # خاموش/روشن
    if text == '🔴 خاموش ربات':
        db["bot_enabled"] = False
        save_db()
        update.message.reply_text("خاموش شد")
        return

    if text == '🟢 روشن ربات':
        db["bot_enabled"] = True
        save_db()
        update.message.reply_text("روشن شد")
        return

    # تست
    if text == '🎁 تست':
        if not db["test_enabled"]:
            update.message.reply_text(f"❌ {db['test_reason']}")
            return
        db["users"][uid]["tests"] += 1
        save_db()
        update.message.reply_text("ثبت شد")
        return

    if text == '🎁 خاموش تست':
        user_data[uid] = {"step":"test_off"}
        update.message.reply_text("دلیل:")
        return

    if step == "test_off":
        db["test_enabled"] = False
        db["test_reason"] = text
        save_db()
        update.message.reply_text("خاموش شد")
        user_data[uid] = {}
        return

    if text == '🎁 روشن تست':
        db["test_enabled"] = True
        save_db()
        update.message.reply_text("روشن شد")
        return

    # کیف پول
    if text == '💳 کیف پول':
        bal = db["users"][uid]["wallet"]
        keyboard = []
        for a in db["wallet_settings"]["amounts"]:
            keyboard.append([InlineKeyboardButton(f"{a:,}", callback_data=f"wallet_{a}")])
        keyboard.append([InlineKeyboardButton("💵 دلخواه", callback_data="wallet_custom")])

        update.message.reply_text(f"💰 موجودی: {bal:,}", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if step == "wallet_custom":
        try:
            amount = int(text)
            if 50000 <= amount <= 5000000:
                user_data[uid] = {"step":"wallet_pay","amount":amount}
                update.message.reply_text(f"واریز {amount} به کارت:\n{db['card']['number']}")
            else:
                update.message.reply_text("❌ محدودیت")
        except:
            update.message.reply_text("❌ عدد")
        return

    # خرید
    if text == '💰 خرید':
        keyboard = []
        for cat in db["categories"].values():
            for p in cat:
                keyboard.append([InlineKeyboardButton(p["name"], callback_data=f"buy_{p['id']}")])

        update.message.reply_text("پلن:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

# -------- عکس --------
def handle_photo(update, context):
    uid = str(update.effective_user.id)

    if user_data.get(uid, {}).get("step") == "wallet_pay":
        amount = user_data[uid]["amount"]

        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ تایید", callback_data=f"wallet_ok_{uid}_{amount}")
        ]])

        context.bot.send_photo(
            db["admins"][0],
            update.message.photo[-1].file_id,
            caption=f"شارژ {amount}",
            reply_markup=btn
        )

        update.message.reply_text("ارسال شد")
        user_data[uid] = {}

# -------- callback --------
def handle_cb(update, context):
    q = update.callback_query
    uid = str(q.from_user.id)
    q.answer()

    if q.data.startswith("wallet_") and q.data != "wallet_custom":
        amount = int(q.data.split("_")[1])
        user_data[uid] = {"step":"wallet_pay","amount":amount}
        q.message.reply_text(f"واریز {amount} به:\n{db['card']['number']}")

    if q.data == "wallet_custom":
        user_data[uid] = {"step":"wallet_custom"}
        q.message.reply_text("مبلغ:")

    if q.data.startswith("wallet_ok_"):
        _, u, a = q.data.split("_")
        db["users"][u]["wallet"] += int(a)
        save_db()
        context.bot.send_message(u, "شارژ شد")

# -------- اجرا --------
def main():
    Thread(target=run_web, daemon=True).start()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    dp.add_handler(CallbackQueryHandler(handle_cb))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

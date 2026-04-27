import os, json, logging, shutil
from flask import Flask
from threading import Thread
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from datetime import datetime

# ---------- تنظیمات ----------
TOKEN = "8765075222:AAFT6p_zeYmEcahPoezxtUeqMlsGz0Ra35o"
DB_FILE = "data.json"
BACKUP_DIR = "backups"

# ادمین‌ها (اولی ادمین اصلی)
DEFAULT_ADMINS = [5993860770]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- وب سرور ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# ---------- دیتابیس ----------
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "users": {},
            "admins": DEFAULT_ADMINS.copy(),
            "categories": {
                "🚀": [
                    {"id": 1, "name": "پلن 20GB", "price": 80, "volume": "20GB", "days": 30}
                ]
            },
            "configs": {},
            "wallet_settings": {"amounts": [100000,300000,700000,1500000,2000000]},
            "card": {"number": "0000000000000000", "name": "NAME"}
        }

    # تضمین فیلدها
    data.setdefault("admins", DEFAULT_ADMINS.copy())
    data.setdefault("configs", {})
    data.setdefault("wallet_settings", {"amounts":[100000,300000,700000,1500000,2000000]})
    data.setdefault("users", {})
    return data

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_db()
user_data = {}

def is_admin(uid):
    return int(uid) in db.get("admins", [])

def is_owner(uid):
    admins = db.get("admins", [])
    return admins and int(uid) == int(admins[0])

# ---------- منو ----------
def main_menu(uid):
    kb = [
        ['💰 خرید', '💳 کیف پول'],
        ['📂 سرویس‌ها']
    ]
    if is_admin(uid):
        kb.append(['⚙️ مدیریت'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def admin_menu():
    kb = [
        ['➕ افزودن ادمین', '➕ افزودن کانفیگ'],
        ['💾 بکاپ', '📤 ریستور بکاپ'],
        ['🔙 برگشت']
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def back_btn():
    return ReplyKeyboardMarkup([['🔙 برگشت']], resize_keyboard=True)

# ---------- استارت ----------
def start(update, context):
    uid = str(update.effective_user.id)

    if uid not in db["users"]:
        db["users"][uid] = {
            "wallet": 0,
            "purchases": []
        }
        save_db()

    update.message.reply_text("خوش آمدید", reply_markup=main_menu(uid))

# ---------- پیام ----------
def handle_msg(update, context):
    text = update.message.text
    uid = str(update.effective_user.id)
    step = user_data.get(uid, {}).get("step")

    if text == '🔙 برگشت':
        user_data[uid] = {}
        start(update, context)
        return

    # ---------- کیف پول ----------
    if text == '💳 کیف پول':
        bal = db["users"][uid]["wallet"]
        btn = []
        for a in db["wallet_settings"]["amounts"]:
            btn.append([InlineKeyboardButton(f"{a:,} تومان", callback_data=f"wallet_{a}")])
        btn.append([InlineKeyboardButton("💵 مبلغ دلخواه", callback_data="wallet_custom")])

        update.message.reply_text(
            f"💰 موجودی شما: {bal:,}",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    if step == 'wallet_custom':
        try:
            amount = int(text)
            if 50000 <= amount <= 5000000:
                user_data[uid] = {"step": "wallet_pay", "amount": amount}
                update.message.reply_text(f"پرداخت {amount:,} به کارت:\n{db['card']['number']}")
            else:
                update.message.reply_text("❌ بین 50 هزار تا 5 میلیون")
        except:
            update.message.reply_text("❌ عدد")
        return

    # ---------- مدیریت ----------
    if text == '⚙️ مدیریت' and is_admin(uid):
        update.message.reply_text("پنل مدیریت", reply_markup=admin_menu())
        return

    # افزودن ادمین
    if text == '➕ افزودن ادمین':
        if not is_owner(uid):
            update.message.reply_text("❌ فقط ادمین اصلی")
            return
        user_data[uid] = {"step": "add_admin"}
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
                update.message.reply_text("⚠️ قبلاً هست")
        except:
            update.message.reply_text("❌ نامعتبر")
        user_data[uid] = {}
        return

    # افزودن کانفیگ
    if text == '➕ افزودن کانفیگ' and is_admin(uid):
        user_data[uid] = {"step": "add_config"}
        update.message.reply_text("آیدی پلن:")
        return

    if step == "add_config":
        pid = text
        user_data[uid] = {"step": "save_config", "pid": pid}
        update.message.reply_text("کانفیگ:")
        return

    if step == "save_config":
        pid = user_data[uid]["pid"]
        db["configs"].setdefault(pid, []).append(text)
        save_db()
        update.message.reply_text("✅ ذخیره شد")
        user_data[uid] = {}
        return

    # بکاپ
    if text == '💾 بکاپ' and is_admin(uid):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        name = f"{BACKUP_DIR}/backup_{datetime.now().strftime('%H%M%S')}.json"
        shutil.copy(DB_FILE, name)
        context.bot.send_document(uid, open(name, 'rb'))
        return

    if text == '📤 ریستور بکاپ' and is_admin(uid):
        user_data[uid] = {"step": "restore"}
        update.message.reply_text("فایل json ارسال کن")
        return

# ---------- عکس ----------
def handle_photo(update, context):
    uid = str(update.effective_user.id)

    # شارژ کیف پول
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
        return

# ---------- فایل ----------
def handle_doc(update, context):
    uid = str(update.effective_user.id)

    if user_data.get(uid, {}).get("step") == "restore":
        file = update.message.document
        path = f"{BACKUP_DIR}/restore.json"

        context.bot.get_file(file.file_id).download(path)
        global db
        db = json.load(open(path, 'r', encoding='utf-8'))
        save_db()

        update.message.reply_text("✅ ریستور شد")
        user_data[uid] = {}

# ---------- callback ----------
def handle_cb(update, context):
    q = update.callback_query
    uid = str(q.from_user.id)
    q.answer()

    # انتخاب مبلغ کیف پول
    if q.data.startswith("wallet_") and q.data != "wallet_custom":
        amount = int(q.data.split("_")[1])
        user_data[uid] = {"step": "wallet_pay", "amount": amount}
        q.message.reply_text(f"واریز {amount} به:\n{db['card']['number']}")
        return

    if q.data == "wallet_custom":
        user_data[uid] = {"step": "wallet_custom"}
        q.message.reply_text("مبلغ:")
        return

    # تایید شارژ
    if q.data.startswith("wallet_ok_"):
        _, u, a = q.data.split("_")
        db["users"][u]["wallet"] += int(a)
        save_db()
        context.bot.send_message(u, f"شارژ شد {a}")
        q.message.reply_text("✅")
        return

# ---------- اجرا ----------
def main():
    Thread(target=run_web, daemon=True).start()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    dp.add_handler(MessageHandler(Filters.document, handle_doc))
    dp.add_handler(CallbackQueryHandler(handle_cb))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

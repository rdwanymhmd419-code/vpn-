import os
import json
import logging
from flask import Flask
from threading import Thread, Lock
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# -------- تنظیمات --------
TOKEN = "8681405252:AAH7ONTudaE34evtbxWeLdk0dtZc_XkULEA"
ADMIN_ID = 5993860770
DB_FILE = "db.json"

# -------- لاگ --------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------- لاک (خیلی مهم برای جلوگیری از دابل مصرف) --------
lock = Lock()

# -------- وب سرور برای Railway --------
app = Flask(__name__)

@app.route('/')
def home():
    return "Reseller Bot Running ✅"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# -------- دیتابیس --------
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {
        "plans": {
            "5GB": {"active": True},
            "10GB": {"active": True}
        },
        "inventory": {
            "5GB": [],
            "10GB": []
        },
        "vouchers": {},
        "resellers": {}
    }

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

db = load_db()
user_state = {}

# -------- منو --------
def reseller_menu():
    return ReplyKeyboardMarkup([
        ['📦 موجودی من'],
        ['⚙️ ساخت کانفیگ']
    ], resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup([
        ['➕ افزودن کانفیگ'],
        ['🎟 ساخت واچر']
    ], resize_keyboard=True)

# -------- استارت --------
def start(update, context):
    uid = str(update.effective_user.id)

    if uid not in db["resellers"]:
        db["resellers"][uid] = {"stock": {}, "used": {}}
        save_db()

    update.message.reply_text(
        "🔐 ورود به پنل نمایندگی\n\nکد واچر رو بفرست:",
    )

# -------- پیام --------
def handle_msg(update, context):
    text = update.message.text
    uid = str(update.effective_user.id)

    # -------- ادمین --------
    if str(uid) == str(ADMIN_ID):

        if text == '➕ افزودن کانفیگ':
            user_state[uid] = {"step": "add_plan"}
            update.message.reply_text("نام پلن؟ (مثلاً 5GB)")
            return

        if text == '🎟 ساخت واچر':
            user_state[uid] = {"step": "voucher_plan"}
            update.message.reply_text("نام پلن؟")
            return

        step = user_state.get(uid, {}).get("step")

        if step == "add_plan":
            user_state[uid]["plan"] = text
            user_state[uid]["step"] = "add_count"
            update.message.reply_text("چند تا؟")
            return

        if step == "add_count":
            user_state[uid]["count"] = int(text)
            user_state[uid]["step"] = "add_configs"
            user_state[uid]["configs"] = []
            update.message.reply_text("کانفیگ‌ها رو یکی یکی بفرست")
            return

        if step == "add_configs":
            user_state[uid]["configs"].append(text)

            if len(user_state[uid]["configs"]) >= user_state[uid]["count"]:
                plan = user_state[uid]["plan"]

                if plan not in db["inventory"]:
                    db["inventory"][plan] = []

                db["inventory"][plan].extend(user_state[uid]["configs"])
                save_db()

                update.message.reply_text("✅ ذخیره شد", reply_markup=admin_menu())
                user_state[uid] = {}
            return

        if step == "voucher_plan":
            user_state[uid]["plan"] = text
            user_state[uid]["step"] = "voucher_count"
            update.message.reply_text("چند تا از این پلن؟")
            return

        if step == "voucher_count":
            count = int(text)
            plan = user_state[uid]["plan"]

            code = os.urandom(4).hex().upper()

            db["vouchers"][code] = {
                "plans": {plan: count},
                "used": False
            }
            save_db()

            update.message.reply_text(f"🎟 واچر:\n{code}", reply_markup=admin_menu())
            user_state[uid] = {}
            return

    # -------- کاربر --------

    # اگر واچر وارد کرد
    if text in db["vouchers"]:
        v = db["vouchers"][text]

        if v["used"]:
            update.message.reply_text("❌ قبلاً استفاده شده")
            return

        if uid not in db["resellers"]:
            db["resellers"][uid] = {"stock": {}, "used": {}}

        for plan, count in v["plans"].items():
            db["resellers"][uid]["stock"][plan] = \
                db["resellers"][uid]["stock"].get(plan, 0) + count

        v["used"] = True
        save_db()

        update.message.reply_text("✅ واچر فعال شد", reply_markup=reseller_menu())
        return

    # موجودی
    if text == '📦 موجودی من':
        stock = db["resellers"][uid]["stock"]
        used = db["resellers"][uid]["used"]

        msg = "📦 موجودی:\n"
        for p in stock:
            msg += f"\n{p} → باقی: {stock[p]} | مصرف: {used.get(p,0)}"

        update.message.reply_text(msg)
        return

    # ساخت کانفیگ
    if text == '⚙️ ساخت کانفیگ':
        plans = db["resellers"][uid]["stock"]
        buttons = [[InlineKeyboardButton(p, callback_data=f"make_{p}")] for p in plans]
        update.message.reply_text("پلن رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(buttons))
        return

# -------- کالبک --------
def handle_cb(update, context):
    query = update.callback_query
    uid = str(query.from_user.id)
    query.answer()

    if query.data.startswith("make_"):
        plan = query.data.split("_")[1]

        # 🔒 بخش حیاتی (جلوگیری از دابل مصرف)
        with lock:
            if db["resellers"][uid]["stock"].get(plan, 0) <= 0:
                query.message.reply_text("❌ موجودی نداری")
                return

            if len(db["inventory"].get(plan, [])) == 0:
                query.message.reply_text("❌ انبار خالیه")
                return

            config = db["inventory"][plan].pop(0)

            db["resellers"][uid]["stock"][plan] -= 1
            db["resellers"][uid]["used"][plan] = \
                db["resellers"][uid]["used"].get(plan, 0) + 1

            save_db()

        context.bot.send_message(uid, f"🎉 کانفیگ شما:\n\n{config}")

# -------- اجرا --------
def main():
    Thread(target=run_web).start()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, handle_msg))
    dp.add_handler(CallbackQueryHandler(handle_cb))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

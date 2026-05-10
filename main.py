# main.py

import os
import json
import logging
from threading import Thread
from datetime import datetime

from flask import Flask
from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters
)

# =========================
# تنظیمات
# =========================

TOKEN = "8681405252:AAH7ONTudaE34evtbxWeLdk0dtZc_XkULEA"
ADMIN_ID = 5993860770,7935344235

DB_FILE = "db.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# =========================
# Flask
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "BOT RUNNING", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# =========================
# دیتابیس
# =========================

def default_db():
    return {
        "bot_enabled": True,

        "auto_config": True,

        "card": {
            "number": "6274120000000000",
            "name": "VPN ADMIN"
        },

        "texts": {
            "welcome": "🔥 به فروشگاه VPN خوش آمدید",
            "config": "🎉 سرویس شما آماده شد\n\n{config}",
            "off": "⛔️ ربات موقتاً غیرفعال است"
        },

        "plans": [
            {
                "id": 1,
                "name": "20GB",
                "price": 80,
                "days": 30
            },
            {
                "id": 2,
                "name": "50GB",
                "price": 140,
                "days": 30
            }
        ],

        "configs": {
            "1": [],
            "2": []
        },

        "users": {}
    }

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default_db()

    return default_db()

db = load_db()

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# =========================
# State
# =========================

state = {}

# =========================
# User
# =========================

def ensure_user(uid, name="کاربر"):

    uid = str(uid)

    if uid not in db["users"]:

        db["users"][uid] = {
            "name": name,
            "wallet": 0,
            "services": [],
            "joined": datetime.now().strftime("%Y-%m-%d")
        }

        save_db()

# =========================
# منو
# =========================

def main_menu(uid):

    kb = [
        ['🛒 خرید', '💳 کیف پول'],
        ['📂 سرویس‌ها', '👤 پشتیبانی']
    ]

    if str(uid) == str(ADMIN_ID):
        kb.append(['⚙️ مدیریت'])

    return ReplyKeyboardMarkup(
        kb,
        resize_keyboard=True
    )

def admin_menu():

    kb = [
        ['📦 افزودن کانفیگ', '🤖 ارسال خودکار'],
        ['➕ پلن', '➖ حذف پلن'],
        ['📥 بکاپ', '🔴 خاموش/روشن'],
        ['📢 همگانی', '💳 کارت'],
        ['🔙 برگشت']
    ]

    return ReplyKeyboardMarkup(
        kb,
        resize_keyboard=True
    )

# =========================
# Start
# =========================

def start(update, context):

    uid = update.effective_user.id

    ensure_user(
        uid,
        update.effective_user.first_name
    )

    if not db["bot_enabled"] and uid != ADMIN_ID:
        update.message.reply_text(
            db["texts"]["off"]
        )
        return

    update.message.reply_text(
        db["texts"]["welcome"],
        reply_markup=main_menu(uid)
    )

# =========================
# خرید
# =========================

def show_plans(update):

    buttons = []

    for p in db["plans"]:

        txt = f"{p['name']} | {p['price']} هزار"

        buttons.append([
            InlineKeyboardButton(
                txt,
                callback_data=f"buy_{p['id']}"
            )
        ])

    update.message.reply_text(
        "📦 انتخاب پلن",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# =========================
# ارسال کانفیگ
# =========================

def deliver_config(context, user_id, plan):

    pid = str(plan["id"])

    # اتومات
    if db["auto_config"]:

        if pid in db["configs"]:

            if len(db["configs"][pid]) > 0:

                cfg = db["configs"][pid].pop(0)

                save_db()

                msg = db["texts"]["config"].format(
                    config=cfg
                )

                context.bot.send_message(
                    int(user_id),
                    msg
                )

                db["users"][str(user_id)]["services"].append(
                    plan["name"]
                )

                save_db()

                return True

    return False

# =========================
# پیام
# =========================

def handle_text(update, context):

    try:

        uid = str(update.effective_user.id)

        text = update.message.text

        ensure_user(uid)

        if not db["bot_enabled"] and int(uid) != ADMIN_ID:

            update.message.reply_text(
                db["texts"]["off"]
            )

            return

        st = state.get(uid, {})

        # برگشت
        if text == "🔙 برگشت":

            state[uid] = {}

            update.message.reply_text(
                "برگشت",
                reply_markup=main_menu(uid)
            )

            return

        # خرید
        if text == "🛒 خرید":

            show_plans(update)

            return

        # کیف پول
        if text == "💳 کیف پول":

            wallet = db["users"][uid]["wallet"]

            update.message.reply_text(
                f"💰 موجودی: {wallet:,} تومان"
            )

            return

        # سرویس ها
        if text == "📂 سرویس‌ها":

            services = db["users"][uid]["services"]

            if not services:

                update.message.reply_text(
                    "❌ سرویسی ندارید"
                )

                return

            msg = "📂 سرویس‌های شما\n\n"

            for s in services:

                msg += f"• {s}\n"

            update.message.reply_text(msg)

            return

        # پشتیبانی
        if text == "👤 پشتیبانی":

            update.message.reply_text(
                "@Support"
            )

            return

        # =====================
        # مدیریت
        # =====================

        if int(uid) == ADMIN_ID:

            # پنل
            if text == "⚙️ مدیریت":

                update.message.reply_text(
                    "⚙️ پنل مدیریت",
                    reply_markup=admin_menu()
                )

                return

            # خاموش روشن
            if text == "🔴 خاموش/روشن":

                db["bot_enabled"] = not db["bot_enabled"]

                save_db()

                update.message.reply_text(
                    f"وضعیت: {db['bot_enabled']}"
                )

                return

            # ارسال خودکار
            if text == "🤖 ارسال خودکار":

                db["auto_config"] = not db["auto_config"]

                save_db()

                update.message.reply_text(
                    f"ارسال خودکار: {db['auto_config']}"
                )

                return

            # بکاپ
            if text == "📥 بکاپ":

                save_db()

                context.bot.send_document(
                    ADMIN_ID,
                    open(DB_FILE, "rb"),
                    filename="backup.json"
                )

                return

            # همگانی
            if text == "📢 همگانی":

                state[uid] = {
                    "step": "broadcast"
                }

                update.message.reply_text(
                    "پیام را ارسال کن"
                )

                return

            # افزودن کانفیگ
            if text == "📦 افزودن کانفیگ":

                buttons = []

                for p in db["plans"]:

                    buttons.append([
                        InlineKeyboardButton(
                            p["name"],
                            callback_data=f"addcfg_{p['id']}"
                        )
                    ])

                update.message.reply_text(
                    "پلن را انتخاب کن",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )

                return

            # افزودن پلن
            if text == "➕ پلن":

                state[uid] = {
                    "step": "new_plan_name"
                }

                update.message.reply_text(
                    "نام پلن:"
                )

                return

            # حذف پلن
            if text == "➖ حذف پلن":

                buttons = []

                for p in db["plans"]:

                    buttons.append([
                        InlineKeyboardButton(
                            f"❌ {p['name']}",
                            callback_data=f"delplan_{p['id']}"
                        )
                    ])

                update.message.reply_text(
                    "حذف پلن",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )

                return

            # مرحله افزودن پلن
            if st.get("step") == "new_plan_name":

                st["name"] = text

                st["step"] = "new_plan_price"

                update.message.reply_text(
                    "قیمت هزار تومانی:"
                )

                return

            if st.get("step") == "new_plan_price":

                try:

                    price = int(text)

                    pid = len(db["plans"]) + 1

                    db["plans"].append({
                        "id": pid,
                        "name": st["name"],
                        "price": price,
                        "days": 30
                    })

                    db["configs"][str(pid)] = []

                    save_db()

                    state[uid] = {}

                    update.message.reply_text(
                        "✅ اضافه شد"
                    )

                except:

                    update.message.reply_text(
                        "❌ خطا"
                    )

                return

            # افزودن کانفیگ
            if st.get("step") == "wait_config":

                pid = st["pid"]

                if str(pid) not in db["configs"]:
                    db["configs"][str(pid)] = []

                db["configs"][str(pid)].append(text)

                save_db()

                state[uid] = {}

                update.message.reply_text(
                    "✅ کانفیگ ذخیره شد"
                )

                return

            # همگانی
            if st.get("step") == "broadcast":

                ok = 0

                for user in db["users"]:

                    try:

                        context.bot.send_message(
                            int(user),
                            text
                        )

                        ok += 1

                    except:
                        pass

                state[uid] = {}

                update.message.reply_text(
                    f"✅ ارسال شد\n{ok}"
                )

                return

            # ارسال دستی
            if st.get("manual_send"):

                target = st["manual_send"]

                context.bot.send_message(
                    int(target),
                    db["texts"]["config"].format(
                        config=text
                    )
                )

                state[uid] = {}

                update.message.reply_text(
                    "✅ ارسال شد"
                )

                return

            # رد
            if st.get("reject_user"):

                target = st["reject_user"]

                context.bot.send_message(
                    int(target),
                    f"❌ پرداخت رد شد\n\n{text}"
                )

                state[uid] = {}

                update.message.reply_text(
                    "✅ ارسال شد"
                )

                return

    except Exception as e:

        logger.error(e)

# =========================
# عکس
# =========================

def handle_photo(update, context):

    try:

        uid = str(update.effective_user.id)

        st = state.get(uid, {})

        # فیش
        if st.get("step") == "wait_receipt":

            pid = st["plan"]

            plan = None

            for p in db["plans"]:

                if p["id"] == pid:
                    plan = p

            buttons = [
                [
                    InlineKeyboardButton(
                        "✅ تایید",
                        callback_data=f"accept_{uid}_{pid}"
                    ),

                    InlineKeyboardButton(
                        "❌ رد",
                        callback_data=f"reject_{uid}"
                    )
                ]
            ]

            context.bot.send_photo(
                ADMIN_ID,
                update.message.photo[-1].file_id,
                caption=f"خرید جدید\n\nکاربر: {uid}\nپلن: {plan['name']}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

            update.message.reply_text(
                "✅ برای ادمین ارسال شد"
            )

            state[uid] = {}

    except Exception as e:

        logger.error(e)

# =========================
# Callback
# =========================

def handle_callback(update, context):

    try:

        query = update.callback_query

        query.answer()

        uid = str(query.from_user.id)

        data = query.data

        # خرید
        if data.startswith("buy_"):

            pid = int(data.split("_")[1])

            plan = None

            for p in db["plans"]:

                if p["id"] == pid:
                    plan = p

            txt = f"""
🧾 پیش فاکتور

📦 پلن: {plan['name']}
📅 مدت: {plan['days']} روز
💰 مبلغ: {plan['price']} هزار تومان

💳 کارت:
{db['card']['number']}

👤 {db['card']['name']}

پس از پرداخت فیش را ارسال کنید
"""

            state[uid] = {
                "step": "wait_receipt",
                "plan": pid
            }

            query.message.reply_text(txt)

            return

        # افزودن کانفیگ
        if data.startswith("addcfg_"):

            pid = int(data.split("_")[1])

            state[uid] = {
                "step": "wait_config",
                "pid": pid
            }

            query.message.reply_text(
                "کانفیگ را ارسال کن"
            )

            return

        # حذف پلن
        if data.startswith("delplan_"):

            pid = int(data.split("_")[1])

            new_plans = []

            for p in db["plans"]:

                if p["id"] != pid:
                    new_plans.append(p)

            db["plans"] = new_plans

            if str(pid) in db["configs"]:
                del db["configs"][str(pid)]

            save_db()

            query.message.reply_text(
                "✅ حذف شد"
            )

            return

        # تایید
        if data.startswith("accept_"):

            parts = data.split("_")

            target = parts[1]

            pid = int(parts[2])

            plan = None

            for p in db["plans"]:

                if p["id"] == pid:
                    plan = p

            ok = deliver_config(
                context,
                target,
                plan
            )

            if ok:

                query.message.reply_text(
                    "✅ کانفیگ ارسال شد"
                )

            else:

                state[uid] = {
                    "manual_send": target
                }

                query.message.reply_text(
                    "⚠️ کانفیگ موجود نیست یا ارسال خودکار خاموش است\n\nکانفیگ را دستی ارسال کن"
                )

            return

        # رد
        if data.startswith("reject_"):

            target = data.split("_")[1]

            state[uid] = {
                "reject_user": target
            }

            query.message.reply_text(
                "دلیل رد:"
            )

            return

    except Exception as e:

        logger.error(e)

# =========================
# Main
# =========================

def main():

    Thread(
        target=run_web,
        daemon=True
    ).start()

    updater = Updater(
        TOKEN,
        use_context=True
    )

    dp = updater.dispatcher

    dp.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    dp.add_handler(
        CallbackQueryHandler(
            handle_callback
        )
    )

    dp.add_handler(
        MessageHandler(
            Filters.photo,
            handle_photo
        )
    )

    dp.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command,
            handle_text
        )
    )

    updater.start_polling()

    updater.idle()

if __name__ == "__main__":
    main()

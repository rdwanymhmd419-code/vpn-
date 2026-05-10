# =========================
# MAIN.PY - PART 1
# Production Version
# =========================

import os
import json
import logging
import traceback

from flask import Flask
from threading import Thread
from datetime import datetime

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
# LOGGING
# =========================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# =========================
# FLASK
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "VPN BOT RUNNING", 200

def run_web():

    port = int(
        os.environ.get("PORT", 8080)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )

# =========================
# CONFIG
# =========================

TOKEN = "8681405252:AAH7ONTudaE34evtbxWeLdk0dtZc_XkULEA"

MAIN_ADMIN = 5993860770

DB_FILE = "db.json"

# =========================
# DEFAULT DATABASE
# =========================

def default_db():

    return {

        "bot_enabled": True,

        "auto_config": True,

        "test_enabled": True,

        "test_reason": "",

        "brand": "VPN SHOP",

        "support": "@support",

        "guide": "@guide",

        "admins": [
            MAIN_ADMIN
        ],

        "wallet_prices": [

            100000,
            300000,
            500000,
            1000000,
            2000000

        ],

        "card": {

            "number":
            "6274120000000000",

            "name":
            "VPN ADMIN"

        },

        "texts": {

            "welcome":
            "🔥 به فروشگاه VPN خوش آمدید",

            "off":
            "⛔️ ربات موقتاً غیرفعال است",

            "config":
            "🎉 سرویس شما آماده شد\n\n{config}",

            "wait_admin":
            "⏳ پرداخت شما ثبت شد\nلطفاً منتظر تایید ادمین باشید",

            "rejected":
            "❌ پرداخت شما رد شد\n\nدلیل:\n{reason}",

            "wallet_ok":
            "✅ کیف پول شما شارژ شد",

            "test_off":
            "❌ تست غیرفعال است\n\n{reason}"

        },

        "plans": [

            {

                "id": 1,

                "name": "20GB",

                "price": 80000,

                "days": 30,

                "category": "پیشنهادی"

            },

            {

                "id": 2,

                "name": "50GB",

                "price": 140000,

                "days": 30,

                "category": "پیشنهادی"

            }

        ],

        "configs": {

            "1": [],
            "2": []

        },

        "used_configs": [],

        "users": {}

    }

# =========================
# LOAD DB
# =========================

def load_db():

    if os.path.exists(DB_FILE):

        try:

            with open(
                DB_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except Exception as e:

            logger.error(e)

            return default_db()

    return default_db()

db = load_db()

# =========================
# SAVE DB
# =========================

def save_db():

    with open(
        DB_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            db,
            f,
            ensure_ascii=False,
            indent=2
        )

# =========================
# USER STATE
# =========================

state = {}

# =========================
# HELPERS
# =========================

def is_admin(uid):

    return int(uid) in db["admins"]

def ensure_user(uid, name="کاربر"):

    uid = str(uid)

    if uid not in db["users"]:

        db["users"][uid] = {

            "name": name,

            "wallet": 0,

            "services": [],

            "joined":
            datetime.now().strftime("%Y-%m-%d")

        }

        save_db()

# =========================
# MENUS
# =========================

def main_menu(uid):

    kb = [

        ['🛒 خرید', '💳 کیف پول'],

        ['📂 سرویس‌های من', '🎁 تست رایگان'],

        ['👤 پشتیبانی', '📚 آموزش']

    ]

    if is_admin(uid):

        kb.append(['⚙️ مدیریت'])

    return ReplyKeyboardMarkup(
        kb,
        resize_keyboard=True
    )

# =========================
# ADMIN MENU
# =========================

def admin_menu():

    kb = [

        ['📦 افزودن کانفیگ', '🤖 ارسال خودکار'],

        ['➕ افزودن پلن', '➖ حذف پلن'],

        ['💳 کارت', '🏷 برند'],

        ['📥 بکاپ', '📤 ریستور'],

        ['🔴 خاموش/روشن', '🎁 تست'],

        ['📢 همگانی', '📌 پین پیام'],

        ['👮 افزودن ادمین', '📊 آمار'],

        ['🔙 برگشت']

    ]

    return ReplyKeyboardMarkup(
        kb,
        resize_keyboard=True
    )

# =========================
# START
# =========================

def start(update, context):

    try:

        uid = update.effective_user.id

        ensure_user(
            uid,
            update.effective_user.first_name
        )

        if (
            not db["bot_enabled"]
            and
            not is_admin(uid)
        ):

            update.message.reply_text(
                db["texts"]["off"]
            )

            return

        update.message.reply_text(

            db["texts"]["welcome"],

            reply_markup=main_menu(uid)

        )

    except Exception as e:

        logger.error(e)

# =========================
# SHOW PLANS
# =========================

def show_plans(update):

    buttons = []

    for p in db["plans"]:

        txt = (
            f"🔥 {p['name']} | "
            f"{p['price']:,} تومان"
        )

        buttons.append([

            InlineKeyboardButton(
                txt,
                callback_data=f"buy_{p['id']}"
            )

        ])

    update.message.reply_text(

        "📦 انتخاب پلن:",

        reply_markup=InlineKeyboardMarkup(
            buttons
        )

    )

# =========================
# SEND CONFIG
# =========================

def deliver_config(
    context,
    user_id,
    plan
):

    pid = str(plan["id"])

    if not db["auto_config"]:
        return False

    if pid not in db["configs"]:
        return False

    if len(db["configs"][pid]) <= 0:
        return False

    config = db["configs"][pid].pop(0)

    if config in db["used_configs"]:
        return False

    db["used_configs"].append(config)

    db["users"][str(user_id)]["services"].append({

        "plan":
        plan["name"],

        "date":
        datetime.now().strftime("%Y-%m-%d %H:%M")

    })

    save_db()

    text = db["texts"]["config"].format(
        config=config
    )

    context.bot.send_message(
        int(user_id),
        text
    )

    return True

# =========================
# HANDLE TEXT
# =========================

def handle_text(update, context):

    try:

        uid = str(
            update.effective_user.id
        )

        text = update.message.text

        ensure_user(uid)

        if (
            not db["bot_enabled"]
            and
            not is_admin(uid)
        ):

            update.message.reply_text(
                db["texts"]["off"]
            )

            return

        st = state.get(uid, {})

        # =====================
        # BACK
        # =====================

        if text == "🔙 برگشت":

            state[uid] = {}

            update.message.reply_text(

                "✅ برگشت",

                reply_markup=main_menu(uid)

            )

            return

        # =====================
        # BUY
        # =====================

        if text == "🛒 خرید":

            show_plans(update)

            return

        # =====================
        # WALLET
        # =====================

        if text == "💳 کیف پول":

            wallet = db["users"][uid]["wallet"]

            msg = (
                f"💰 موجودی کیف پول:\n\n"
                f"{wallet:,} تومان"
            )

            buttons = []

            for amount in db["wallet_prices"]:

                buttons.append([

                    InlineKeyboardButton(

                        f"{amount:,} تومان",

                        callback_data=
                        f"wallet_{amount}"

                    )

                ])

            buttons.append([

                InlineKeyboardButton(

                    "💵 مبلغ دلخواه",

                    callback_data="wallet_custom"

                )

            ])

            update.message.reply_text(

                msg,

                reply_markup=
                InlineKeyboardMarkup(buttons)

            )

            return

        # =====================
        # SERVICES
        # =====================

        if text == "📂 سرویس‌های من":

            services = db["users"][uid]["services"]

            if len(services) <= 0:

                update.message.reply_text(
                    "❌ سرویسی ندارید"
                )

                return

            msg = "📂 سرویس‌های شما\n\n"

            for s in services:

                msg += (
                    f"🔥 {s['plan']}\n"
                    f"📅 {s['date']}\n\n"
                )

            update.message.reply_text(msg)

            return

        # =====================
        # FREE TEST
        # =====================

        if text == "🎁 تست رایگان":

            if not db["test_enabled"]:

                reason = db["test_reason"]

                msg = db["texts"]["test_off"].format(
                    reason=reason
                )

                update.message.reply_text(msg)

                return

            update.message.reply_text(
                "✅ درخواست تست ثبت شد"
            )

            context.bot.send_message(

                MAIN_ADMIN,

                f"🎁 درخواست تست\n\n"
                f"👤 {uid}"

            )

            return

        # =====================
        # SUPPORT
        # =====================

        if text == "👤 پشتیبانی":

            update.message.reply_text(
                db["support"]
            )

            return

        # =====================
        # GUIDE
        # =====================

        if text == "📚 آموزش":

            update.message.reply_text(
                db["guide"]
            )

            return
            # =========================
# MAIN.PY - PART 2
# ادامه مستقیم فایل
# =========================

        # =====================
        # ADMIN PANEL
        # =====================

        if text == "⚙️ مدیریت":

            if not is_admin(uid):

                return

            update.message.reply_text(

                "⚙️ پنل مدیریت",

                reply_markup=admin_menu()

            )

            return

        # =====================
        # AUTO CONFIG
        # =====================

        if text == "🤖 ارسال خودکار":

            if not is_admin(uid):
                return

            db["auto_config"] = not db["auto_config"]

            save_db()

            status = (
                "✅ روشن"
                if db["auto_config"]
                else "❌ خاموش"
            )

            update.message.reply_text(
                f"وضعیت ارسال خودکار:\n\n{status}"
            )

            return

        # =====================
        # BOT ON/OFF
        # =====================

        if text == "🔴 خاموش/روشن":

            if not is_admin(uid):
                return

            db["bot_enabled"] = not db["bot_enabled"]

            save_db()

            status = (
                "✅ روشن"
                if db["bot_enabled"]
                else "❌ خاموش"
            )

            update.message.reply_text(
                f"وضعیت ربات:\n\n{status}"
            )

            return

        # =====================
        # TEST ON/OFF
        # =====================

        if text == "🎁 تست":

            if not is_admin(uid):
                return

            keyboard = [

                [

                    InlineKeyboardButton(
                        "✅ روشن",
                        callback_data="test_on"
                    ),

                    InlineKeyboardButton(
                        "❌ خاموش",
                        callback_data="test_off"
                    )

                ]

            ]

            update.message.reply_text(

                "تنظیم تست رایگان:",

                reply_markup=
                InlineKeyboardMarkup(keyboard)

            )

            return

        # =====================
        # CARD EDIT
        # =====================

        if text == "💳 کارت":

            if not is_admin(uid):
                return

            current = (

                f"💳 کارت فعلی:\n\n"

                f"{db['card']['number']}\n"

                f"{db['card']['name']}\n\n"

                f"شماره کارت جدید را ارسال کن:"
            )

            state[uid] = {

                "step":
                "edit_card_number"

            }

            update.message.reply_text(current)

            return

        # شماره کارت
        if st.get("step") == "edit_card_number":

            number = text.replace(" ", "")

            if (
                not number.isdigit()
                or
                len(number) != 16
            ):

                update.message.reply_text(
                    "❌ شماره کارت نامعتبر است"
                )

                return

            st["card_number"] = number

            st["step"] = "edit_card_name"

            update.message.reply_text(
                "👤 نام صاحب کارت را ارسال کن:"
            )

            return

        # نام صاحب کارت
        if st.get("step") == "edit_card_name":

            db["card"]["number"] = st["card_number"]

            db["card"]["name"] = text

            save_db()

            state[uid] = {}

            update.message.reply_text(
                "✅ کارت ذخیره شد"
            )

            return

        # =====================
        # BRAND
        # =====================

        if text == "🏷 برند":

            if not is_admin(uid):
                return

            state[uid] = {

                "step":
                "edit_brand"

            }

            update.message.reply_text(
                "🏷 نام جدید برند را ارسال کن:"
            )

            return

        if st.get("step") == "edit_brand":

            db["brand"] = text

            save_db()

            state[uid] = {}

            update.message.reply_text(
                "✅ برند ذخیره شد"
            )

            return

        # =====================
        # ADD PLAN
        # =====================

        if text == "➕ افزودن پلن":

            if not is_admin(uid):
                return

            state[uid] = {

                "step":
                "new_plan_name"

            }

            update.message.reply_text(
                "📦 نام پلن را ارسال کن:"
            )

            return

        if st.get("step") == "new_plan_name":

            st["name"] = text

            st["step"] = "new_plan_price"

            update.message.reply_text(
                "💰 قیمت پلن:"
            )

            return

        if st.get("step") == "new_plan_price":

            if not text.isdigit():

                update.message.reply_text(
                    "❌ فقط عدد"
                )

                return

            st["price"] = int(text)

            st["step"] = "new_plan_days"

            update.message.reply_text(
                "📅 تعداد روز:"
            )

            return

        if st.get("step") == "new_plan_days":

            if not text.isdigit():

                update.message.reply_text(
                    "❌ فقط عدد"
                )

                return

            max_id = 0

            for p in db["plans"]:

                if p["id"] > max_id:
                    max_id = p["id"]

            plan = {

                "id":
                max_id + 1,

                "name":
                st["name"],

                "price":
                st["price"],

                "days":
                int(text),

                "category":
                "عمومی"

            }

            db["plans"].append(plan)

            db["configs"][str(plan["id"])] = []

            save_db()

            state[uid] = {}

            update.message.reply_text(
                "✅ پلن اضافه شد"
            )

            return

        # =====================
        # DELETE PLAN
        # =====================

        if text == "➖ حذف پلن":

            if not is_admin(uid):
                return

            buttons = []

            for p in db["plans"]:

                buttons.append([

                    InlineKeyboardButton(

                        f"❌ {p['name']}",

                        callback_data=
                        f"delplan_{p['id']}"

                    )

                ])

            update.message.reply_text(

                "پلن موردنظر را انتخاب کن:",

                reply_markup=
                InlineKeyboardMarkup(buttons)

            )

            return

        # =====================
        # ADD CONFIG
        # =====================

        if text == "📦 افزودن کانفیگ":

            if not is_admin(uid):
                return

            buttons = []

            for p in db["plans"]:

                buttons.append([

                    InlineKeyboardButton(

                        p["name"],

                        callback_data=
                        f"addcfg_{p['id']}"

                    )

                ])

            update.message.reply_text(

                "پلن موردنظر را انتخاب کن:",

                reply_markup=
                InlineKeyboardMarkup(buttons)

            )

            return

        if st.get("step") == "wait_config":

            pid = str(st["plan_id"])

            if pid not in db["configs"]:

                db["configs"][pid] = []

            db["configs"][pid].append(text)

            save_db()

            state[uid] = {}

            update.message.reply_text(
                "✅ کانفیگ ذخیره شد"
            )

            return

        # =====================
        # ADD ADMIN
        # =====================

        if text == "👮 افزودن ادمین":

            if int(uid) != MAIN_ADMIN:

                update.message.reply_text(
                    "❌ فقط ادمین اصلی"
                )

                return

            state[uid] = {

                "step":
                "add_admin"

            }

            update.message.reply_text(
                "🆔 آیدی عددی ادمین جدید:"
            )

            return

        if st.get("step") == "add_admin":

            if not text.isdigit():

                update.message.reply_text(
                    "❌ آیدی نامعتبر"
                )

                return

            aid = int(text)

            if aid not in db["admins"]:

                db["admins"].append(aid)

                save_db()

            state[uid] = {}

            update.message.reply_text(
                "✅ ادمین اضافه شد"
            )

            return

        # =====================
        # PIN MESSAGE
        # =====================

        if text == "📌 پین پیام":

            if not is_admin(uid):
                return

            state[uid] = {

                "step":
                "pin_msg"

            }

            update.message.reply_text(
                "📌 پیام را ارسال کن:"
            )

            return

        if st.get("step") == "pin_msg":

            try:

                sent = context.bot.send_message(
                    int(uid),
                    text
                )

                context.bot.pin_chat_message(
                    chat_id=int(uid),
                    message_id=sent.message_id
                )

                update.message.reply_text(
                    "✅ پیام پین شد"
                )

            except:

                update.message.reply_text(
                    "❌ خطا در پین"
                )

            state[uid] = {}

            return

        # =====================
        # BROADCAST
        # =====================

        if text == "📢 همگانی":

            if not is_admin(uid):
                return

            state[uid] = {

                "step":
                "broadcast"

            }

            update.message.reply_text(
                "📨 پیام همگانی را ارسال کن:"
            )

            return

        if st.get("step") == "broadcast":

            success = 0
            failed = 0

            for u in db["users"]:

                try:

                    context.bot.send_message(
                        int(u),
                        text
                    )

                    success += 1

                except:

                    failed += 1

            state[uid] = {}

            update.message.reply_text(

                f"✅ ارسال انجام شد\n\n"

                f"موفق: {success}\n"

                f"ناموفق: {failed}"

            )

            return

        # =====================
        # STATS
        # =====================

        if text == "📊 آمار":

            if not is_admin(uid):
                return

            users = len(db["users"])

            plans = len(db["plans"])

            configs = 0

            for k in db["configs"]:
                configs += len(db["configs"][k])

            sold = len(db["used_configs"])

            msg = (

                f"📊 آمار ربات\n\n"

                f"👤 کاربران: {users}\n"

                f"📦 پلن‌ها: {plans}\n"

                f"📁 کانفیگ‌ها: {configs}\n"

                f"🔥 فروخته شده: {sold}"

            )

            update.message.reply_text(msg)

            return
            # =========================
# MAIN.PY - PART 3
# ادامه مستقیم فایل
# =========================

        # =====================
        # BACKUP
        # =====================

        if text == "📥 بکاپ":

            if not is_admin(uid):
                return

            try:

                save_db()

                with open(DB_FILE, "rb") as f:

                    context.bot.send_document(

                        chat_id=int(uid),

                        document=f,

                        filename="backup.json",

                        caption="✅ بکاپ دیتابیس"

                    )

            except Exception as e:

                logger.error(e)

                update.message.reply_text(
                    "❌ خطا در بکاپ"
                )

            return

        # =====================
        # RESTORE
        # =====================

        if text == "📤 ریستور":

            if not is_admin(uid):
                return

            state[uid] = {

                "step":
                "restore_db"

            }

            update.message.reply_text(
                "📂 فایل بکاپ JSON را ارسال کن:"
            )

            return

        # =====================
        # CUSTOM WALLET
        # =====================

        if st.get("step") == "wallet_custom":

            if not text.isdigit():

                update.message.reply_text(
                    "❌ فقط عدد وارد کن"
                )

                return

            amount = int(text)

            if amount < 50000:

                update.message.reply_text(
                    "❌ حداقل 50 هزار تومان"
                )

                return

            if amount > 5000000:

                update.message.reply_text(
                    "❌ حداکثر 5 میلیون تومان"
                )

                return

            st["amount"] = amount

            st["step"] = "wallet_receipt"

            msg = (

                f"💳 شارژ کیف پول\n\n"

                f"💰 مبلغ: {amount:,} تومان\n\n"

                f"شماره کارت:\n"

                f"{db['card']['number']}\n\n"

                f"👤 {db['card']['name']}\n\n"

                f"📸 بعد پرداخت فیش را ارسال کن"

            )

            update.message.reply_text(msg)

            return

        # =====================
        # WAIT RECEIPT
        # =====================

        if st.get("step") == "wait_receipt":

            update.message.reply_text(
                "📸 لطفاً عکس فیش را ارسال کن"
            )

            return

        # =====================
        # MANUAL CONFIG
        # =====================

        if st.get("step") == "manual_config":

            target = st["target"]

            plan = st["plan"]

            cfg = text

            db["users"][str(target)]["services"].append({

                "plan":
                plan["name"],

                "date":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                )

            })

            save_db()

            final_text = db["texts"]["config"].format(
                config=cfg
            )

            context.bot.send_message(
                int(target),
                final_text
            )

            update.message.reply_text(
                "✅ کانفیگ ارسال شد"
            )

            state[uid] = {}

            return

        # =====================
        # REJECT REASON
        # =====================

        if st.get("step") == "reject_reason":

            target = st["target"]

            reason = text

            msg = db["texts"]["rejected"].format(
                reason=reason
            )

            context.bot.send_message(
                int(target),
                msg
            )

            update.message.reply_text(
                "✅ دلیل رد ارسال شد"
            )

            state[uid] = {}

            return

        # =====================
        # UNKNOWN
        # =====================

        update.message.reply_text(
            "❌ دستور نامعتبر"
        )

    except Exception as e:

        logger.error(traceback.format_exc())

        update.message.reply_text(
            "❌ خطا"
        )

# =========================
# CALLBACKS
# =========================

def handle_callback(update, context):

    try:

        query = update.callback_query

        query.answer()

        uid = str(query.from_user.id)

        data = query.data

        ensure_user(uid)

        # =====================
        # BUY PLAN
        # =====================

        if data.startswith("buy_"):

            pid = int(
                data.split("_")[1]
            )

            plan = None

            for p in db["plans"]:

                if p["id"] == pid:
                    plan = p

            if not plan:

                query.message.reply_text(
                    "❌ پلن پیدا نشد"
                )

                return

            wallet = db["users"][uid]["wallet"]

            price = plan["price"]

            txt = (

                f"🧾 پیش فاکتور\n\n"

                f"📦 پلن: {plan['name']}\n"

                f"📅 مدت: {plan['days']} روز\n"

                f"💰 مبلغ: {price:,} تومان\n\n"

                f"💳 موجودی کیف پول:\n"
                f"{wallet:,} تومان"

            )

            buttons = []

            # پرداخت کامل با کیف پول
            if wallet >= price:

                buttons.append([

                    InlineKeyboardButton(

                        "💰 پرداخت با کیف پول",

                        callback_data=
                        f"walletpay_{pid}"

                    )

                ])

            # خرید ترکیبی
            elif wallet > 0:

                remain = price - wallet

                buttons.append([

                    InlineKeyboardButton(

                        f"💳 ترکیبی | "
                        f"{remain:,} تومان",

                        callback_data=
                        f"mixpay_{pid}"

                    )

                ])

            # کارت به کارت
            buttons.append([

                InlineKeyboardButton(

                    "🏦 کارت به کارت",

                    callback_data=
                    f"cardpay_{pid}"

                )

            ])

            query.message.reply_text(

                txt,

                reply_markup=
                InlineKeyboardMarkup(buttons)

            )

            return

        # =====================
        # WALLET PAY
        # =====================

        if data.startswith("walletpay_"):

            pid = int(
                data.split("_")[1]
            )

            plan = None

            for p in db["plans"]:

                if p["id"] == pid:
                    plan = p

            if not plan:
                return

            price = plan["price"]

            db["users"][uid]["wallet"] -= price

            save_db()

            ok = deliver_config(
                context,
                uid,
                plan
            )

            if ok:

                query.message.reply_text(
                    "✅ خرید انجام شد"
                )

            else:

                state[str(MAIN_ADMIN)] = {

                    "step":
                    "manual_config",

                    "target":
                    uid,

                    "plan":
                    plan

                }

                context.bot.send_message(

                    MAIN_ADMIN,

                    f"⚠️ ارسال خودکار ناموفق بود\n\n"
                    f"کانفیگ دستی ارسال کن"

                )

                query.message.reply_text(
                    db["texts"]["wait_admin"]
                )

            return

        # =====================
        # MIX PAY
        # =====================

        if data.startswith("mixpay_"):

            pid = int(
                data.split("_")[1]
            )

            plan = None

            for p in db["plans"]:

                if p["id"] == pid:
                    plan = p

            if not plan:
                return

            wallet = db["users"][uid]["wallet"]

            remain = plan["price"] - wallet

            state[uid] = {

                "step":
                "wait_receipt",

                "plan":
                plan,

                "mixed":
                True,

                "remain":
                remain

            }

            txt = (

                f"💳 پرداخت ترکیبی\n\n"

                f"💰 باقی مانده:\n"

                f"{remain:,} تومان\n\n"

                f"🏦 شماره کارت:\n"

                f"{db['card']['number']}\n\n"

                f"👤 {db['card']['name']}\n\n"

                f"📸 فیش را ارسال کن"

            )

            query.message.reply_text(txt)

            return

        # =====================
        # CARD PAY
        # =====================

        if data.startswith("cardpay_"):

            pid = int(
                data.split("_")[1]
            )

            plan = None

            for p in db["plans"]:

                if p["id"] == pid:
                    plan = p

            if not plan:
                return

            state[uid] = {

                "step":
                "wait_receipt",

                "plan":
                plan

            }

            txt = (

                f"🏦 کارت به کارت\n\n"

                f"📦 {plan['name']}\n"

                f"💰 {plan['price']:,} تومان\n\n"

                f"شماره کارت:\n"

                f"{db['card']['number']}\n\n"

                f"👤 {db['card']['name']}\n\n"

                f"📸 بعد پرداخت فیش را ارسال کن"

            )

            query.message.reply_text(txt)

            return
            # =========================
# MAIN.PY - PART 4
# ادامه مستقیم فایل
# =========================

        # =====================
        # WALLET CHARGE
        # =====================

        if data.startswith("wallet_"):

            amount = data.split("_")[1]

            if amount == "custom":

                state[uid] = {

                    "step":
                    "wallet_custom"

                }

                query.message.reply_text(

                    "💵 مبلغ دلخواه را ارسال کن\n\n"

                    "حداقل: 50,000\n"

                    "حداکثر: 5,000,000"

                )

                return

            amount = int(amount)

            state[uid] = {

                "step":
                "wallet_receipt",

                "amount":
                amount

            }

            txt = (

                f"💳 شارژ کیف پول\n\n"

                f"💰 مبلغ:\n"

                f"{amount:,} تومان\n\n"

                f"🏦 شماره کارت:\n"

                f"{db['card']['number']}\n\n"

                f"👤 {db['card']['name']}\n\n"

                f"📸 فیش را ارسال کن"

            )

            query.message.reply_text(txt)

            return

        # =====================
        # ADD CONFIG CALLBACK
        # =====================

        if data.startswith("addcfg_"):

            if not is_admin(uid):
                return

            pid = int(
                data.split("_")[1]
            )

            state[uid] = {

                "step":
                "wait_config",

                "plan_id":
                pid

            }

            query.message.reply_text(
                "📥 کانفیگ را ارسال کن:"
            )

            return

        # =====================
        # DELETE PLAN CALLBACK
        # =====================

        if data.startswith("delplan_"):

            if not is_admin(uid):
                return

            pid = int(
                data.split("_")[1]
            )

            new_plans = []

            for p in db["plans"]:

                if p["id"] != pid:
                    new_plans.append(p)

            db["plans"] = new_plans

            if str(pid) in db["configs"]:

                del db["configs"][str(pid)]

            save_db()

            query.message.reply_text(
                "✅ پلن حذف شد"
            )

            return

        # =====================
        # TEST ON
        # =====================

        if data == "test_on":

            if not is_admin(uid):
                return

            db["test_enabled"] = True

            db["test_reason"] = ""

            save_db()

            query.message.reply_text(
                "✅ تست روشن شد"
            )

            return

        # =====================
        # TEST OFF
        # =====================

        if data == "test_off":

            if not is_admin(uid):
                return

            state[uid] = {

                "step":
                "test_reason"

            }

            query.message.reply_text(
                "❌ دلیل خاموش شدن تست:"
            )

            return

        # =====================
        # APPROVE PAYMENT
        # =====================

        if data.startswith("approve_"):

            if not is_admin(uid):
                return

            parts = data.split("_")

            user_id = parts[1]

            pid = int(parts[2])

            pay_type = parts[3]

            plan = None

            for p in db["plans"]:

                if p["id"] == pid:
                    plan = p

            if not plan:

                query.message.reply_text(
                    "❌ پلن یافت نشد"
                )

                return

            # خرید ترکیبی
            if pay_type == "mix":

                wallet = db["users"][user_id]["wallet"]

                db["users"][user_id]["wallet"] = 0

                save_db()

            ok = deliver_config(

                context,

                user_id,

                plan

            )

            # اگر ارسال خودکار موفق بود
            if ok:

                query.message.reply_text(
                    "✅ کانفیگ ارسال شد"
                )

            else:

                # ارسال دستی
                state[uid] = {

                    "step":
                    "manual_config",

                    "target":
                    user_id,

                    "plan":
                    plan

                }

                query.message.reply_text(

                    "⚠️ ارسال خودکار ممکن نبود\n\n"

                    "کانفیگ را دستی ارسال کن"

                )

            return

        # =====================
        # REJECT PAYMENT
        # =====================

        if data.startswith("reject_"):

            if not is_admin(uid):
                return

            user_id = data.split("_")[1]

            state[uid] = {

                "step":
                "reject_reason",

                "target":
                user_id

            }

            query.message.reply_text(
                "❌ دلیل رد را ارسال کن:"
            )

            return

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

        query.message.reply_text(
            "❌ خطا در عملیات"
        )

# =========================
# HANDLE PHOTO
# =========================

def handle_photo(update, context):

    try:

        uid = str(
            update.effective_user.id
        )

        ensure_user(uid)

        st = state.get(uid, {})

        # =====================
        # WALLET RECEIPT
        # =====================

        if st.get("step") == "wallet_receipt":

            amount = st["amount"]

            caption = (

                f"💳 درخواست شارژ کیف پول\n\n"

                f"👤 کاربر: {uid}\n"

                f"💰 مبلغ: {amount:,} تومان"

            )

            buttons = [

                [

                    InlineKeyboardButton(

                        "✅ تایید",

                        callback_data=
                        f"walletok_{uid}_{amount}"

                    ),

                    InlineKeyboardButton(

                        "❌ رد",

                        callback_data=
                        f"walletreject_{uid}"

                    )

                ]

            ]

            context.bot.send_photo(

                MAIN_ADMIN,

                photo=
                update.message.photo[-1].file_id,

                caption=caption,

                reply_markup=
                InlineKeyboardMarkup(buttons)

            )

            update.message.reply_text(
                db["texts"]["wait_admin"]
            )

            state[uid] = {}

            return

        # =====================
        # PLAN RECEIPT
        # =====================

        if st.get("step") == "wait_receipt":

            plan = st["plan"]

            mixed = st.get("mixed", False)

            payment_type = (
                "mix"
                if mixed
                else "card"
            )

            caption = (

                f"🧾 فیش جدید\n\n"

                f"👤 کاربر: {uid}\n"

                f"📦 پلن: {plan['name']}\n"

                f"💰 مبلغ: "
                f"{plan['price']:,}"

            )

            buttons = [

                [

                    InlineKeyboardButton(

                        "✅ تایید",

                        callback_data=
                        f"approve_{uid}_{plan['id']}_{payment_type}"

                    ),

                    InlineKeyboardButton(

                        "❌ رد",

                        callback_data=
                        f"reject_{uid}"

                    )

                ]

            ]

            context.bot.send_photo(

                MAIN_ADMIN,

                photo=
                update.message.photo[-1].file_id,

                caption=caption,

                reply_markup=
                InlineKeyboardMarkup(buttons)

            )

            update.message.reply_text(
                db["texts"]["wait_admin"]
            )

            state[uid] = {}

            return

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

        update.message.reply_text(
            "❌ خطا در پردازش فیش"
        )

# =========================
# HANDLE DOCUMENT
# =========================

def handle_document(update, context):

    try:

        uid = str(
            update.effective_user.id
        )

        if not is_admin(uid):
            return

        st = state.get(uid, {})

        # =====================
        # RESTORE DATABASE
        # =====================

        if st.get("step") == "restore_db":

            file = update.message.document

            tg_file = context.bot.get_file(
                file.file_id
            )

            tg_file.download("restore.json")

            with open(
                "restore.json",
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            global db

            db = data

            save_db()

            state[uid] = {}

            update.message.reply_text(
                "✅ بکاپ ریستور شد"
            )

            return

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

        update.message.reply_text(
            "❌ خطا در ریستور"
                )
        # =========================
# MAIN.PY - PART 5
# ادامه مستقیم فایل
# =========================

# =========================
# EXTRA CALLBACKS
# =========================

def extra_callbacks(update, context):

    try:

        query = update.callback_query

        query.answer()

        data = query.data

        uid = str(query.from_user.id)

        # =====================
        # WALLET ACCEPT
        # =====================

        if data.startswith("walletok_"):

            if not is_admin(uid):
                return

            parts = data.split("_")

            target = parts[1]

            amount = int(parts[2])

            if str(target) not in db["users"]:

                query.message.reply_text(
                    "❌ کاربر یافت نشد"
                )

                return

            db["users"][str(target)]["wallet"] += amount

            save_db()

            context.bot.send_message(

                int(target),

                db["texts"]["wallet_ok"]

            )

            query.message.reply_text(
                "✅ کیف پول شارژ شد"
            )

            return

        # =====================
        # WALLET REJECT
        # =====================

        if data.startswith("walletreject_"):

            if not is_admin(uid):
                return

            target = data.split("_")[1]

            state[uid] = {

                "step":
                "reject_reason",

                "target":
                target

            }

            query.message.reply_text(
                "❌ دلیل رد شارژ کیف پول:"
            )

            return

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

# =========================
# EXTRA TEXT STATES
# =========================

def extra_text_states(update, context):

    try:

        uid = str(
            update.effective_user.id
        )

        text = update.message.text

        st = state.get(uid, {})

        # =====================
        # TEST REASON
        # =====================

        if st.get("step") == "test_reason":

            db["test_enabled"] = False

            db["test_reason"] = text

            save_db()

            state[uid] = {}

            update.message.reply_text(
                "✅ تست خاموش شد"
            )

            return True

        return False

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

        return False

# =========================
# SAFE SEND
# =========================

def safe_send(bot, chat_id, text):

    try:

        bot.send_message(
            int(chat_id),
            text
        )

        return True

    except:

        return False

# =========================
# MAIN
# =========================

def main():

    try:

        logger.info(
            "BOT STARTED..."
        )

        # WEB SERVER
        Thread(
            target=run_web,
            daemon=True
        ).start()

        # TELEGRAM
        updater = Updater(
            TOKEN,
            use_context=True
        )

        dp = updater.dispatcher

        # =====================
        # COMMANDS
        # =====================

        dp.add_handler(

            CommandHandler(
                "start",
                start
            )

        )

        # =====================
        # CALLBACKS
        # =====================

        dp.add_handler(

            CallbackQueryHandler(
                handle_callback
            )

        )

        dp.add_handler(

            CallbackQueryHandler(
                extra_callbacks
            )

        )

        # =====================
        # PHOTOS
        # =====================

        dp.add_handler(

            MessageHandler(
                Filters.photo,
                handle_photo
            )

        )

        # =====================
        # DOCUMENTS
        # =====================

        dp.add_handler(

            MessageHandler(
                Filters.document,
                handle_document
            )

        )

        # =====================
        # TEXT HANDLER
        # =====================

        def text_router(update, context):

            try:

                handled = extra_text_states(
                    update,
                    context
                )

                if handled:
                    return

                handle_text(
                    update,
                    context
                )

            except Exception as e:

                logger.error(
                    traceback.format_exc()
                )

        dp.add_handler(

            MessageHandler(

                Filters.text
                &
                ~Filters.command,

                text_router

            )

        )

        # =====================
        # START BOT
        # =====================

        updater.start_polling()

        logger.info(
            "BOT IS RUNNING"
        )

        updater.idle()

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

# =========================
# RUN
# =========================

if __name__ == "__main__":

    main()

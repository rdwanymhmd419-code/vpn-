# =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 1
# main.py
# =========================================

import os
import json
import logging
import traceback
import requests
import random
import string
from datetime import datetime
from threading import Thread

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

# =========================================
# LOGGING
# =========================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# =========================================
# FLASK
# =========================================

app = Flask(__name__)

@app.route("/")
def home():
    return "BOT ONLINE", 200

def run_web():
    port = int(
        os.environ.get("PORT", 8080)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )

# =========================================
# TOKEN
# =========================================

TOKEN = "8681405252:AAH7ONTudaE34evtbxWeLdk0dtZc_XkULEA"

# =========================================
# ADMINS
# =========================================

MAIN_ADMIN = 5993860770

ADMINS = [
    5993860770
]

MAIN_ADMIN_STR = str(MAIN_ADMIN)

# =========================================
# XUI SETTINGS
# =========================================

XUI_URL = "http://87.248.152.205:8081"

XUI_USERNAME = "amir"

XUI_PASSWORD = "amirreza871221"

# =========================================
# DATABASE
# =========================================

DB_FILE = "data.json"

# =========================================
# STATES
# =========================================

state = {}

# =========================================
# DEFAULT DATABASE
# =========================================

default_db = {

    "bot_enabled": True,

    "brand": "تک نت وی‌پی‌ان",

    "support": "@Support",

    "guide": "@Guide",

    "auto_send": True,

    "manual_send": False,

    "payment_methods": {

        "card": True,
        "gateway": False,
        "crypto": False

    },

    "card": {

        "number": "6277601368776066",
        "name": "محمد رضوانی"

    },

    "texts": {

        "welcome":
        "🔥 به {brand} خوش آمدید",

        "wait_admin":
        "⏳ منتظر تایید ادمین باشید",

        "wait_manual":
        "⏳ منتظر ارسال دستی ادمین باشید",

        "config_send":
        "🎉 سرویس شما آماده شد\n\n"
        "👤 نام: {name}\n"
        "📦 حجم: {volume}GB\n"
        "📅 اعتبار: {days} روز\n\n"
        "🔗 کانفیگ:\n\n"
        "{config}\n\n"
        "❤️ ممنون از خرید شما",

        "support":
        "🆘 پشتیبانی:\n{support}",

        "guide":
        "📚 آموزش:\n{guide}"

    },

    "wallet_prices": [

        100000,
        300000,
        500000,
        1000000,
        2000000

    ],

    "test_settings": {

        "enabled": True,
        "volume": 1,
        "days": 1

    },

    "categories": [

        {
            "id": 1,
            "name": "🚀 قوی"
        },

        {
            "id": 2,
            "name": "💎 ارزان"
        },

        {
            "id": 3,
            "name": "👥 چند کاربره"
        }

    ],

    "plans": [

        {
            "id": 1,
            "cat": 1,
            "name": "20GB",
            "volume": 20,
            "days": 30,
            "users": 1,
            "price": 80000
        },

        {
            "id": 2,
            "cat": 1,
            "name": "50GB",
            "volume": 50,
            "days": 30,
            "users": 1,
            "price": 150000
        },

        {
            "id": 3,
            "cat": 2,
            "name": "10GB",
            "volume": 10,
            "days": 30,
            "users": 1,
            "price": 50000
        }

    ],

    "configs": {},

    "users": {}

}

# =========================================
# LOAD DATABASE
# =========================================

def load_db():

    global db

    try:

        if os.path.exists(DB_FILE):

            with open(
                DB_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                db = json.load(f)

                logger.info(
                    "DATABASE LOADED"
                )

        else:

            db = default_db

            save_db()

    except Exception as e:

        logger.error(e)

        db = default_db

        save_db()

# =========================================
# SAVE DATABASE
# =========================================

def save_db():

    try:

        with open(
            DB_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                db,
                f,
                ensure_ascii=False,
                indent=4
            )

    except Exception as e:

        logger.error(e)

# =========================================
# LOAD DB NOW
# =========================================

load_db()

# =========================================
# CREATE USER
# =========================================

def ensure_user(uid):

    uid = str(uid)

    if uid not in db["users"]:

        db["users"][uid] = {

            "wallet": 0,

            "services": [],

            "joined": str(datetime.now()),

            "invited_by": None,

            "total_buy": 0,

            "test_used": False

        }

        save_db()

# =========================================
# ADMIN CHECK
# =========================================

def is_admin(uid):

    return int(uid) in ADMINS

# =========================================
# RANDOM EMAIL
# =========================================

def random_email():

    chars = string.ascii_lowercase + string.digits

    name = ''.join(
        random.choice(chars)
        for _ in range(8)
    )

    return f"{name}@gmail.com"

# =========================================
# RANDOM PASSWORD
# =========================================

def random_password():

    chars = string.ascii_letters + string.digits

    return ''.join(
        random.choice(chars)
        for _ in range(12)
    )

# =========================================
# XUI LOGIN
# =========================================

session = requests.Session()

def xui_login():

    try:

        url = f"{XUI_URL}/login"

        data = {

            "username": XUI_USERNAME,
            "password": XUI_PASSWORD

        }

        r = session.post(
            url,
            data=data,
            timeout=20
        )

        if r.status_code == 200:

            logger.info(
                "XUI LOGIN SUCCESS"
            )

            return True

        return False

    except Exception as e:

        logger.error(e)

        return False

# =========================================
# XUI CREATE CLIENT
# =========================================

def create_xui_client(

    volume_gb,
    days,
    limit_ip

):

    try:

        email = random_email()

        password = random_password()

        total_bytes = (
            volume_gb *
            1024 *
            1024 *
            1024
        )

        expiry = int(
            (
                datetime.now().timestamp() +
                (days * 86400)
            ) * 1000
        )

        payload = {

            "id": 1,

            "settings": json.dumps({

                "clients": [

                    {

                        "id": ''.join(
                            random.choice(
                                string.hexdigits
                            )
                            for _ in range(32)
                        ),

                        "email": email,

                        "limitIp": limit_ip,

                        "totalGB": total_bytes,

                        "expiryTime": expiry,

                        "enable": True,

                        "tgId": "",

                        "subId": password

                    }

                ]

            })

        }

        url = f"{XUI_URL}/panel/api/inbounds/addClient"

        r = session.post(
            url,
            json=payload,
            timeout=20
        )

        if r.status_code == 200:

            return {

                "email": email,
                "password": password

            }

        return None

    except Exception as e:

        logger.error(e)

        return None
      # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 2
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# MAIN MENU
# =========================================

def main_menu(uid):

    keyboard = [

        ["💰 خرید سرویس"],

        ["👛 کیف پول", "🎁 تست"],

        ["📂 سرویس‌های من", "⏳ تمدید"],

        ["👤 پشتیبانی", "📚 آموزش"]

    ]

    if is_admin(uid):

        keyboard.append(
            ["⚙️ مدیریت"]
        )

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

# =========================================
# ADMIN MENU
# =========================================

def admin_menu():

    keyboard = [

        ["📦 مدیریت پلن‌ها"],

        ["📁 مدیریت دسته‌بندی"],

        ["🔗 افزودن کانفیگ"],

        ["💳 روش پرداخت"],

        ["👛 تنظیمات کیف پول"],

        ["🎁 تنظیمات تست"],

        ["📨 ارسال همگانی"],

        ["👤 ارسال پیام"],

        ["📌 پین همگانی"],

        ["🤖 تنظیمات ربات"],

        ["💾 بکاپ"],

        ["🔙 برگشت"]

    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

# =========================================
# BACK MENU
# =========================================

def back_menu():

    return ReplyKeyboardMarkup(
        [["🔙 برگشت"]],
        resize_keyboard=True
    )

# =========================================
# SHOW CATEGORIES
# =========================================

def show_categories(

    update

):

    keyboard = []

    for cat in db["categories"]:

        keyboard.append([

            InlineKeyboardButton(

                cat["name"],

                callback_data=f"cat_{cat['id']}"

            )

        ])

    update.message.reply_text(

        "📂 دسته‌بندی مورد نظر را انتخاب کنید",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )

# =========================================
# SHOW PLANS
# =========================================

def show_plans(

    query,

    cat_id

):

    keyboard = []

    found = False

    for plan in db["plans"]:

        if plan["cat"] == cat_id:

            found = True

            txt = (

                f"{plan['name']} | "

                f"{plan['volume']}GB | "

                f"{plan['days']} روز | "

                f"{plan['price']:,}"

            )

            keyboard.append([

                InlineKeyboardButton(

                    txt,

                    callback_data=f"plan_{plan['id']}"

                )

            ])

    if not found:

        query.message.reply_text(

            "❌ پلنی وجود ندارد"

        )

        return

    query.message.reply_text(

        "📦 پلن مورد نظر را انتخاب کنید",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )

# =========================================
# WALLET MENU
# =========================================

def wallet_menu():

    keyboard = []

    for amount in db["wallet_prices"]:

        keyboard.append([

            InlineKeyboardButton(

                f"{amount:,} تومان",

                callback_data=f"wallet_{amount}"

            )

        ])

    keyboard.append([

        InlineKeyboardButton(

            "💰 مبلغ دلخواه",

            callback_data="wallet_custom"

        )

    ])

    return InlineKeyboardMarkup(
        keyboard
    )

# =========================================
# PAYMENT MENU
# =========================================

def payment_menu():

    keyboard = []

    if db["payment_methods"]["card"]:

        keyboard.append([

            InlineKeyboardButton(

                "💳 کارت به کارت",

                callback_data="pay_card"

            )

        ])

    if db["payment_methods"]["gateway"]:

        keyboard.append([

            InlineKeyboardButton(

                "🏦 درگاه پرداخت",

                callback_data="pay_gateway"

            )

        ])

    if db["payment_methods"]["crypto"]:

        keyboard.append([

            InlineKeyboardButton(

                "🪙 رمز ارز",

                callback_data="pay_crypto"

            )

        ])

    return InlineKeyboardMarkup(
        keyboard
    )

# =========================================
# START
# =========================================

def start(

    update,

    context

):

    try:

        uid = str(
            update.effective_user.id
        )

        ensure_user(uid)

        # =====================================
        # BOT OFF
        # =====================================

        if not db["bot_enabled"]:

            if not is_admin(uid):

                update.message.reply_text(

                    "🔴 ربات موقتاً خاموش است"

                )

                return

        # =====================================
        # INVITE SYSTEM
        # =====================================

        if context.args:

            inviter = context.args[0]

            if inviter != uid:

                if not db["users"][uid]["invited_by"]:

                    db["users"][uid]["invited_by"] = inviter

                    save_db()

        # =====================================
        # WELCOME
        # =====================================

        txt = db["texts"]["welcome"]

        txt = txt.replace(

            "{brand}",

            db["brand"]

        )

        update.message.reply_text(

            txt,

            reply_markup=main_menu(uid)

        )

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

# =========================================
# TEXT HANDLER
# =========================================

def text_handler(

    update,

    context

):

    try:

        uid = str(
            update.effective_user.id
        )

        text = update.message.text

        ensure_user(uid)

        # =====================================
        # BOT OFF
        # =====================================

        if not db["bot_enabled"]:

            if not is_admin(uid):

                update.message.reply_text(

                    "🔴 ربات خاموش است"

                )

                return

        # =====================================
        # BACK
        # =====================================

        if text == "🔙 برگشت":

            state[uid] = {}

            update.message.reply_text(

                "🏠 منوی اصلی",

                reply_markup=main_menu(uid)

            )

            return

        # =====================================
        # BUY SERVICE
        # =====================================

        if text == "💰 خرید سرویس":

            show_categories(update)

            return

        # =====================================
        # WALLET
        # =====================================

        if text == "👛 کیف پول":

            wallet = db["users"][uid]["wallet"]

            update.message.reply_text(

                f"👛 کیف پول شما\n\n"

                f"💰 موجودی: {wallet:,} تومان",

                reply_markup=wallet_menu()

            )

            return

        # =====================================
        # SERVICES
        # =====================================

        if text == "📂 سرویس‌های من":

            services = db["users"][uid]["services"]

            if len(services) == 0:

                update.message.reply_text(

                    "❌ سرویسی ندارید"

                )

                return

            msg = "📂 سرویس‌های شما\n\n"

            for s in services:

                msg += (

                    f"📦 {s['name']}\n"

                    f"📊 {s['volume']}GB\n"

                    f"📅 {s['days']} روز\n\n"

                )

            update.message.reply_text(msg)

            return

        # =====================================
        # TEST
        # =====================================

        if text == "🎁 تست":

            if not db["test_settings"]["enabled"]:

                update.message.reply_text(

                    "❌ تست غیرفعال است"

                )

                return

            if db["users"][uid]["test_used"]:

                update.message.reply_text(

                    "❌ قبلاً تست گرفته‌اید"

                )

                return

            volume = db["test_settings"]["volume"]

            days = db["test_settings"]["days"]

            xui_login()

            result = create_xui_client(

                volume,
                days,
                1
            )

            if not result:

                update.message.reply_text(

                    "❌ خطا در ساخت تست"

                )

                return

            config = (

                f"vless://"

                f"{result['password']}"

                f"@server.com:443"

            )

            txt = (

                "🎁 تست شما آماده شد\n\n"

                f"📊 حجم: {volume}GB\n"

                f"📅 مدت: {days} روز\n\n"

                f"{config}"

            )

            update.message.reply_text(txt)

            db["users"][uid]["test_used"] = True

            save_db()

            return

        # =====================================
        # SUPPORT
        # =====================================

        if text == "👤 پشتیبانی":

            txt = db["texts"]["support"]

            txt = txt.replace(

                "{support}",

                db["support"]

            )

            update.message.reply_text(txt)

            return

        # =====================================
        # GUIDE
        # =====================================

        if text == "📚 آموزش":

            txt = db["texts"]["guide"]

            txt = txt.replace(

                "{guide}",

                db["guide"]

            )

            update.message.reply_text(txt)

            return
          # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 3
# ادامه مستقیم فایل main.py
# =========================================

        # =====================================
        # RENEW
        # =====================================

        if text == "⏳ تمدید":

            services = db["users"][uid]["services"]

            if len(services) == 0:

                update.message.reply_text(

                    "❌ سرویسی برای تمدید ندارید"

                )

                return

            keyboard = []

            for i, srv in enumerate(services):

                keyboard.append([

                    InlineKeyboardButton(

                        f"{srv['name']} | {srv['volume']}GB",

                        callback_data=f"renew_{i}"

                    )

                ])

            update.message.reply_text(

                "♻️ سرویس مورد نظر را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # ADMIN PANEL
        # =====================================

        if text == "⚙️ مدیریت":

            if not is_admin(uid):

                return

            update.message.reply_text(

                "⚙️ پنل مدیریت",

                reply_markup=admin_menu()

            )

            return

        # =====================================
        # CATEGORY MANAGEMENT
        # =====================================

        if text == "📁 مدیریت دسته‌بندی":

            if not is_admin(uid):

                return

            keyboard = [

                ["➕ افزودن دسته"],

                ["✏️ ویرایش دسته"],

                ["🗑 حذف دسته"],

                ["📋 لیست دسته‌ها"],

                ["🔙 برگشت"]

            ]

            update.message.reply_text(

                "📁 مدیریت دسته‌بندی",

                reply_markup=ReplyKeyboardMarkup(

                    keyboard,

                    resize_keyboard=True

                )

            )

            return

        # =====================================
        # ADD CATEGORY
        # =====================================

        if text == "➕ افزودن دسته":

            state[uid] = {

                "step": "add_category"

            }

            update.message.reply_text(

                "✍️ نام دسته را ارسال کنید",

                reply_markup=back_menu()

            )

            return

        # =====================================
        # LIST CATEGORY
        # =====================================

        if text == "📋 لیست دسته‌ها":

            msg = "📂 لیست دسته‌بندی‌ها\n\n"

            for cat in db["categories"]:

                msg += (

                    f"🆔 {cat['id']} - "

                    f"{cat['name']}\n"

                )

            update.message.reply_text(msg)

            return

        # =====================================
        # DELETE CATEGORY
        # =====================================

        if text == "🗑 حذف دسته":

            keyboard = []

            for cat in db["categories"]:

                keyboard.append([

                    InlineKeyboardButton(

                        cat["name"],

                        callback_data=f"delete_cat_{cat['id']}"

                    )

                ])

            update.message.reply_text(

                "🗑 دسته مورد نظر را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # EDIT CATEGORY
        # =====================================

        if text == "✏️ ویرایش دسته":

            keyboard = []

            for cat in db["categories"]:

                keyboard.append([

                    InlineKeyboardButton(

                        cat["name"],

                        callback_data=f"edit_cat_{cat['id']}"

                    )

                ])

            update.message.reply_text(

                "✏️ دسته را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # PLAN MANAGEMENT
        # =====================================

        if text == "📦 مدیریت پلن‌ها":

            keyboard = [

                ["➕ افزودن پلن"],

                ["✏️ ویرایش پلن"],

                ["🗑 حذف پلن"],

                ["📋 لیست پلن‌ها"],

                ["🔙 برگشت"]

            ]

            update.message.reply_text(

                "📦 مدیریت پلن‌ها",

                reply_markup=ReplyKeyboardMarkup(

                    keyboard,

                    resize_keyboard=True

                )

            )

            return

        # =====================================
        # LIST PLANS
        # =====================================

        if text == "📋 لیست پلن‌ها":

            msg = "📦 لیست پلن‌ها\n\n"

            for plan in db["plans"]:

                msg += (

                    f"🆔 {plan['id']}\n"

                    f"📦 {plan['name']}\n"

                    f"📊 {plan['volume']}GB\n"

                    f"📅 {plan['days']} روز\n"

                    f"👥 {plan['users']} کاربر\n"

                    f"💰 {plan['price']:,}\n\n"

                )

            update.message.reply_text(msg)

            return

        # =====================================
        # ADD PLAN
        # =====================================

        if text == "➕ افزودن پلن":

            keyboard = []

            for cat in db["categories"]:

                keyboard.append([

                    InlineKeyboardButton(

                        cat["name"],

                        callback_data=f"select_cat_{cat['id']}"

                    )

                ])

            update.message.reply_text(

                "📂 دسته پلن را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # DELETE PLAN
        # =====================================

        if text == "🗑 حذف پلن":

            keyboard = []

            for plan in db["plans"]:

                keyboard.append([

                    InlineKeyboardButton(

                        plan["name"],

                        callback_data=f"delete_plan_{plan['id']}"

                    )

                ])

            update.message.reply_text(

                "🗑 پلن مورد نظر را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # EDIT PLAN
        # =====================================

        if text == "✏️ ویرایش پلن":

            keyboard = []

            for plan in db["plans"]:

                keyboard.append([

                    InlineKeyboardButton(

                        plan["name"],

                        callback_data=f"edit_plan_{plan['id']}"

                    )

                ])

            update.message.reply_text(

                "✏️ پلن مورد نظر را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # ADD CONFIG
        # =====================================

        if text == "🔗 افزودن کانفیگ":

            keyboard = []

            for plan in db["plans"]:

                keyboard.append([

                    InlineKeyboardButton(

                        plan["name"],

                        callback_data=f"config_plan_{plan['id']}"

                    )

                ])

            update.message.reply_text(

                "📦 پلن را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # WALLET SETTINGS
        # =====================================

        if text == "👛 تنظیمات کیف پول":

            keyboard = [

                ["➕ افزودن مبلغ"],

                ["🗑 حذف مبلغ"],

                ["📋 لیست مبالغ"],

                ["🔙 برگشت"]

            ]

            update.message.reply_text(

                "👛 تنظیمات کیف پول",

                reply_markup=ReplyKeyboardMarkup(

                    keyboard,

                    resize_keyboard=True

                )

            )

            return

        # =====================================
        # TEST SETTINGS
        # =====================================

        if text == "🎁 تنظیمات تست":

            status = "🟢 فعال"

            if not db["test_settings"]["enabled"]:

                status = "🔴 غیرفعال"

            keyboard = [

                ["🟢 فعال", "🔴 غیرفعال"],

                ["⚙️ تنظیم تست"],

                ["🔙 برگشت"]

            ]

            update.message.reply_text(

                f"🎁 وضعیت تست: {status}",

                reply_markup=ReplyKeyboardMarkup(

                    keyboard,

                    resize_keyboard=True

                )

            )

            return

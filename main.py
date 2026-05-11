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
# =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 4
# ادامه مستقیم فایل main.py
# =========================================

        # =====================================
        # TEST ENABLE
        # =====================================

        if text == "🟢 فعال":

            db["test_settings"]["enabled"] = True

            save_db()

            update.message.reply_text(

                "✅ تست فعال شد"

            )

            return

        # =====================================
        # TEST DISABLE
        # =====================================

        if text == "🔴 غیرفعال":

            db["test_settings"]["enabled"] = False

            save_db()

            update.message.reply_text(

                "❌ تست غیرفعال شد"

            )

            return

        # =====================================
        # TEST CONFIG
        # =====================================

        if text == "⚙️ تنظیم تست":

            state[uid] = {

                "step": "test_volume"

            }

            update.message.reply_text(

                "📊 حجم تست را ارسال کنید\n\n"
                "1 تا 100",

                reply_markup=back_menu()

            )

            return

        # =====================================
        # PAYMENT SETTINGS
        # =====================================

        if text == "💳 روش پرداخت":

            card = "🟢"

            gateway = "🔴"

            crypto = "🔴"

            if db["payment_methods"]["gateway"]:
                gateway = "🟢"

            if db["payment_methods"]["crypto"]:
                crypto = "🟢"

            keyboard = [

                ["💳 کارت به کارت"],

                ["🏦 درگاه پرداخت"],

                ["🪙 رمز ارز"],

                ["🔙 برگشت"]

            ]

            update.message.reply_text(

                f"💳 وضعیت پرداخت\n\n"

                f"{card} کارت به کارت\n"
                f"{gateway} درگاه\n"
                f"{crypto} رمز ارز",

                reply_markup=ReplyKeyboardMarkup(

                    keyboard,

                    resize_keyboard=True

                )

            )

            return

        # =====================================
        # BOT SETTINGS
        # =====================================

        if text == "🤖 تنظیمات ربات":

            auto_send = "🟢"

            manual_send = "🔴"

            if not db["auto_send"]:
                auto_send = "🔴"

            if db["manual_send"]:
                manual_send = "🟢"

            keyboard = [

                ["🟢 ارسال خودکار"],

                ["📨 ارسال دستی"],

                ["➕ افزودن ادمین"],

                ["✏️ ویرایش متن‌ها"],

                ["🔴 خاموش کردن ربات"],

                ["🟢 روشن کردن ربات"],

                ["🔙 برگشت"]

            ]

            update.message.reply_text(

                f"🤖 تنظیمات ربات\n\n"

                f"{auto_send} ارسال خودکار\n"
                f"{manual_send} ارسال دستی",

                reply_markup=ReplyKeyboardMarkup(

                    keyboard,

                    resize_keyboard=True

                )

            )

            return

        # =====================================
        # AUTO SEND
        # =====================================

        if text == "🟢 ارسال خودکار":

            db["auto_send"] = True

            save_db()

            update.message.reply_text(

                "✅ ارسال خودکار فعال شد"

            )

            return

        # =====================================
        # MANUAL SEND
        # =====================================

        if text == "📨 ارسال دستی":

            db["manual_send"] = not db["manual_send"]

            save_db()

            if db["manual_send"]:

                update.message.reply_text(

                    "✅ ارسال دستی فعال شد"

                )

            else:

                update.message.reply_text(

                    "❌ ارسال دستی غیرفعال شد"

                )

            return

        # =====================================
        # BOT OFF
        # =====================================

        if text == "🔴 خاموش کردن ربات":

            db["bot_enabled"] = False

            save_db()

            update.message.reply_text(

                "🔴 ربات خاموش شد"

            )

            return

        # =====================================
        # BOT ON
        # =====================================

        if text == "🟢 روشن کردن ربات":

            db["bot_enabled"] = True

            save_db()

            update.message.reply_text(

                "🟢 ربات روشن شد"

            )

            return

        # =====================================
        # ADD ADMIN
        # =====================================

        if text == "➕ افزودن ادمین":

            if int(uid) != MAIN_ADMIN:

                update.message.reply_text(

                    "❌ فقط ادمین اصلی"

                )

                return

            state[uid] = {

                "step": "add_admin"

            }

            update.message.reply_text(

                "👤 آیدی عددی ادمین را ارسال کنید",

                reply_markup=back_menu()

            )

            return

        # =====================================
        # EDIT TEXTS
        # =====================================

        if text == "✏️ ویرایش متن‌ها":

            keyboard = [

                ["👋 خوش آمد"],

                ["📦 متن ارسال کانفیگ"],

                ["⏳ متن انتظار"],

                ["📚 آموزش"],

                ["👤 پشتیبانی"],

                ["🔙 برگشت"]

            ]

            update.message.reply_text(

                "✏️ متن مورد نظر را انتخاب کنید",

                reply_markup=ReplyKeyboardMarkup(

                    keyboard,

                    resize_keyboard=True

                )

            )

            return

        # =====================================
        # BROADCAST
        # =====================================

        if text == "📨 ارسال همگانی":

            state[uid] = {

                "step": "broadcast"

            }

            update.message.reply_text(

                "📨 پیام را ارسال کنید",

                reply_markup=back_menu()

            )

            return

        # =====================================
        # PRIVATE MESSAGE
        # =====================================

        if text == "👤 ارسال پیام":

            state[uid] = {

                "step": "private_user"

            }

            update.message.reply_text(

                "🆔 آیدی عددی کاربر را ارسال کنید",

                reply_markup=back_menu()

            )

            return

        # =====================================
        # PIN MESSAGE
        # =====================================

        if text == "📌 پین همگانی":

            state[uid] = {

                "step": "pin_message"

            }

            update.message.reply_text(

                "📌 پیام را ارسال کنید",

                reply_markup=back_menu()

            )

            return

        # =====================================
        # BACKUP
        # =====================================

        if text == "💾 بکاپ":

            keyboard = [

                ["📥 دریافت بکاپ"],

                ["📤 بازگردانی بکاپ"],

                ["🔙 برگشت"]

            ]

            update.message.reply_text(

                "💾 مدیریت بکاپ",

                reply_markup=ReplyKeyboardMarkup(

                    keyboard,

                    resize_keyboard=True

                )

            )

            return

        # =====================================
        # GET BACKUP
        # =====================================

        if text == "📥 دریافت بکاپ":

            with open(

                DB_FILE,

                "rb"

            ) as f:

                update.message.reply_document(

                    f,

                    filename="backup.json"

                )

            return

        # =====================================
        # RESTORE BACKUP
        # =====================================

        if text == "📤 بازگردانی بکاپ":

            state[uid] = {

                "step": "restore_backup"

            }

            update.message.reply_text(

                "📤 فایل بکاپ را ارسال کنید",

                reply_markup=back_menu()

            )

            return
           # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 5
# ادامه مستقیم فایل main.py
# =========================================

        # =====================================
        # STATES
        # =====================================

        if uid in state:

            step = state[uid].get("step")

            # =================================
            # ADD CATEGORY
            # =================================

            if step == "add_category":

                new_id = 1

                if db["categories"]:

                    new_id = max(

                        c["id"]
                        for c in db["categories"]

                    ) + 1

                db["categories"].append({

                    "id": new_id,

                    "name": text

                })

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ دسته اضافه شد",

                    reply_markup=admin_menu()

                )

                return

            # =================================
            # TEST VOLUME
            # =================================

            if step == "test_volume":

                try:

                    volume = int(text)

                    if volume < 1 or volume > 100:

                        update.message.reply_text(

                            "❌ عدد نامعتبر"

                        )

                        return

                    state[uid] = {

                        "step": "test_days",

                        "volume": volume

                    }

                    update.message.reply_text(

                        "📅 مدت تست را ارسال کنید\n"
                        "1 تا 30"

                    )

                    return

                except:

                    update.message.reply_text(

                        "❌ فقط عدد"

                    )

                    return

            # =================================
            # TEST DAYS
            # =================================

            if step == "test_days":

                try:

                    days = int(text)

                    if days < 1 or days > 30:

                        update.message.reply_text(

                            "❌ عدد نامعتبر"

                        )

                        return

                    volume = state[uid]["volume"]

                    db["test_settings"]["volume"] = volume

                    db["test_settings"]["days"] = days

                    save_db()

                    state[uid] = {}

                    update.message.reply_text(

                        "✅ تنظیمات تست ذخیره شد",

                        reply_markup=admin_menu()

                    )

                    return

                except:

                    update.message.reply_text(

                        "❌ فقط عدد"

                    )

                    return

            # =================================
            # ADD ADMIN
            # =================================

            if step == "add_admin":

                try:

                    admin_id = int(text)

                    if admin_id not in ADMINS:

                        ADMINS.append(admin_id)

                    state[uid] = {}

                    update.message.reply_text(

                        "✅ ادمین اضافه شد",

                        reply_markup=admin_menu()

                    )

                    return

                except:

                    update.message.reply_text(

                        "❌ آیدی نامعتبر"

                    )

                    return

            # =================================
            # PRIVATE USER
            # =================================

            if step == "private_user":

                state[uid] = {

                    "step": "private_message",

                    "target": text

                }

                update.message.reply_text(

                    "📨 پیام را ارسال کنید"

                )

                return

            # =================================
            # PRIVATE MESSAGE
            # =================================

            if step == "private_message":

                target = state[uid]["target"]

                try:

                    context.bot.send_message(

                        int(target),

                        text

                    )

                    update.message.reply_text(

                        "✅ ارسال شد"

                    )

                except:

                    update.message.reply_text(

                        "❌ خطا در ارسال"

                    )

                state[uid] = {}

                return

            # =================================
            # BROADCAST
            # =================================

            if step == "broadcast":

                success = 0

                failed = 0

                for user_id in db["users"]:

                    try:

                        context.bot.send_message(

                            int(user_id),

                            text

                        )

                        success += 1

                    except:

                        failed += 1

                state[uid] = {}

                update.message.reply_text(

                    f"✅ انجام شد\n\n"

                    f"موفق: {success}\n"

                    f"ناموفق: {failed}",

                    reply_markup=admin_menu()

                )

                return

            # =================================
            # PIN MESSAGE
            # =================================

            if step == "pin_message":

                success = 0

                failed = 0

                for user_id in db["users"]:

                    try:

                        msg = context.bot.send_message(

                            int(user_id),

                            text

                        )

                        context.bot.pin_chat_message(

                            int(user_id),

                            msg.message_id

                        )

                        success += 1

                    except:

                        failed += 1

                state[uid] = {}

                update.message.reply_text(

                    f"📌 انجام شد\n\n"

                    f"موفق: {success}\n"

                    f"ناموفق: {failed}",

                    reply_markup=admin_menu()

                )

                return

            # =================================
            # EDIT TEXTS
            # =================================

            if text == "👋 خوش آمد":

                state[uid] = {

                    "step": "edit_welcome"

                }

                update.message.reply_text(

                    "✍️ متن جدید را ارسال کنید"

                )

                return

            if text == "📦 متن ارسال کانفیگ":

                state[uid] = {

                    "step": "edit_config"

                }

                update.message.reply_text(

                    "✍️ متن جدید را ارسال کنید"

                )

                return

            if text == "⏳ متن انتظار":

                state[uid] = {

                    "step": "edit_wait"

                }

                update.message.reply_text(

                    "✍️ متن جدید را ارسال کنید"

                )

                return

            if text == "📚 آموزش":

                state[uid] = {

                    "step": "edit_guide"

                }

                update.message.reply_text(

                    "✍️ متن جدید را ارسال کنید"

                )

                return

            if text == "👤 پشتیبانی":

                state[uid] = {

                    "step": "edit_support"

                }

                update.message.reply_text(

                    "✍️ متن جدید را ارسال کنید"

                )

                return

            # =================================
            # SAVE TEXTS
            # =================================

            if step == "edit_welcome":

                db["texts"]["welcome"] = text

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ ذخیره شد"

                )

                return

            if step == "edit_config":

                db["texts"]["config_send"] = text

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ ذخیره شد"

                )

                return 
# =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 6
# ادامه مستقیم فایل main.py
# =========================================

            if step == "edit_wait":

                db["texts"]["wait_manual"] = text

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ ذخیره شد"

                )

                return

            if step == "edit_guide":

                db["texts"]["guide"] = text

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ ذخیره شد"

                )

                return

            if step == "edit_support":

                db["texts"]["support"] = text

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ ذخیره شد"

                )

                return

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

# =========================================
# CALLBACK HANDLER
# =========================================

def callback_handler(

    update,

    context

):

    try:

        query = update.callback_query

        query.answer()

        uid = str(
            query.from_user.id
        )

        data = query.data

        ensure_user(uid)

        # =====================================
        # CATEGORY
        # =====================================

        if data.startswith("cat_"):

            cat_id = int(

                data.split("_")[1]

            )

            show_plans(

                query,

                cat_id

            )

            return

        # =====================================
        # PLAN
        # =====================================

        if data.startswith("plan_"):

            plan_id = int(

                data.split("_")[1]

            )

            selected = None

            for plan in db["plans"]:

                if plan["id"] == plan_id:

                    selected = plan

                    break

            if not selected:

                query.message.reply_text(

                    "❌ پلن یافت نشد"

                )

                return

            state[uid] = {

                "step": "buy_name",

                "plan": selected

            }

            query.message.reply_text(

                "👤 اسم اکانت را ارسال کنید"

            )

            return

        # =====================================
        # WALLET PRICE
        # =====================================

        if data.startswith("wallet_"):

            amount = int(

                data.split("_")[1]

            )

            state[uid] = {

                "step": "wallet_receipt",

                "amount": amount

            }

            card = db["card"]

            txt = (

                "💳 کارت به کارت\n\n"

                f"💰 مبلغ: {amount:,}\n\n"

                f"💳 شماره کارت:\n"

                f"{card['number']}\n\n"

                f"👤 به نام:\n"

                f"{card['name']}\n\n"

                "📸 سپس عکس فیش را ارسال کنید"

            )

            query.message.reply_text(txt)

            return

        # =====================================
        # DELETE CATEGORY
        # =====================================

        if data.startswith("delete_cat_"):

            cat_id = int(

                data.split("_")[2]

            )

            db["categories"] = [

                c for c in db["categories"]

                if c["id"] != cat_id

            ]

            save_db()

            query.message.reply_text(

                "✅ حذف شد"

            )

            return

        # =====================================
        # DELETE PLAN
        # =====================================

        if data.startswith("delete_plan_"):

            plan_id = int(

                data.split("_")[2]

            )

            db["plans"] = [

                p for p in db["plans"]

                if p["id"] != plan_id

            ]

            save_db()

            query.message.reply_text(

                "✅ حذف شد"

            )

            return

        # =====================================
        # CONFIG PLAN
        # =====================================

        if data.startswith("config_plan_"):

            plan_id = int(

                data.split("_")[2]

            )

            state[uid] = {

                "step": "config_count",

                "plan_id": plan_id

            }

            query.message.reply_text(

                "🔢 چند کانفیگ می‌خواهید اضافه کنید؟"

            )

            return

        # =====================================
        # RENEW
        # =====================================

        if data.startswith("renew_"):

            index = int(

                data.split("_")[1]

            )

            services = db["users"][uid]["services"]

            if index >= len(services):

                query.message.reply_text(

                    "❌ خطا"

                )

                return

            srv = services[index]

            state[uid] = {

                "step": "renew_payment",

                "service": srv

            }

            keyboard = [

                [

                    InlineKeyboardButton(

                        "👛 کیف پول",

                        callback_data="renew_wallet"

                    )

                ],

                [

                    InlineKeyboardButton(

                        "💳 کارت",

                        callback_data="renew_card"

                    )

                ]

            ]

            query.message.reply_text(

                f"♻️ تمدید {srv['name']}\n\n"

                f"💰 مبلغ: {srv['price']:,}",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

# =========================================
# PHOTO HANDLER
# =========================================

def photo_handler(

    update,

    context

):

    try:

        uid = str(
            update.effective_user.id
        )

        ensure_user(uid)

        if uid not in state:

            return

        step = state[uid].get("step")

        # =====================================
        # WALLET RECEIPT
        # =====================================

        if step == "wallet_receipt":

            amount = state[uid]["amount"]

            photo = update.message.photo[-1].file_id

            caption = (

                "💰 درخواست شارژ کیف پول\n\n"

                f"👤 کاربر: {uid}\n"

                f"💵 مبلغ: {amount:,}"

            )

            keyboard = InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(

                        "✅ تایید",

                        callback_data=f"wallet_ok_{uid}_{amount}"

                    ),

                    InlineKeyboardButton(

                        "❌ رد",

                        callback_data=f"wallet_no_{uid}"

                    )

                ]

            ])

            for admin in ADMINS:

                context.bot.send_photo(

                    admin,

                    photo,

                    caption=caption,

                    reply_markup=keyboard

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
        # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 7
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# FINAL STEPS
# =========================================

def final_steps(

    update,

    context

):

    try:

        uid = str(
            update.effective_user.id
        )

        if uid not in state:

            return

        step = state[uid].get("step")

        text = update.message.text

        ensure_user(uid)

        # =====================================
        # BUY NAME
        # =====================================

        if step == "buy_name":

            plan = state[uid]["plan"]

            state[uid] = {

                "step": "buy_payment",

                "plan": plan,

                "account_name": text

            }

            keyboard = [

                [

                    InlineKeyboardButton(

                        "👛 کیف پول",

                        callback_data="buy_wallet"

                    )

                ],

                [

                    InlineKeyboardButton(

                        "💳 کارت به کارت",

                        callback_data="buy_card"

                    )

                ],

                [

                    InlineKeyboardButton(

                        "💰 ترکیبی",

                        callback_data="buy_mix"

                    )

                ]

            ]

            update.message.reply_text(

                f"📦 {plan['name']}\n\n"

                f"💰 مبلغ: {plan['price']:,}\n\n"

                "💳 روش پرداخت را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # CONFIG COUNT
        # =====================================

        if step == "config_count":

            try:

                count = int(text)

                if count < 1:

                    update.message.reply_text(

                        "❌ نامعتبر"

                    )

                    return

                state[uid] = {

                    "step": "config_bulk",

                    "plan_id": state[uid]["plan_id"],

                    "count": count

                }

                update.message.reply_text(

                    "🔗 کانفیگ‌ها را ارسال کنید\n\n"

                    "هر کانفیگ با دو اینتر جدا شود"

                )

                return

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

                return

        # =====================================
        # CONFIG BULK
        # =====================================

        if step == "config_bulk":

            plan_id = state[uid]["plan_id"]

            count = state[uid]["count"]

            configs = text.split("\n\n")

            clean = []

            for c in configs:

                c = c.strip()

                if c:

                    clean.append(c)

            if len(clean) != count:

                update.message.reply_text(

                    f"❌ باید {count} کانفیگ ارسال کنید"

                )

                return

            if str(plan_id) not in db["configs"]:

                db["configs"][str(plan_id)] = []

            added = 0

            for conf in clean:

                if conf not in db["configs"][str(plan_id)]:

                    db["configs"][str(plan_id)].append(conf)

                    added += 1

            save_db()

            state[uid] = {}

            update.message.reply_text(

                f"✅ {added} کانفیگ اضافه شد",

                reply_markup=admin_menu()

            )

            return

        # =====================================
        # RESTORE BACKUP
        # =====================================

        if step == "restore_backup":

            update.message.reply_text(

                "📤 فایل json را ارسال کنید"

            )

            return

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

# =========================================
# DOCUMENT HANDLER
# =========================================

def document_handler(

    update,

    context

):

    try:

        uid = str(
            update.effective_user.id
        )

        if uid not in state:

            return

        step = state[uid].get("step")

        # =====================================
        # RESTORE BACKUP
        # =====================================

        if step == "restore_backup":

            file = update.message.document

            path = "restore.json"

            tg_file = context.bot.get_file(

                file.file_id

            )

            tg_file.download(path)

            with open(

                path,

                "r",

                encoding="utf-8"

            ) as f:

                data = json.load(f)

            global db

            db = data

            save_db()

            state[uid] = {}

            update.message.reply_text(

                "✅ بکاپ بازگردانی شد",

                reply_markup=admin_menu()

            )

            return

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

# =========================================
# MAIN
# =========================================

def main():

    try:

        logger.info(
            "BOT STARTED"
        )

        Thread(
            target=run_web
        ).start()

        updater = Updater(

            TOKEN,

            use_context=True

        )

        dp = updater.dispatcher

        # =====================================
        # HANDLERS
        # =====================================

        dp.add_handler(

            CommandHandler(

                "start",

                start

            )

        )

        dp.add_handler(

            CallbackQueryHandler(

                callback_handler

            )

        )

        dp.add_handler(

            MessageHandler(

                Filters.photo,

                photo_handler

            )

        )

        dp.add_handler(

            MessageHandler(

                Filters.document,

                document_handler

            )

        )

        dp.add_handler(

            MessageHandler(

                Filters.text & ~Filters.command,

                text_handler

            )

        )

        dp.add_handler(

            MessageHandler(

                Filters.text & ~Filters.command,

                final_steps

            )

        )

        # =====================================
        # START BOT
        # =====================================

        updater.start_polling()

        updater.idle()

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

# =========================================
# RUN
# =========================================

if __name__ == "__main__":

    main()
    # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 8
# سیستم خرید واقعی + تایید فیش
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# GET PLAN
# =========================================

def get_plan(plan_id):

    for plan in db["plans"]:

        if plan["id"] == plan_id:

            return plan

    return None

# =========================================
# SEND CONFIG TO USER
# =========================================

def send_config_to_user(

    context,
    user_id,
    plan,
    account_name

):

    try:

        # =================================
        # AUTO CONFIG FROM XUI
        # =================================

        if not db["manual_send"]:

            xui_login()

            result = create_xui_client(

                plan["volume"],
                plan["days"],
                plan["users"]

            )

            if result:

                config = (

                    f"vless://"

                    f"{result['password']}"

                    f"@server.com:443"

                )

            else:

                config = None

        else:

            config = None

        # =================================
        # MANUAL CONFIG STORAGE
        # =================================

        if config is None:

            plan_configs = db["configs"].get(

                str(plan["id"]),

                []

            )

            if len(plan_configs) == 0:

                context.bot.send_message(

                    MAIN_ADMIN,

                    f"⚠️ کانفیگ پلن {plan['name']} تمام شد"

                )

                context.bot.send_message(

                    int(user_id),

                    "⏳ منتظر ارسال ادمین باشید"

                )

                return False

            config = plan_configs.pop(0)

            db["configs"][

                str(plan["id"])

            ] = plan_configs

            save_db()

        # =================================
        # SAVE SERVICE
        # =================================

        service = {

            "name": account_name,

            "volume": plan["volume"],

            "days": plan["days"],

            "price": plan["price"],

            "config": config,

            "created": str(datetime.now())

        }

        db["users"][

            str(user_id)

        ]["services"].append(service)

        db["users"][

            str(user_id)

        ]["total_buy"] += plan["price"]

        save_db()

        # =================================
        # SEND TEXT
        # =================================

        txt = db["texts"]["config_send"]

        txt = txt.replace(

            "{name}",

            account_name

        )

        txt = txt.replace(

            "{volume}",

            str(plan["volume"])

        )

        txt = txt.replace(

            "{days}",

            str(plan["days"])

        )

        txt = txt.replace(

            "{config}",

            config

        )

        context.bot.send_message(

            int(user_id),

            txt

        )

        return True

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

        return False

# =========================================
# CALLBACK UPDATE
# این بخش را داخل callback_handler
# قبل از except اضافه کن
# =========================================

        # =====================================
        # BUY WALLET
        # =====================================

        if data == "buy_wallet":

            if uid not in state:

                return

            plan = state[uid]["plan"]

            account_name = state[uid]["account_name"]

            wallet = db["users"][uid]["wallet"]

            if wallet < plan["price"]:

                query.message.reply_text(

                    "❌ موجودی کافی نیست"

                )

                return

            db["users"][uid]["wallet"] -= plan["price"]

            save_db()

            ok = send_config_to_user(

                context,
                uid,
                plan,
                account_name

            )

            if ok:

                query.message.reply_text(

                    "✅ خرید انجام شد"

                )

            else:

                query.message.reply_text(

                    "❌ خطا در ارسال"

                )

            state[uid] = {}

            return

        # =====================================
        # BUY CARD
        # =====================================

        if data == "buy_card":

            if uid not in state:

                return

            plan = state[uid]["plan"]

            account_name = state[uid]["account_name"]

            state[uid]["step"] = "buy_receipt"

            card = db["card"]

            txt = (

                "💳 کارت به کارت\n\n"

                f"💰 مبلغ: {plan['price']:,}\n\n"

                f"💳 شماره کارت:\n"

                f"{card['number']}\n\n"

                f"👤 به نام:\n"

                f"{card['name']}\n\n"

                "📸 فیش را ارسال کنید"

            )

            query.message.reply_text(txt)

            return

        # =====================================
        # BUY MIX
        # =====================================

        if data == "buy_mix":

            if uid not in state:

                return

            plan = state[uid]["plan"]

            account_name = state[uid]["account_name"]

            wallet = db["users"][uid]["wallet"]

            remain = plan["price"] - wallet

            if remain <= 0:

                remain = 0

            db["users"][uid]["wallet"] = 0

            save_db()

            state[uid] = {

                "step": "mix_receipt",

                "plan": plan,

                "account_name": account_name,

                "remain": remain

            }

            card = db["card"]

            txt = (

                "💰 خرید ترکیبی\n\n"

                f"👛 موجودی کیف پول: {wallet:,}\n"

                f"💳 مبلغ باقی مانده: {remain:,}\n\n"

                f"{card['number']}\n\n"

                "📸 فیش را ارسال کنید"

            )

            query.message.reply_text(txt)

            return

        # =====================================
        # WALLET OK
        # =====================================

        if data.startswith("wallet_ok_"):

            parts = data.split("_")

            target = parts[2]

            amount = int(parts[3])

            ensure_user(target)

            db["users"][target]["wallet"] += amount

            save_db()

            context.bot.send_message(

                int(target),

                f"✅ کیف پول شما {amount:,} تومان شارژ شد"

            )

            query.message.reply_text(

                "✅ تایید شد"

            )

            return

        # =====================================
        # WALLET NO
        # =====================================

        if data.startswith("wallet_no_"):

            target = data.split("_")[2]

            context.bot.send_message(

                int(target),

                "❌ فیش شما رد شد"

            )

            query.message.reply_text(

                "❌ رد شد"

            )

            return
            # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 9
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# این بخش را داخل photo_handler
# قبل از except اضافه کن
# =========================================

        # =====================================
        # BUY RECEIPT
        # =====================================

        if step == "buy_receipt":

            plan = state[uid]["plan"]

            account_name = state[uid]["account_name"]

            photo = update.message.photo[-1].file_id

            caption = (

                "🛒 خرید جدید\n\n"

                f"👤 کاربر: {uid}\n"

                f"📦 پلن: {plan['name']}\n"

                f"💰 مبلغ: {plan['price']:,}\n"

                f"👤 نام اکانت: {account_name}"

            )

            keyboard = InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(

                        "✅ تایید خرید",

                        callback_data=

                        f"buy_ok_{uid}_{plan['id']}"

                    ),

                    InlineKeyboardButton(

                        "❌ رد خرید",

                        callback_data=

                        f"buy_no_{uid}"

                    )

                ]

            ])

            for admin in ADMINS:

                context.bot.send_photo(

                    admin,

                    photo,

                    caption=caption,

                    reply_markup=keyboard

                )

            update.message.reply_text(

                db["texts"]["wait_admin"]

            )

            return

        # =====================================
        # MIX RECEIPT
        # =====================================

        if step == "mix_receipt":

            plan = state[uid]["plan"]

            remain = state[uid]["remain"]

            account_name = state[uid]["account_name"]

            photo = update.message.photo[-1].file_id

            caption = (

                "💰 خرید ترکیبی\n\n"

                f"👤 کاربر: {uid}\n"

                f"📦 پلن: {plan['name']}\n"

                f"💵 باقی مانده: {remain:,}\n"

                f"👤 نام: {account_name}"

            )

            keyboard = InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(

                        "✅ تایید",

                        callback_data=

                        f"mix_ok_{uid}_{plan['id']}"

                    ),

                    InlineKeyboardButton(

                        "❌ رد",

                        callback_data=

                        f"mix_no_{uid}"

                    )

                ]

            ])

            for admin in ADMINS:

                context.bot.send_photo(

                    admin,

                    photo,

                    caption=caption,

                    reply_markup=keyboard

                )

            update.message.reply_text(

                db["texts"]["wait_admin"]

            )

            return

# =========================================
# این بخش را داخل callback_handler
# قبل از except اضافه کن
# =========================================

        # =====================================
        # BUY OK
        # =====================================

        if data.startswith("buy_ok_"):

            parts = data.split("_")

            target = parts[2]

            plan_id = int(parts[3])

            ensure_user(target)

            plan = get_plan(plan_id)

            if not plan:

                query.message.reply_text(

                    "❌ پلن یافت نشد"

                )

                return

            account_name = "VPN USER"

            ok = send_config_to_user(

                context,
                target,
                plan,
                account_name

            )

            if ok:

                context.bot.send_message(

                    int(target),

                    "✅ پرداخت تایید شد"

                )

                query.message.reply_text(

                    "✅ انجام شد"

                )

            else:

                query.message.reply_text(

                    "❌ خطا در ارسال"

                )

            return

        # =====================================
        # BUY NO
        # =====================================

        if data.startswith("buy_no_"):

            target = data.split("_")[2]

            context.bot.send_message(

                int(target),

                "❌ خرید شما رد شد"

            )

            query.message.reply_text(

                "❌ رد شد"

            )

            return

        # =====================================
        # MIX OK
        # =====================================

        if data.startswith("mix_ok_"):

            parts = data.split("_")

            target = parts[2]

            plan_id = int(parts[3])

            ensure_user(target)

            plan = get_plan(plan_id)

            if not plan:

                return

            ok = send_config_to_user(

                context,
                target,
                plan,
                "VPN USER"

            )

            if ok:

                context.bot.send_message(

                    int(target),

                    "✅ خرید تایید شد"

                )

                query.message.reply_text(

                    "✅ انجام شد"

                )

            else:

                query.message.reply_text(

                    "❌ خطا"

                )

            return

        # =====================================
        # MIX NO
        # =====================================

        if data.startswith("mix_no_"):

            target = data.split("_")[2]

            context.bot.send_message(

                int(target),

                "❌ خرید رد شد"

            )

            query.message.reply_text(

                "❌ رد شد"

            )

            return

        # =====================================
        # RENEW WALLET
        # =====================================

        if data == "renew_wallet":

            if uid not in state:

                return

            srv = state[uid]["service"]

            wallet = db["users"][uid]["wallet"]

            if wallet < srv["price"]:

                query.message.reply_text(

                    "❌ موجودی کافی نیست"

                )

                return

            db["users"][uid]["wallet"] -= srv["price"]

            save_db()

            query.message.reply_text(

                "✅ تمدید انجام شد"

            )

            return

        # =====================================
        # RENEW CARD
        # =====================================

        if data == "renew_card":

            card = db["card"]

            txt = (

                "💳 تمدید سرویس\n\n"

                f"{card['number']}\n\n"

                "📸 فیش را ارسال کنید"

            )

            query.message.reply_text(txt)

            return
            # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 10
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# این بخش را داخل text_handler
# قبل از except اضافه کن
# =========================================

        # =====================================
        # ADD WALLET PRICE
        # =====================================

        if text == "➕ افزودن مبلغ":

            state[uid] = {

                "step": "add_wallet_price"

            }

            update.message.reply_text(

                "💰 مبلغ را ارسال کنید"

            )

            return

        # =====================================
        # DELETE WALLET PRICE
        # =====================================

        if text == "🗑 حذف مبلغ":

            keyboard = []

            for amount in db["wallet_prices"]:

                keyboard.append([

                    InlineKeyboardButton(

                        f"{amount:,}",

                        callback_data=

                        f"delete_wallet_{amount}"

                    )

                ])

            update.message.reply_text(

                "🗑 مبلغ را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # WALLET LIST
        # =====================================

        if text == "📋 لیست مبالغ":

            msg = "💰 مبالغ کیف پول\n\n"

            for amount in db["wallet_prices"]:

                msg += f"{amount:,}\n"

            update.message.reply_text(msg)

            return

        # =====================================
        # STATES
        # =====================================

        if uid in state:

            step = state[uid].get("step")

            # =================================
            # ADD WALLET PRICE
            # =================================

            if step == "add_wallet_price":

                try:

                    amount = int(text)

                    if amount not in db["wallet_prices"]:

                        db["wallet_prices"].append(

                            amount

                        )

                    save_db()

                    state[uid] = {}

                    update.message.reply_text(

                        "✅ اضافه شد"

                    )

                    return

                except:

                    update.message.reply_text(

                        "❌ فقط عدد"

                    )

                    return

# =========================================
# این بخش را داخل callback_handler
# قبل از except اضافه کن
# =========================================

        # =====================================
        # DELETE WALLET
        # =====================================

        if data.startswith("delete_wallet_"):

            amount = int(

                data.split("_")[2]

            )

            if amount in db["wallet_prices"]:

                db["wallet_prices"].remove(

                    amount

                )

            save_db()

            query.message.reply_text(

                "✅ حذف شد"

            )

            return

# =========================================
# SEND MEDIA BROADCAST
# این تابع را بالای main()
# اضافه کن
# =========================================

def send_broadcast_media(

    context,
    user_id,
    message

):

    try:

        if message.photo:

            context.bot.send_photo(

                user_id,

                message.photo[-1].file_id,

                caption=message.caption or ""

            )

            return True

        if message.video:

            context.bot.send_video(

                user_id,

                message.video.file_id,

                caption=message.caption or ""

            )

            return True

        if message.document:

            context.bot.send_document(

                user_id,

                message.document.file_id,

                caption=message.caption or ""

            )

            return True

        if message.text:

            context.bot.send_message(

                user_id,

                message.text

            )

            return True

        return False

    except:

        return False

# =========================================
# MEDIA HANDLER
# این تابع را بالای main()
# اضافه کن
# =========================================

def media_handler(

    update,

    context

):

    try:

        uid = str(
            update.effective_user.id
        )

        if uid not in state:

            return

        step = state[uid].get("step")

        # =====================================
        # BROADCAST MEDIA
        # =====================================

        if step == "broadcast":

            success = 0

            failed = 0

            for user_id in db["users"]:

                ok = send_broadcast_media(

                    context,
                    int(user_id),
                    update.message

                )

                if ok:

                    success += 1

                else:

                    failed += 1

            state[uid] = {}

            update.message.reply_text(

                f"✅ ارسال شد\n\n"

                f"موفق: {success}\n"

                f"ناموفق: {failed}"

            )

            return

        # =====================================
        # PRIVATE MEDIA
        # =====================================

        if step == "private_message":

            target = state[uid]["target"]

            ok = send_broadcast_media(

                context,
                int(target),
                update.message

            )

            state[uid] = {}

            if ok:

                update.message.reply_text(

                    "✅ ارسال شد"

                )

            else:

                update.message.reply_text(

                    "❌ خطا"

                )

            return

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

# =========================================
# این بخش را داخل main()
# قبل از updater.start_polling()
# اضافه کن
# =========================================

        dp.add_handler(

            MessageHandler(

                Filters.photo |
                Filters.video |
                Filters.document,

                media_handler

            )

        )
        # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 11
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# XUI GET INBOUNDS
# این تابع را بالای main()
# اضافه کن
# =========================================

def get_inbounds():

    try:

        url = f"{XUI_URL}/panel/api/inbounds/list"

        r = session.get(

            url,

            timeout=20

        )

        if r.status_code != 200:

            return []

        data = r.json()

        if not data.get("success"):

            return []

        return data.get("obj", [])

    except Exception as e:

        logger.error(e)

        return []

# =========================================
# CREATE REAL CONFIG
# این تابع را جایگزین
# create_xui_client
# قبلی کن
# =========================================

def create_xui_client(

    volume_gb,
    days,
    limit_ip

):

    try:

        xui_login()

        inbounds = get_inbounds()

        if len(inbounds) == 0:

            return None

        inbound = inbounds[0]

        inbound_id = inbound["id"]

        inbound_port = inbound["port"]

        inbound_remark = inbound["remark"]

        settings = json.loads(

            inbound["settings"]

        )

        client_id = ''.join(

            random.choice(

                string.hexdigits.lower()

            )

            for _ in range(32)

        )

        email = random_email()

        sub_id = random_password()

        total_bytes = (

            volume_gb *
            1024 *
            1024 *
            1024

        )

        expiry = int(

            (
                datetime.now().timestamp()
                +
                (
                    days * 86400
                )

            ) * 1000

        )

        client = {

            "id": client_id,

            "email": email,

            "limitIp": limit_ip,

            "totalGB": total_bytes,

            "expiryTime": expiry,

            "enable": True,

            "tgId": "",

            "subId": sub_id

        }

        settings["clients"].append(

            client

        )

        payload = {

            "id": inbound_id,

            "settings": json.dumps(

                settings

            )

        }

        url = (

            f"{XUI_URL}"

            f"/panel/api/inbounds/updateClient/"

            f"{client_id}"

        )

        r = session.post(

            url,

            json=payload,

            timeout=20

        )

        if r.status_code != 200:

            return None

        host = XUI_URL.replace(

            "http://",

            ""

        ).split(":")[0]

        config = (

            f"vless://{client_id}"

            f"@{host}:{inbound_port}"

            f"?type=tcp&security=none"

            f"#{inbound_remark}"

        )

        return {

            "config": config,

            "email": email,

            "client_id": client_id

        }

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

        return None

# =========================================
# این تابع را جایگزین
# send_config_to_user
# قبلی کن
# =========================================

def send_config_to_user(

    context,
    user_id,
    plan,
    account_name

):

    try:

        config = None

        # =================================
        # AUTO CREATE
        # =================================

        if db["auto_send"]:

            result = create_xui_client(

                plan["volume"],
                plan["days"],
                plan["users"]

            )

            if result:

                config = result["config"]

        # =================================
        # MANUAL CONFIG STORAGE
        # =================================

        if config is None:

            plan_configs = db["configs"].get(

                str(plan["id"]),

                []

            )

            if len(plan_configs) == 0:

                context.bot.send_message(

                    MAIN_ADMIN,

                    f"⚠️ کانفیگ پلن {plan['name']} تمام شد"

                )

                context.bot.send_message(

                    int(user_id),

                    db["texts"]["wait_manual"]

                )

                return False

            config = plan_configs.pop(0)

            db["configs"][

                str(plan["id"])

            ] = plan_configs

            save_db()

        # =================================
        # SAVE SERVICE
        # =================================

        service = {

            "name": account_name,

            "volume": plan["volume"],

            "days": plan["days"],

            "price": plan["price"],

            "config": config,

            "created": str(datetime.now())

        }

        db["users"][

            str(user_id)

        ]["services"].append(service)

        db["users"][

            str(user_id)

        ]["total_buy"] += plan["price"]

        save_db()

        # =================================
        # SEND
        # =================================

        txt = db["texts"]["config_send"]

        txt = txt.replace(

            "{name}",

            account_name

        )

        txt = txt.replace(

            "{volume}",

            str(plan["volume"])

        )

        txt = txt.replace(

            "{days}",

            str(plan["days"])

        )

        txt = txt.replace(

            "{config}",

            config

        )

        keyboard = InlineKeyboardMarkup([

            [

                InlineKeyboardButton(

                    "📚 آموزش اتصال",

                    url="https://t.me/test"

                )

            ],

            [

                InlineKeyboardButton(

                    "🆘 پشتیبانی",

                    url="https://t.me/test"

                )

            ]

        ])

        context.bot.send_message(

            int(user_id),

            txt,

            reply_markup=keyboard

        )

        return True

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

        return False
        # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 12
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# EDIT CATEGORY
# این بخش را داخل callback_handler
# قبل از except اضافه کن
# =========================================

        # =====================================
        # EDIT CATEGORY
        # =====================================

        if data.startswith("edit_cat_"):

            cat_id = int(

                data.split("_")[2]

            )

            state[uid] = {

                "step": "edit_category_name",

                "cat_id": cat_id

            }

            query.message.reply_text(

                "✏️ نام جدید دسته را ارسال کنید"

            )

            return

        # =====================================
        # EDIT PLAN
        # =====================================

        if data.startswith("edit_plan_"):

            plan_id = int(

                data.split("_")[2]

            )

            state[uid] = {

                "step": "edit_plan_name",

                "plan_id": plan_id

            }

            query.message.reply_text(

                "✏️ نام جدید پلن را ارسال کنید"

            )

            return

        # =====================================
        # SELECT CATEGORY FOR PLAN
        # =====================================

        if data.startswith("select_cat_"):

            cat_id = int(

                data.split("_")[2]

            )

            state[uid] = {

                "step": "new_plan_name",

                "cat_id": cat_id

            }

            query.message.reply_text(

                "📦 نام پلن را ارسال کنید"

            )

            return

# =========================================
# این بخش را داخل final_steps
# قبل از except اضافه کن
# =========================================

        # =====================================
        # EDIT CATEGORY NAME
        # =====================================

        if step == "edit_category_name":

            cat_id = state[uid]["cat_id"]

            for cat in db["categories"]:

                if cat["id"] == cat_id:

                    cat["name"] = text

                    break

            save_db()

            state[uid] = {}

            update.message.reply_text(

                "✅ دسته ویرایش شد",

                reply_markup=admin_menu()

            )

            return

        # =====================================
        # EDIT PLAN NAME
        # =====================================

        if step == "edit_plan_name":

            state[uid]["name"] = text

            state[uid]["step"] = "edit_plan_volume"

            update.message.reply_text(

                "📊 حجم را ارسال کنید"

            )

            return

        # =====================================
        # EDIT PLAN VOLUME
        # =====================================

        if step == "edit_plan_volume":

            try:

                volume = int(text)

                state[uid]["volume"] = volume

                state[uid]["step"] = "edit_plan_days"

                update.message.reply_text(

                    "📅 تعداد روز را ارسال کنید"

                )

                return

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

                return

        # =====================================
        # EDIT PLAN DAYS
        # =====================================

        if step == "edit_plan_days":

            try:

                days = int(text)

                state[uid]["days"] = days

                state[uid]["step"] = "edit_plan_users"

                update.message.reply_text(

                    "👥 تعداد کاربر را ارسال کنید"

                )

                return

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

                return

        # =====================================
        # EDIT PLAN USERS
        # =====================================

        if step == "edit_plan_users":

            try:

                users = int(text)

                state[uid]["users"] = users

                state[uid]["step"] = "edit_plan_price"

                update.message.reply_text(

                    "💰 قیمت را ارسال کنید"

                )

                return

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

                return

        # =====================================
        # EDIT PLAN PRICE
        # =====================================

        if step == "edit_plan_price":

            try:

                price = int(text)

                plan_id = state[uid]["plan_id"]

                for plan in db["plans"]:

                    if plan["id"] == plan_id:

                        plan["name"] = state[uid]["name"]

                        plan["volume"] = state[uid]["volume"]

                        plan["days"] = state[uid]["days"]

                        plan["users"] = state[uid]["users"]

                        plan["price"] = price

                        break

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ پلن ویرایش شد",

                    reply_markup=admin_menu()

                )

                return

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

                return

        # =====================================
        # NEW PLAN NAME
        # =====================================

        if step == "new_plan_name":

            state[uid]["name"] = text

            state[uid]["step"] = "new_plan_volume"

            update.message.reply_text(

                "📊 حجم را ارسال کنید"

            )

            return

        # =====================================
        # NEW PLAN VOLUME
        # =====================================

        if step == "new_plan_volume":

            try:

                volume = int(text)

                state[uid]["volume"] = volume

                state[uid]["step"] = "new_plan_days"

                update.message.reply_text(

                    "📅 تعداد روز را ارسال کنید"

                )

                return

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

                return

        # =====================================
        # NEW PLAN DAYS
        # =====================================

        if step == "new_plan_days":

            try:

                days = int(text)

                state[uid]["days"] = days

                state[uid]["step"] = "new_plan_users"

                update.message.reply_text(

                    "👥 تعداد کاربر را ارسال کنید"

                )

                return

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

                return
                # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 13
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# این بخش را داخل final_steps
# ادامه مستقیم PART 12
# قبل از except اضافه کن
# =========================================

        # =====================================
        # NEW PLAN USERS
        # =====================================

        if step == "new_plan_users":

            try:

                users = int(text)

                state[uid]["users"] = users

                state[uid]["step"] = "new_plan_price"

                update.message.reply_text(

                    "💰 قیمت را ارسال کنید"

                )

                return

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

                return

        # =====================================
        # NEW PLAN PRICE
        # =====================================

        if step == "new_plan_price":

            try:

                price = int(text)

                new_id = 1

                if db["plans"]:

                    new_id = max(

                        p["id"]
                        for p in db["plans"]

                    ) + 1

                db["plans"].append({

                    "id": new_id,

                    "cat": state[uid]["cat_id"],

                    "name": state[uid]["name"],

                    "volume": state[uid]["volume"],

                    "days": state[uid]["days"],

                    "users": state[uid]["users"],

                    "price": price

                })

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ پلن اضافه شد",

                    reply_markup=admin_menu()

                )

                return

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

                return

# =========================================
# STATS FUNCTION
# این تابع را بالای main()
# اضافه کن
# =========================================

def get_stats():

    try:

        total_users = len(

            db["users"]

        )

        total_services = 0

        total_sales = 0

        total_wallet = 0

        for uid in db["users"]:

            user = db["users"][uid]

            total_services += len(

                user["services"]

            )

            total_sales += user.get(

                "total_buy",

                0

            )

            total_wallet += user.get(

                "wallet",

                0

            )

        return {

            "users": total_users,

            "services": total_services,

            "sales": total_sales,

            "wallet": total_wallet

        }

    except:

        return {

            "users": 0,

            "services": 0,

            "sales": 0,

            "wallet": 0

        }

# =========================================
# این بخش را داخل text_handler
# قبل از except اضافه کن
# =========================================

        # =====================================
        # STATS
        # =====================================

        if text == "📊 آمار":

            stats = get_stats()

            msg = (

                "📊 آمار ربات\n\n"

                f"👥 کاربران: "

                f"{stats['users']}\n\n"

                f"📦 سرویس‌ها: "

                f"{stats['services']}\n\n"

                f"💰 فروش کل: "

                f"{stats['sales']:,}\n\n"

                f"👛 موجودی کیف پول کاربران: "

                f"{stats['wallet']:,}"

            )

            update.message.reply_text(msg)

            return

# =========================================
# ADMIN MENU UPDATE
# این تابع را جایگزین
# admin_menu
# قبلی کن
# =========================================

def admin_menu():

    keyboard = [

        ["📦 مدیریت پلن‌ها"],

        ["📁 مدیریت دسته‌بندی"],

        ["🔗 افزودن کانفیگ"],

        ["💳 روش پرداخت"],

        ["👛 تنظیمات کیف پول"],

        ["🎁 تنظیمات تست"],

        ["📊 آمار"],

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
# SAFE SAVE
# این تابع را جایگزین
# save_db
# قبلی کن
# =========================================

def save_db():

    try:

        temp_file = "temp.json"

        with open(

            temp_file,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                db,

                f,

                ensure_ascii=False,

                indent=4

            )

        if os.path.exists(DB_FILE):

            os.remove(DB_FILE)

        os.rename(

            temp_file,

            DB_FILE

        )

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

# =========================================
# AUTO BACKUP
# این تابع را بالای main()
# اضافه کن
# =========================================

def auto_backup():

    try:

        backup_name = (

            "backup_"

            +

            datetime.now().strftime(

                "%Y_%m_%d_%H_%M"

            )

            +

            ".json"

        )

        with open(

            backup_name,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                db,

                f,

                ensure_ascii=False,

                indent=4

            )

        logger.info(

            "AUTO BACKUP CREATED"

        )

    except Exception as e:

        logger.error(e)
        # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 14
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# SCHEDULER
# این تابع را بالای main()
# اضافه کن
# =========================================

def scheduler_loop():

    while True:

        try:

            now = datetime.now()

            # =================================
            # AUTO BACKUP EVERY 6 HOURS
            # =================================

            if now.hour in [0, 6, 12, 18]:

                auto_backup()

                time.sleep(3600)

            # =================================
            # CHECK EXPIRE SERVICES
            # =================================

            for uid in db["users"]:

                user = db["users"][uid]

                services = user.get(

                    "services",

                    []

                )

                for srv in services:

                    try:

                        created = datetime.strptime(

                            srv["created"].split(".")[0],

                            "%Y-%m-%d %H:%M:%S"

                        )

                        expire = created + timedelta(

                            days=srv["days"]

                        )

                        remain = (

                            expire -

                            datetime.now()

                        ).days

                        # =====================
                        # EXPIRE WARNING
                        # =====================

                        if remain == 1:

                            bot.send_message(

                                int(uid),

                                "⚠️ سرویس شما فردا منقضی می‌شود"

                            )

                    except:

                        pass

            time.sleep(60)

        except Exception as e:

            logger.error(e)

            time.sleep(60)

# =========================================
# BOT SETTINGS MENU
# این تابع را بالای main()
# اضافه کن
# =========================================

def settings_menu():

    auto_status = (

        "🟢 روشن"

        if db["auto_send"]

        else "🔴 خاموش"

    )

    manual_status = (

        "🟢 روشن"

        if db["manual_send"]

        else "🔴 خاموش"

    )

    test_status = (

        "🟢 روشن"

        if db["test_enabled"]

        else "🔴 خاموش"

    )

    keyboard = [

        [

            f"⚡ ارسال خودکار: {auto_status}"

        ],

        [

            f"👨‍💻 ارسال دستی: {manual_status}"

        ],

        [

            f"🎁 تست: {test_status}"

        ],

        [

            "✏️ ویرایش متن‌ها"

        ],

        [

            "🔙 برگشت"

        ]

    ]

    return ReplyKeyboardMarkup(

        keyboard,

        resize_keyboard=True

    )

# =========================================
# PAYMENT MENU
# این تابع را بالای main()
# اضافه کن
# =========================================

def payment_menu():

    keyboard = [

        ["💳 کارت به کارت"],

        ["🌐 درگاه پرداخت"],

        ["🔙 برگشت"]

    ]

    return ReplyKeyboardMarkup(

        keyboard,

        resize_keyboard=True

    )

# =========================================
# WALLET MENU
# این تابع را بالای main()
# اضافه کن
# =========================================

def wallet_menu():

    keyboard = [

        ["➕ افزودن مبلغ"],

        ["🗑 حذف مبلغ"],

        ["📋 لیست مبالغ"],

        ["🔙 برگشت"]

    ]

    return ReplyKeyboardMarkup(

        keyboard,

        resize_keyboard=True

    )

# =========================================
# TEST MENU
# این تابع را بالای main()
# اضافه کن
# =========================================

def test_menu():

    keyboard = [

        ["🟢 فعال"],

        ["🔴 غیرفعال"],

        ["⚙️ تنظیمات تست"],

        ["🔙 برگشت"]

    ]

    return ReplyKeyboardMarkup(

        keyboard,

        resize_keyboard=True

    )

# =========================================
# TEXTS MENU
# این تابع را بالای main()
# اضافه کن
# =========================================

def texts_menu():

    keyboard = [

        ["👋 خوش آمد"],

        ["📦 متن ارسال کانفیگ"],

        ["⏳ متن انتظار"],

        ["📚 آموزش"],

        ["👤 پشتیبانی"],

        ["🔙 برگشت"]

    ]

    return ReplyKeyboardMarkup(

        keyboard,

        resize_keyboard=True

    )

# =========================================
# این بخش را داخل text_handler
# قبل از except اضافه کن
# =========================================

        # =====================================
        # BOT SETTINGS
        # =====================================

        if text == "🤖 تنظیمات ربات":

            update.message.reply_text(

                "⚙️ تنظیمات",

                reply_markup=settings_menu()

            )

            return

        # =====================================
        # PAYMENT SETTINGS
        # =====================================

        if text == "💳 روش پرداخت":

            update.message.reply_text(

                "💳 تنظیمات پرداخت",

                reply_markup=payment_menu()

            )

            return

        # =====================================
        # WALLET SETTINGS
        # =====================================

        if text == "👛 تنظیمات کیف پول":

            update.message.reply_text(

                "👛 تنظیمات کیف پول",

                reply_markup=wallet_menu()

            )

            return

        # =====================================
        # TEST SETTINGS
        # =====================================

        if text == "🎁 تنظیمات تست":

            update.message.reply_text(

                "🎁 تنظیمات تست",

                reply_markup=test_menu()

            )

            return

        # =====================================
        # TEXTS SETTINGS
        # =====================================

        if text == "✏️ ویرایش متن‌ها":

            update.message.reply_text(

                "✏️ ویرایش متن‌ها",

                reply_markup=texts_menu()

            )

            return
            # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 15
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# این بخش را داخل text_handler
# ادامه PART 14
# قبل از except اضافه کن
# =========================================

        # =====================================
        # AUTO SEND TOGGLE
        # =====================================

        if "⚡ ارسال خودکار" in text:

            db["auto_send"] = not db["auto_send"]

            save_db()

            status = (

                "🟢 روشن"

                if db["auto_send"]

                else "🔴 خاموش"

            )

            update.message.reply_text(

                f"✅ ارسال خودکار: {status}",

                reply_markup=settings_menu()

            )

            return

        # =====================================
        # MANUAL SEND TOGGLE
        # =====================================

        if "👨‍💻 ارسال دستی" in text:

            db["manual_send"] = not db["manual_send"]

            save_db()

            status = (

                "🟢 روشن"

                if db["manual_send"]

                else "🔴 خاموش"

            )

            update.message.reply_text(

                f"✅ ارسال دستی: {status}",

                reply_markup=settings_menu()

            )

            return

        # =====================================
        # TEST ENABLE
        # =====================================

        if text == "🟢 فعال":

            db["test_enabled"] = True

            save_db()

            update.message.reply_text(

                "✅ تست فعال شد",

                reply_markup=test_menu()

            )

            return

        # =====================================
        # TEST DISABLE
        # =====================================

        if text == "🔴 غیرفعال":

            db["test_enabled"] = False

            save_db()

            update.message.reply_text(

                "❌ تست غیرفعال شد",

                reply_markup=test_menu()

            )

            return

        # =====================================
        # TEST SETTINGS
        # =====================================

        if text == "⚙️ تنظیمات تست":

            state[uid] = {

                "step": "test_volume"

            }

            update.message.reply_text(

                "📊 حجم تست را ارسال کنید\n"

                "1 تا 100"

            )

            return

        # =====================================
        # PAYMENT CARD
        # =====================================

        if text == "💳 کارت به کارت":

            state[uid] = {

                "step": "edit_card"

            }

            update.message.reply_text(

                "💳 شماره کارت را ارسال کنید"

            )

            return

        # =====================================
        # PAYMENT GATEWAY
        # =====================================

        if text == "🌐 درگاه پرداخت":

            state[uid] = {

                "step": "gateway_link"

            }

            update.message.reply_text(

                "🌐 لینک درگاه را ارسال کنید"

            )

            return

        # =====================================
        # STATES
        # =====================================

        if uid in state:

            step = state[uid].get("step")

            # =================================
            # EDIT CARD
            # =================================

            if step == "edit_card":

                db["card"]["number"] = text

                state[uid] = {

                    "step": "edit_card_name"

                }

                update.message.reply_text(

                    "👤 نام صاحب کارت را ارسال کنید"

                )

                return

            # =================================
            # EDIT CARD NAME
            # =================================

            if step == "edit_card_name":

                db["card"]["name"] = text

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ ذخیره شد",

                    reply_markup=payment_menu()

                )

                return

            # =================================
            # GATEWAY LINK
            # =================================

            if step == "gateway_link":

                db["gateway"] = text

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ درگاه ذخیره شد",

                    reply_markup=payment_menu()

                )

                return

# =========================================
# TEST SERVICE
# این بخش را داخل callback_handler
# قبل از except اضافه کن
# =========================================

        # =====================================
        # GET TEST
        # =====================================

        if data == "get_test":

            if not db["test_enabled"]:

                query.message.reply_text(

                    "❌ تست غیرفعال است"

                )

                return

            services = db["users"][uid]["services"]

            for srv in services:

                if srv.get("is_test"):

                    query.message.reply_text(

                        "❌ قبلا تست دریافت کرده‌اید"

                    )

                    return

            volume = db["test_settings"]["volume"]

            days = db["test_settings"]["days"]

            result = create_xui_client(

                volume,
                days,
                1

            )

            if not result:

                query.message.reply_text(

                    "❌ خطا در ساخت تست"

                )

                return

            config = result["config"]

            service = {

                "name": "TEST",

                "volume": volume,

                "days": days,

                "price": 0,

                "config": config,

                "created": str(datetime.now()),

                "is_test": True

            }

            db["users"][uid][

                "services"

            ].append(service)

            save_db()

            txt = (

                "🎁 تست شما آماده شد\n\n"

                f"📊 حجم: {volume}GB\n"

                f"📅 مدت: {days} روز\n\n"

                f"{config}"

            )

            query.message.reply_text(txt)

            return
            # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 16
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# CATEGORY MANAGEMENT MENU
# این تابع را بالای main()
# اضافه کن
# =========================================

def category_manage_menu():

    keyboard = [

        ["➕ افزودن دسته"],

        ["✏️ ویرایش دسته"],

        ["🗑 حذف دسته"],

        ["📋 لیست دسته‌ها"],

        ["🔙 برگشت"]

    ]

    return ReplyKeyboardMarkup(

        keyboard,

        resize_keyboard=True

    )

# =========================================
# PLAN MANAGEMENT MENU
# این تابع را بالای main()
# اضافه کن
# =========================================

def plan_manage_menu():

    keyboard = [

        ["➕ افزودن پلن"],

        ["✏️ ویرایش پلن"],

        ["🗑 حذف پلن"],

        ["📋 لیست پلن‌ها"],

        ["🔙 برگشت"]

    ]

    return ReplyKeyboardMarkup(

        keyboard,

        resize_keyboard=True

    )

# =========================================
# THIS PART INSIDE text_handler
# قبل از except اضافه کن
# =========================================

        # =====================================
        # CATEGORY MANAGEMENT
        # =====================================

        if text == "📁 مدیریت دسته‌بندی":

            update.message.reply_text(

                "📁 مدیریت دسته‌ها",

                reply_markup=category_manage_menu()

            )

            return

        # =====================================
        # PLAN MANAGEMENT
        # =====================================

        if text == "📦 مدیریت پلن‌ها":

            update.message.reply_text(

                "📦 مدیریت پلن‌ها",

                reply_markup=plan_manage_menu()

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

                "📁 نام دسته را ارسال کنید"

            )

            return

        # =====================================
        # LIST CATEGORIES
        # =====================================

        if text == "📋 لیست دسته‌ها":

            if len(db["categories"]) == 0:

                update.message.reply_text(

                    "❌ دسته‌ای وجود ندارد"

                )

                return

            msg = "📁 لیست دسته‌ها\n\n"

            for cat in db["categories"]:

                msg += (

                    f"🆔 {cat['id']}\n"

                    f"📂 {cat['name']}\n\n"

                )

            update.message.reply_text(msg)

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

                        callback_data=

                        f"edit_cat_{cat['id']}"

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
        # DELETE CATEGORY
        # =====================================

        if text == "🗑 حذف دسته":

            keyboard = []

            for cat in db["categories"]:

                keyboard.append([

                    InlineKeyboardButton(

                        cat["name"],

                        callback_data=

                        f"delete_cat_{cat['id']}"

                    )

                ])

            update.message.reply_text(

                "🗑 دسته را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

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

                        callback_data=

                        f"select_cat_{cat['id']}"

                    )

                ])

            update.message.reply_text(

                "📁 دسته را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # LIST PLANS
        # =====================================

        if text == "📋 لیست پلن‌ها":

            if len(db["plans"]) == 0:

                update.message.reply_text(

                    "❌ پلنی وجود ندارد"

                )

                return

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
            # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 17
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# THIS PART INSIDE text_handler
# ادامه PART 16
# قبل از except اضافه کن
# =========================================

        # =====================================
        # EDIT PLAN
        # =====================================

        if text == "✏️ ویرایش پلن":

            if len(db["plans"]) == 0:

                update.message.reply_text(

                    "❌ پلنی وجود ندارد"

                )

                return

            keyboard = []

            for plan in db["plans"]:

                keyboard.append([

                    InlineKeyboardButton(

                        plan["name"],

                        callback_data=

                        f"edit_plan_{plan['id']}"

                    )

                ])

            update.message.reply_text(

                "✏️ پلن را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # DELETE PLAN
        # =====================================

        if text == "🗑 حذف پلن":

            if len(db["plans"]) == 0:

                update.message.reply_text(

                    "❌ پلنی وجود ندارد"

                )

                return

            keyboard = []

            for plan in db["plans"]:

                keyboard.append([

                    InlineKeyboardButton(

                        plan["name"],

                        callback_data=

                        f"delete_plan_{plan['id']}"

                    )

                ])

            update.message.reply_text(

                "🗑 پلن را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # ADD CONFIG
        # =====================================

        if text == "🔗 افزودن کانفیگ":

            if len(db["plans"]) == 0:

                update.message.reply_text(

                    "❌ ابتدا پلن بسازید"

                )

                return

            keyboard = []

            for plan in db["plans"]:

                keyboard.append([

                    InlineKeyboardButton(

                        plan["name"],

                        callback_data=

                        f"config_plan_{plan['id']}"

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
        # BROADCAST
        # =====================================

        if text == "📨 ارسال همگانی":

            state[uid] = {

                "step": "broadcast"

            }

            update.message.reply_text(

                "📨 پیام را ارسال کنید\n\n"

                "متن / عکس / ویدیو / فایل"

            )

            return

        # =====================================
        # PRIVATE MESSAGE
        # =====================================

        if text == "👤 ارسال پیام":

            state[uid] = {

                "step": "private_user"

            }

            update.message.reply_text(

                "🆔 آیدی عددی کاربر را ارسال کنید"

            )

            return

        # =====================================
        # PIN BROADCAST
        # =====================================

        if text == "📌 پین همگانی":

            state[uid] = {

                "step": "pin_message"

            }

            update.message.reply_text(

                "📌 متن پیام را ارسال کنید"

            )

            return

        # =====================================
        # BACKUP
        # =====================================

        if text == "💾 بکاپ":

            with open(

                DB_FILE,

                "rb"

            ) as f:

                update.message.reply_document(

                    f,

                    filename="backup.json",

                    caption="💾 بکاپ ربات"

                )

            return

        # =====================================
        # BACK
        # =====================================

        if text == "🔙 برگشت":

            state[uid] = {}

            if is_admin(uid):

                update.message.reply_text(

                    "🏠 پنل مدیریت",

                    reply_markup=admin_menu()

                )

            else:

                update.message.reply_text(

                    "🏠 منوی اصلی",

                    reply_markup=main_menu()

                )

            return

# =========================================
# USER SERVICES MENU
# این تابع را بالای main()
# اضافه کن
# =========================================

def user_services_menu(

    uid

):

    keyboard = []

    services = db["users"][uid]["services"]

    for i, srv in enumerate(services):

        keyboard.append([

            InlineKeyboardButton(

                f"{srv['name']} | تمدید",

                callback_data=f"renew_{i}"

            )

        ])

    return InlineKeyboardMarkup(

        keyboard

    )

# =========================================
# THIS PART INSIDE text_handler
# قبل از except اضافه کن
# =========================================

        # =====================================
        # MY SERVICES
        # =====================================

        if text == "📦 سرویس‌های من":

            services = db["users"][uid]["services"]

            if len(services) == 0:

                update.message.reply_text(

                    "❌ سرویسی ندارید"

                )

                return

            msg = "📦 سرویس‌های شما\n\n"

            for srv in services:

                msg += (

                    f"👤 {srv['name']}\n"

                    f"📊 {srv['volume']}GB\n"

                    f"📅 {srv['days']} روز\n\n"

                )

            update.message.reply_text(

                msg,

                reply_markup=

                user_services_menu(uid)

            )

            return

        # =====================================
        # SUPPORT
        # =====================================

        if text == "🆘 پشتیبانی":

            update.message.reply_text(

                db["texts"]["support"]

            )

            return

        # =====================================
        # GUIDE
        # =====================================

        if text == "📚 آموزش":

            update.message.reply_text(

                db["texts"]["guide"]

            )

            return
            # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 18
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# MAIN MENU
# این تابع را جایگزین
# main_menu
# قبلی کن
# =========================================

def main_menu():

    keyboard = [

        ["🛒 خرید سرویس"],

        ["📦 سرویس‌های من"],

        ["👛 کیف پول"],

        ["🎁 تست"],

        ["📚 آموزش", "🆘 پشتیبانی"]

    ]

    return ReplyKeyboardMarkup(

        keyboard,

        resize_keyboard=True

    )

# =========================================
# THIS PART INSIDE text_handler
# قبل از except اضافه کن
# =========================================

        # =====================================
        # BUY SERVICE
        # =====================================

        if text == "🛒 خرید سرویس":

            if len(db["categories"]) == 0:

                update.message.reply_text(

                    "❌ دسته‌ای وجود ندارد"

                )

                return

            keyboard = []

            for cat in db["categories"]:

                keyboard.append([

                    InlineKeyboardButton(

                        cat["name"],

                        callback_data=

                        f"cat_{cat['id']}"

                    )

                ])

            update.message.reply_text(

                "📁 دسته‌بندی را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # WALLET
        # =====================================

        if text == "👛 کیف پول":

            wallet = db["users"][uid]["wallet"]

            msg = (

                "👛 کیف پول\n\n"

                f"💰 موجودی شما:\n"

                f"{wallet:,} تومان\n\n"

                "➕ برای شارژ انتخاب کنید"

            )

            keyboard = []

            for amount in db["wallet_prices"]:

                keyboard.append([

                    InlineKeyboardButton(

                        f"{amount:,} تومان",

                        callback_data=

                        f"wallet_{amount}"

                    )

                ])

            update.message.reply_text(

                msg,

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # TEST
        # =====================================

        if text == "🎁 تست":

            keyboard = InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(

                        "🎁 دریافت تست",

                        callback_data="get_test"

                    )

                ]

            ])

            update.message.reply_text(

                "🎁 دریافت تست رایگان",

                reply_markup=keyboard

            )

            return

# =========================================
# SHOW PLANS
# این تابع را بالای main()
# اضافه کن
# =========================================

def show_plans(

    query,
    cat_id

):

    plans = []

    for plan in db["plans"]:

        if plan["cat"] == cat_id:

            plans.append(plan)

    if len(plans) == 0:

        query.message.reply_text(

            "❌ پلنی وجود ندارد"

        )

        return

    keyboard = []

    for plan in plans:

        text = (

            f"{plan['name']} | "

            f"{plan['volume']}GB | "

            f"{plan['days']} روز | "

            f"{plan['price']:,}"

        )

        keyboard.append([

            InlineKeyboardButton(

                text,

                callback_data=

                f"plan_{plan['id']}"

            )

        ])

    query.message.reply_text(

        "📦 پلن موردنظر را انتخاب کنید",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )

# =========================================
# START FUNCTION
# این تابع را جایگزین
# start
# قبلی کن
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

        name = update.effective_user.first_name

        txt = db["texts"]["welcome"]

        txt = txt.replace(

            "{name}",

            name

        )

        if is_admin(uid):

            update.message.reply_text(

                txt,

                reply_markup=admin_menu()

            )

        else:

            update.message.reply_text(

                txt,

                reply_markup=main_menu()

            )

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

# =========================================
# START SCHEDULER
# این بخش را داخل main()
# قبل از updater.start_polling()
# اضافه کن
# =========================================

        Thread(

            target=scheduler_loop,

            daemon=True

        ).start()

# =========================================
# DEFAULT TEXTS
# این بخش را داخل load_db()
# در قسمت ساخت دیتابیس اولیه
# اضافه کن
# =========================================

            "texts": {

                "welcome":

                "👋 سلام {name}\n"

                "به فروشگاه VPN خوش آمدید",

                "support":

                "🆘 جهت پشتیبانی پیام دهید",

                "guide":

                "📚 آموزش اتصال VPN",

                "config_send":

                "✅ سرویس شما آماده شد\n\n"

                "👤 نام: {name}\n"

                "📊 حجم: {volume}GB\n"

                "📅 مدت: {days} روز\n\n"

                "{config}",

                "wait_admin":

                "⏳ منتظر تایید ادمین باشید",

                "wait_manual":

                "⏳ منتظر ارسال کانفیگ توسط ادمین باشید"

            }

# =========================================
# END OF FILE
# =========================================

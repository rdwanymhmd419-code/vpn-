# =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 1
# =========================================

import os
import json
import uuid
import base64
import random
import logging
import traceback
import requests

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
    CallbackQueryHandler,
    MessageHandler,
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

    return "BOT RUNNING", 200

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

# =========================================
# TOKEN
# =========================================

TOKEN = "8681405252:AAH7ONTudaE34evtbxWeLdk0dtZc_XkULEA"

# =========================================
# ADMINS
# =========================================

MAIN_ADMIN = 5993860770

ADMINS = [5993860770]

# =========================================
# PANEL
# =========================================

PANEL_URL = "http://87.248.152.205:8081"

PANEL_PATH = "/hke43Y4nhZ23K1vc4S"

PANEL_USER = "amir"

PANEL_PASS = "amirreza871221"

INBOUND_ID = 1

# =========================================
# FILES
# =========================================

DB_FILE = "database.json"

# =========================================
# SESSION
# =========================================

session = requests.Session()

# =========================================
# DATABASE
# =========================================

def default_db():

    return {

        "brand": "تک نت VPN",

        "bot_enabled": True,

        "auto_send": True,

        "manual_send": True,

        "wallet_prices": [

            100000,

            300000,

            500000,

            1000000,

            2000000

        ],

        "card": {

            "number": "6277601368776066",

            "name": "محمد رضوانی"

        },

        "support": "@support",

        "guide": "@guide",

        "payment_methods": {

            "card": True,

            "gateway": False,

            "crypto": False

        },

        "test_settings": {

            "enabled": True,

            "volume": 1,

            "days": 1

        },

        "texts": {

            "welcome":

            "🔰 به {brand} خوش آمدید",

            "support":

            "👤 پشتیبانی:\n{support}",

            "guide":

            "📚 آموزش:\n{guide}",

            "invoice":

            "🧾 فاکتور شما آماده شد",

            "wait_admin":

            "⏳ منتظر تایید ادمین باشید",

            "wallet_ok":

            "✅ کیف پول شما شارژ شد",

            "config":

            "🎉 سرویس شما آماده شد\n\n"

            "📦 پلن: {name}\n"

            "📊 حجم: {volume}\n"

            "📅 مدت: {days} روز\n\n"

            "🔗 کانفیگ:\n"

            "{config}"

        },

        "categories": [

            {

                "id": 1,

                "name": "🚀 قوی"

            },

            {

                "id": 2,

                "name": "💎 اقتصادی"

            }

        ],

        "plans": [

            {

                "id": 1,

                "cat": 1,

                "name": "20GB VIP",

                "price": 80000,

                "volume": 20,

                "days": 30,

                "users": 1

            },

            {

                "id": 2,

                "cat": 2,

                "name": "10GB Eco",

                "price": 45000,

                "volume": 10,

                "days": 30,

                "users": 1

            }

        ],

        "users": {}

    }

# =========================================
# LOAD DB
# =========================================

def load_db():

    try:

        if os.path.exists(DB_FILE):

            with open(

                DB_FILE,

                "r",

                encoding="utf-8"

            ) as f:

                return json.load(f)

    except:

        pass

    return default_db()

db = load_db()

# =========================================
# SAVE DB
# =========================================

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

            indent=4

        )

# =========================================
# STATES
# =========================================

state = {}

# =========================================
# HELPERS
# =========================================

def is_admin(uid):

    return int(uid) in ADMINS

def ensure_user(uid):

    uid = str(uid)

    if uid not in db["users"]:

        db["users"][uid] = {

            "wallet": 0,

            "purchases": [],

            "joined": str(datetime.now())

        }

        save_db()
      # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 2
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# MAIN MENU
# =========================================

def main_menu(uid):

    kb = [

        ['💰 خرید سرویس', '👛 کیف پول'],

        ['🎁 تست رایگان', '📂 سرویس‌های من'],

        ['📚 آموزش', '👤 پشتیبانی']

    ]

    if is_admin(uid):

        kb.append(['⚙️ مدیریت'])

    return ReplyKeyboardMarkup(

        kb,

        resize_keyboard=True

    )

# =========================================
# ADMIN MENU
# =========================================

def admin_menu():

    kb = [

        ['📦 مدیریت پلن‌ها', '🗂 مدیریت دسته‌بندی'],

        ['⚙️ تنظیمات تست', '💳 روش پرداخت'],

        ['👛 تنظیمات کیف پول', '📝 ویرایش متن‌ها'],

        ['🤖 ارسال خودکار', '📨 ارسال دستی'],

        ['📢 ارسال همگانی', '✉️ ارسال پیام'],

        ['👤 افزودن ادمین', '📊 آمار'],

        ['💾 بکاپ', '🔙 بازگشت']

    ]

    return ReplyKeyboardMarkup(

        kb,

        resize_keyboard=True

    )

# =========================================
# BACK MENU
# =========================================

def back_menu():

    return ReplyKeyboardMarkup(

        [['🔙 بازگشت']],

        resize_keyboard=True

    )

# =========================================
# PANEL LOGIN
# =========================================

def panel_login():

    try:

        url = (

            f"{PANEL_URL}"

            f"{PANEL_PATH}"

            f"/login"

        )

        data = {

            "username": PANEL_USER,

            "password": PANEL_PASS

        }

        r = session.post(

            url,

            data=data,

            timeout=20

        )

        if r.status_code == 200:

            return True

        return False

    except Exception as e:

        logger.error(

            f"PANEL LOGIN ERROR: {e}"

        )

        return False

# =========================================
# CREATE CONFIG
# =========================================

def create_config(

    email,

    limit_ip,

    total_gb,

    days

):

    try:

        login = panel_login()

        if not login:

            return None

        total_bytes = (

            total_gb *

            1024 *

            1024 *

            1024

        )

        expiry = int(

            (

                datetime.now().timestamp()

                +

                (days * 86400)

            ) * 1000

        )

        client_id = str(uuid.uuid4())

        settings = {

            "clients": [

                {

                    "id": client_id,

                    "alterId": 0,

                    "email": email,

                    "limitIp": limit_ip,

                    "totalGB": total_bytes,

                    "expiryTime": expiry,

                    "enable": True,

                    "tgId": "",

                    "subId": str(uuid.uuid4())[:16]

                }

            ]

        }

        payload = {

            "id": INBOUND_ID,

            "settings": json.dumps(settings)

        }

        url = (

            f"{PANEL_URL}"

            f"{PANEL_PATH}"

            f"/panel/inbound/addClient"

        )

        r = session.post(

            url,

            data=payload,

            timeout=20

        )

        if r.status_code != 200:

            return None

        return {

            "uuid": client_id,

            "email": email

        }

    except Exception as e:

        logger.error(

            f"CREATE CONFIG ERROR: {e}"

        )

        return None

# =========================================
# BUILD VMESS
# =========================================

def build_vmess(

    uuid_code,

    email

):

    try:

        config = {

            "v": "2",

            "ps": email,

            "add": "87.248.152.205",

            "port": "443",

            "id": uuid_code,

            "aid": "0",

            "scy": "auto",

            "net": "ws",

            "type": "none",

            "host": "",

            "path": "/",

            "tls": "tls"

        }

        encoded = base64.b64encode(

            json.dumps(config).encode()

        ).decode()

        return f"vmess://{encoded}"

    except:

        return None

# =========================================
# SEND CONFIG
# =========================================

def deliver_config(

    context,

    user_id,

    plan,

    account_name

):

    try:

        email = (

            account_name

            +

            "_"

            +

            str(random.randint(1000,9999))

        )

        result = create_config(

            email=email,

            limit_ip=plan["users"],

            total_gb=plan["volume"],

            days=plan["days"]

        )

        if not result:

            return False

        link = build_vmess(

            result["uuid"],

            result["email"]

        )

        if not link:

            return False

        txt = db["texts"]["config"]

        txt = txt.replace(

            "{name}",

            plan["name"]

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

            link

        )

        context.bot.send_message(

            int(user_id),

            txt

        )

        db["users"][str(user_id)]["purchases"].append({

            "name": plan["name"],

            "volume": plan["volume"],

            "days": plan["days"],

            "date": str(datetime.now())

        })

        save_db()

        return True

    except Exception as e:

        logger.error(

            f"DELIVER ERROR: {e}"

        )

        return False

# =========================================
# START
# =========================================

def start(update, context):

    uid = str(

        update.effective_user.id

    )

    ensure_user(uid)

    txt = db["texts"]["welcome"]

    txt = txt.replace(

        "{brand}",

        db["brand"]

    )

    update.message.reply_text(

        txt,

        reply_markup=main_menu(uid)

)
  # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 3
# ادامه مستقیم فایل main.py
# =========================================

# =========================================
# SHOW CATEGORIES
# =========================================

def show_categories(

    update,

    context

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

        "📂 دسته‌بندی مورد نظر را انتخاب کنید:",

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

            text = (

                f"{plan['name']} | "

                f"{plan['volume']}GB | "

                f"{plan['days']} روز | "

                f"{plan['price']:,} تومان"

            )

            keyboard.append([

                InlineKeyboardButton(

                    text,

                    callback_data=f"plan_{plan['id']}"

                )

            ])

    if not found:

        query.message.reply_text(

            "❌ پلنی یافت نشد"

        )

        return

    query.message.reply_text(

        "📦 پلن مورد نظر را انتخاب کنید:",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )

# =========================================
# WALLET MENU
# =========================================

def wallet_menu(

    update,

    context

):

    uid = str(

        update.effective_user.id

    )

    wallet = db["users"][uid]["wallet"]

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

            "💵 مبلغ دلخواه",

            callback_data="wallet_custom"

        )

    ])

    txt = (

        f"👛 کیف پول شما\n\n"

        f"💰 موجودی: {wallet:,} تومان\n\n"

        f"مبلغ شارژ را انتخاب کنید:"

    )

    update.message.reply_text(

        txt,

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )

# =========================================
# SERVICE MENU
# =========================================

def my_services(

    update,

    context

):

    uid = str(

        update.effective_user.id

    )

    purchases = db["users"][uid]["purchases"]

    if not purchases:

        update.message.reply_text(

            "❌ هنوز سرویسی ندارید"

        )

        return

    txt = "📂 سرویس‌های شما\n\n"

    for i in purchases:

        txt += (

            f"📦 {i['name']}\n"

            f"📊 {i['volume']}GB\n"

            f"📅 {i['days']} روز\n\n"

        )

    update.message.reply_text(txt)

# =========================================
# FREE TEST
# =========================================

def free_test(

    update,

    context

):

    uid = str(

        update.effective_user.id

    )

    settings = db["test_settings"]

    if not settings["enabled"]:

        update.message.reply_text(

            "❌ تست غیرفعال است"

        )

        return

    try:

        email = (

            "test_"

            +

            str(random.randint(1000,9999))

        )

        result = create_config(

            email=email,

            limit_ip=1,

            total_gb=settings["volume"],

            days=settings["days"]

        )

        if not result:

            update.message.reply_text(

                "❌ خطا در ساخت تست"

            )

            return

        link = build_vmess(

            result["uuid"],

            result["email"]

        )

        txt = (

            "🎁 تست رایگان شما آماده شد\n\n"

            f"📊 حجم: {settings['volume']}GB\n"

            f"📅 مدت: {settings['days']} روز\n\n"

            f"{link}"

        )

        context.bot.send_message(

            int(uid),

            txt

        )

    except Exception as e:

        logger.error(

            f"TEST ERROR: {e}"

        )

        update.message.reply_text(

            "❌ خطا"

        )

# =========================================
# HANDLE MESSAGE
# =========================================

def handle_message(

    update,

    context

):

    try:

        uid = str(

            update.effective_user.id

        )

        ensure_user(uid)

        text = update.message.text

        step = state.get(uid, {}).get("step")

        # =====================================
        # BOT DISABLED
        # =====================================

        if (

            not db["bot_enabled"]

            and

            not is_admin(uid)

        ):

            update.message.reply_text(

                "⛔️ ربات موقتاً غیرفعال است"

            )

            return

        # =====================================
        # BACK
        # =====================================

        if text == "🔙 بازگشت":

            state[uid] = {}

            update.message.reply_text(

                "🏠 منوی اصلی",

                reply_markup=main_menu(uid)

            )

            return

        # =====================================
        # BUY
        # =====================================

        if text == "💰 خرید سرویس":

            show_categories(

                update,

                context

            )

            return

        # =====================================
        # WALLET
        # =====================================

        if text == "👛 کیف پول":

            wallet_menu(

                update,

                context

            )

            return

        # =====================================
        # TEST
        # =====================================

        if text == "🎁 تست رایگان":

            free_test(

                update,

                context

            )

            return

        # =====================================
        # SERVICES
        # =====================================

        if text == "📂 سرویس‌های من":

            my_services(

                update,

                context

            )

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

        # =====================================
        # ADMIN PANEL
        # =====================================

        if (

            text == "⚙️ مدیریت"

            and

            is_admin(uid)

        ):

            update.message.reply_text(

                "⚙️ پنل مدیریت",

                reply_markup=admin_menu()

            )

            return
          # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 4
# ادامه مستقیم فایل main.py
# =========================================

        # =====================================
        # ADMIN - STATISTICS
        # =====================================

        if (

            text == "📊 آمار"

            and

            is_admin(uid)

        ):

            total_users = len(

                db["users"]

            )

            total_plans = len(

                db["plans"]

            )

            total_categories = len(

                db["categories"]

            )

            total_wallet = 0

            for u in db["users"]:

                total_wallet += db["users"][u]["wallet"]

            txt = (

                "📊 آمار ربات\n\n"

                f"👤 کاربران: {total_users}\n"

                f"📦 پلن‌ها: {total_plans}\n"

                f"🗂 دسته‌ها: {total_categories}\n"

                f"💰 مجموع کیف پول: {total_wallet:,}"

            )

            update.message.reply_text(txt)

            return

        # =====================================
        # ADMIN - AUTO SEND
        # =====================================

        if (

            text == "🤖 ارسال خودکار"

            and

            is_admin(uid)

        ):

            db["auto_send"] = (

                not db["auto_send"]

            )

            save_db()

            status = (

                "فعال"

                if db["auto_send"]

                else "غیرفعال"

            )

            update.message.reply_text(

                f"✅ ارسال خودکار: {status}"

            )

            return

        # =====================================
        # ADMIN - MANUAL SEND
        # =====================================

        if (

            text == "📨 ارسال دستی"

            and

            is_admin(uid)

        ):

            db["manual_send"] = (

                not db["manual_send"]

            )

            save_db()

            status = (

                "فعال"

                if db["manual_send"]

                else "غیرفعال"

            )

            update.message.reply_text(

                f"✅ ارسال دستی: {status}"

            )

            return

        # =====================================
        # ADMIN - TEST SETTINGS
        # =====================================

        if (

            text == "⚙️ تنظیمات تست"

            and

            is_admin(uid)

        ):

            keyboard = [

                [

                    InlineKeyboardButton(

                        "✅ فعال",

                        callback_data="test_on"

                    ),

                    InlineKeyboardButton(

                        "❌ غیرفعال",

                        callback_data="test_off"

                    )

                ],

                [

                    InlineKeyboardButton(

                        "⚙️ تنظیم حجم",

                        callback_data="set_test_volume"

                    )

                ],

                [

                    InlineKeyboardButton(

                        "📅 تنظیم روز",

                        callback_data="set_test_days"

                    )

                ]

            ]

            txt = (

                "⚙️ تنظیمات تست\n\n"

                f"وضعیت: "

                f"{'فعال' if db['test_settings']['enabled'] else 'غیرفعال'}\n"

                f"حجم: "

                f"{db['test_settings']['volume']}GB\n"

                f"روز: "

                f"{db['test_settings']['days']}"

            )

            update.message.reply_text(

                txt,

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # ADMIN - PAYMENT METHODS
        # =====================================

        if (

            text == "💳 روش پرداخت"

            and

            is_admin(uid)

        ):

            methods = db["payment_methods"]

            txt = (

                "💳 مدیریت روش پرداخت\n\n"

                f"کارت: "

                f"{'✅' if methods['card'] else '❌'}\n"

                f"درگاه: "

                f"{'✅' if methods['gateway'] else '❌'}\n"

                f"رمزارز: "

                f"{'✅' if methods['crypto'] else '❌'}"

            )

            keyboard = [

                [

                    InlineKeyboardButton(

                        "کارت",

                        callback_data="pay_card"

                    ),

                    InlineKeyboardButton(

                        "درگاه",

                        callback_data="pay_gateway"

                    ),

                    InlineKeyboardButton(

                        "رمزارز",

                        callback_data="pay_crypto"

                    )

                ]

            ]

            update.message.reply_text(

                txt,

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # ADMIN - ADD ADMIN
        # =====================================

        if (

            text == "👤 افزودن ادمین"

            and

            int(uid) == MAIN_ADMIN

        ):

            state[uid] = {

                "step": "add_admin"

            }

            update.message.reply_text(

                "🆔 آیدی عددی ادمین را ارسال کنید",

                reply_markup=back_menu()

            )

            return

        # =====================================
        # ADMIN - BROADCAST
        # =====================================

        if (

            text == "📢 ارسال همگانی"

            and

            is_admin(uid)

        ):

            state[uid] = {

                "step": "broadcast"

            }

            update.message.reply_text(

                "📨 پیام را ارسال کنید",

                reply_markup=back_menu()

            )

            return

        # =====================================
        # ADMIN - PRIVATE MESSAGE
        # =====================================

        if (

            text == "✉️ ارسال پیام"

            and

            is_admin(uid)

        ):

            state[uid] = {

                "step": "private_user"

            }

            update.message.reply_text(

                "🆔 آیدی کاربر را ارسال کنید",

                reply_markup=back_menu()

            )

            return

        # =====================================
        # ADMIN - WALLET SETTINGS
        # =====================================

        if (

            text == "👛 تنظیمات کیف پول"

            and

            is_admin(uid)

        ):

            prices = db["wallet_prices"]

            txt = "👛 مبالغ فعلی:\n\n"

            for p in prices:

                txt += f"{p:,} تومان\n"

            txt += (

                "\nمبالغ جدید را با , وارد کنید\n"

                "مثال:\n"

                "100000,300000,500000"

            )

            state[uid] = {

                "step": "wallet_prices"

            }

            update.message.reply_text(

                txt,

                reply_markup=back_menu()

            )

            return
          # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 5
# ادامه مستقیم فایل main.py
# =========================================

        # =====================================
        # ADMIN - EDIT TEXTS
        # =====================================

        if (

            text == "📝 ویرایش متن‌ها"

            and

            is_admin(uid)

        ):

            keyboard = [

                [

                    InlineKeyboardButton(

                        "خوش آمد",

                        callback_data="text_welcome"

                    )

                ],

                [

                    InlineKeyboardButton(

                        "پشتیبانی",

                        callback_data="text_support"

                    )

                ],

                [

                    InlineKeyboardButton(

                        "آموزش",

                        callback_data="text_guide"

                    )

                ],

                [

                    InlineKeyboardButton(

                        "فاکتور",

                        callback_data="text_invoice"

                    )

                ],

                [

                    InlineKeyboardButton(

                        "کانفیگ",

                        callback_data="text_config"

                    )

                ]

            ]

            update.message.reply_text(

                "📝 متن مورد نظر را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # ADMIN - CATEGORY MANAGEMENT
        # =====================================

        if (

            text == "🗂 مدیریت دسته‌بندی"

            and

            is_admin(uid)

        ):

            keyboard = [

                [

                    InlineKeyboardButton(

                        "➕ افزودن دسته",

                        callback_data="add_category"

                    )

                ]

            ]

            for cat in db["categories"]:

                keyboard.append([

                    InlineKeyboardButton(

                        f"❌ حذف {cat['name']}",

                        callback_data=f"delcat_{cat['id']}"

                    )

                ])

            update.message.reply_text(

                "🗂 مدیریت دسته‌بندی",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # ADMIN - PLAN MANAGEMENT
        # =====================================

        if (

            text == "📦 مدیریت پلن‌ها"

            and

            is_admin(uid)

        ):

            keyboard = [

                [

                    InlineKeyboardButton(

                        "➕ افزودن پلن",

                        callback_data="add_plan"

                    )

                ]

            ]

            for plan in db["plans"]:

                keyboard.append([

                    InlineKeyboardButton(

                        f"❌ {plan['name']}",

                        callback_data=f"delplan_{plan['id']}"

                    )

                ])

            update.message.reply_text(

                "📦 مدیریت پلن‌ها",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # ADD ADMIN STEP
        # =====================================

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

            except:

                update.message.reply_text(

                    "❌ آیدی نامعتبر"

                )

            return

        # =====================================
        # PRIVATE MESSAGE STEP
        # =====================================

        if step == "private_user":

            state[uid] = {

                "step": "private_message",

                "target": text

            }

            update.message.reply_text(

                "📨 پیام را ارسال کنید"

            )

            return

        # =====================================
        # PRIVATE MESSAGE SEND
        # =====================================

        if step == "private_message":

            target = state[uid]["target"]

            try:

                context.bot.send_message(

                    int(target),

                    text

                )

                update.message.reply_text(

                    "✅ پیام ارسال شد",

                    reply_markup=admin_menu()

                )

            except:

                update.message.reply_text(

                    "❌ خطا در ارسال"

                )

            state[uid] = {}

            return

        # =====================================
        # BROADCAST STEP
        # =====================================

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

            update.message.reply_text(

                f"✅ ارسال شد\n\n"

                f"موفق: {success}\n"

                f"ناموفق: {failed}",

                reply_markup=admin_menu()

            )

            state[uid] = {}

            return

        # =====================================
        # WALLET PRICE SETTINGS
        # =====================================

        if step == "wallet_prices":

            try:

                prices = text.split(",")

                new_prices = []

                for p in prices:

                    new_prices.append(

                        int(p.strip())

                    )

                db["wallet_prices"] = new_prices

                save_db()

                update.message.reply_text(

                    "✅ ذخیره شد",

                    reply_markup=admin_menu()

                )

                state[uid] = {}

            except:

                update.message.reply_text(

                    "❌ فرمت اشتباه"

                )

            return

        # =====================================
        # CUSTOM WALLET
        # =====================================

        if step == "custom_wallet":

            try:

                amount = int(text)

                if amount < 50000:

                    update.message.reply_text(

                        "❌ حداقل 50 هزار"

                    )

                    return

                if amount > 5000000:

                    update.message.reply_text(

                        "❌ حداکثر 5 میلیون"

                    )

                    return

                state[uid] = {

                    "step": "wallet_receipt",

                    "amount": amount

                }

                txt = (

                    "💳 پرداخت کیف پول\n\n"

                    f"💰 مبلغ: {amount:,}\n\n"

                    f"شماره کارت:\n"

                    f"{db['card']['number']}\n"

                    f"{db['card']['name']}\n\n"

                    "📸 فیش را ارسال کنید"

                )

                update.message.reply_text(txt)

            except:

                update.message.reply_text(

                    "❌ مبلغ نامعتبر"

                )

            return
          # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 6
# ادامه مستقیم فایل main.py
# =========================================

        # =====================================
        # ADD CATEGORY STEP
        # =====================================

        if step == "add_category":

            try:

                new_id = 1

                if db["categories"]:

                    new_id = max(

                        x["id"]

                        for x in db["categories"]

                    ) + 1

                db["categories"].append({

                    "id": new_id,

                    "name": text

                })

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ دسته‌بندی اضافه شد",

                    reply_markup=admin_menu()

                )

            except Exception as e:

                logger.error(e)

                update.message.reply_text(

                    "❌ خطا"

                )

            return

        # =====================================
        # ADD PLAN NAME
        # =====================================

        if step == "plan_name":

            state[uid]["name"] = text

            state[uid]["step"] = "plan_volume"

            update.message.reply_text(

                "📊 حجم پلن را وارد کنید\nمثال:\n20",

                reply_markup=back_menu()

            )

            return

        # =====================================
        # ADD PLAN VOLUME
        # =====================================

        if step == "plan_volume":

            try:

                state[uid]["volume"] = int(text)

                state[uid]["step"] = "plan_days"

                update.message.reply_text(

                    "📅 تعداد روز را وارد کنید"

                )

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

            return

        # =====================================
        # ADD PLAN DAYS
        # =====================================

        if step == "plan_days":

            try:

                state[uid]["days"] = int(text)

                state[uid]["step"] = "plan_users"

                update.message.reply_text(

                    "👥 تعداد کاربر"

                )

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

            return

        # =====================================
        # ADD PLAN USERS
        # =====================================

        if step == "plan_users":

            try:

                state[uid]["users"] = int(text)

                state[uid]["step"] = "plan_price"

                update.message.reply_text(

                    "💰 قیمت"

                )

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

            return

        # =====================================
        # ADD PLAN PRICE
        # =====================================

        if step == "plan_price":

            try:

                price = int(text)

                new_id = 1

                if db["plans"]:

                    new_id = max(

                        x["id"]

                        for x in db["plans"]

                    ) + 1

                db["plans"].append({

                    "id": new_id,

                    "cat": state[uid]["cat"],

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

            except Exception as e:

                logger.error(e)

                update.message.reply_text(

                    "❌ خطا"

                )

            return

        # =====================================
        # ACCOUNT NAME STEP
        # =====================================

        if step == "account_name":

            state[uid]["account_name"] = text

            plan = state[uid]["plan"]

            price = plan["price"]

            wallet = db["users"][uid]["wallet"]

            txt = (

                "🧾 پیش فاکتور\n\n"

                f"📦 پلن: {plan['name']}\n"

                f"📊 حجم: {plan['volume']}GB\n"

                f"📅 مدت: {plan['days']} روز\n"

                f"👥 کاربر: {plan['users']}\n"

                f"💰 مبلغ: {price:,} تومان\n\n"

                f"👛 موجودی کیف پول: {wallet:,}"

            )

            keyboard = [

                [

                    InlineKeyboardButton(

                        "💳 کارت به کارت",

                        callback_data="pay_card_buy"

                    )

                ],

                [

                    InlineKeyboardButton(

                        "👛 پرداخت با کیف پول",

                        callback_data="pay_wallet_buy"

                    )

                ],

                [

                    InlineKeyboardButton(

                        "🔀 ترکیبی",

                        callback_data="pay_mix_buy"

                    )

                ]

            ]

            update.message.reply_text(

                txt,

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # TEST VOLUME STEP
        # =====================================

        if step == "test_volume":

            try:

                volume = int(text)

                if volume < 1:

                    update.message.reply_text(

                        "❌ حداقل 1"

                    )

                    return

                if volume > 100:

                    update.message.reply_text(

                        "❌ حداکثر 100"

                    )

                    return

                db["test_settings"]["volume"] = volume

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ ذخیره شد",

                    reply_markup=admin_menu()

                )

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

            return

        # =====================================
        # TEST DAYS STEP
        # =====================================

        if step == "test_days":

            try:

                days = int(text)

                if days < 1:

                    update.message.reply_text(

                        "❌ حداقل 1"

                    )

                    return

                if days > 30:

                    update.message.reply_text(

                        "❌ حداکثر 30"

                    )

                    return

                db["test_settings"]["days"] = days

                save_db()

                state[uid] = {}

                update.message.reply_text(

                    "✅ ذخیره شد",

                    reply_markup=admin_menu()

                )

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

            return

    except Exception as e:

        logger.error(traceback.format_exc())

        update.message.reply_text(

            "❌ خطا"
          )
      # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 7
# ادامه مستقیم فایل main.py
# =========================================

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
        # CATEGORY SELECT
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
        # PLAN SELECT
        # =====================================

        if data.startswith("plan_"):

            plan_id = int(

                data.split("_")[1]

            )

            selected = None

            for p in db["plans"]:

                if p["id"] == plan_id:

                    selected = p

                    break

            if not selected:

                query.message.reply_text(

                    "❌ پلن یافت نشد"

                )

                return

            state[uid] = {

                "step": "account_name",

                "plan": selected

            }

            query.message.reply_text(

                "👤 اسم اکانت را وارد کنید",

                reply_markup=back_menu()

            )

            return

        # =====================================
        # WALLET BUTTON
        # =====================================

        if data.startswith("wallet_"):

            amount = int(

                data.split("_")[1]

            )

            state[uid] = {

                "step": "wallet_receipt",

                "amount": amount

            }

            txt = (

                "💳 شارژ کیف پول\n\n"

                f"💰 مبلغ: {amount:,}\n\n"

                f"شماره کارت:\n"

                f"{db['card']['number']}\n"

                f"{db['card']['name']}\n\n"

                "📸 فیش را ارسال کنید"

            )

            query.message.reply_text(txt)

            return

        # =====================================
        # CUSTOM WALLET
        # =====================================

        if data == "wallet_custom":

            state[uid] = {

                "step": "custom_wallet"

            }

            query.message.reply_text(

                "💰 مبلغ دلخواه را وارد کنید\n\n"

                "حداقل: 50 هزار\n"

                "حداکثر: 5 میلیون"

            )

            return

        # =====================================
        # PAY CARD BUY
        # =====================================

        if data == "pay_card_buy":

            plan = state[uid]["plan"]

            amount = plan["price"]

            txt = (

                "💳 پرداخت کارت به کارت\n\n"

                f"💰 مبلغ: {amount:,}\n\n"

                f"شماره کارت:\n"

                f"{db['card']['number']}\n"

                f"{db['card']['name']}\n\n"

                "📸 فیش را ارسال کنید"

            )

            state[uid]["step"] = "buy_receipt"

            query.message.reply_text(txt)

            return

        # =====================================
        # PAY WALLET BUY
        # =====================================

        if data == "pay_wallet_buy":

            plan = state[uid]["plan"]

            price = plan["price"]

            wallet = db["users"][uid]["wallet"]

            if wallet < price:

                query.message.reply_text(

                    "❌ موجودی کیف پول کافی نیست"

                )

                return

            db["users"][uid]["wallet"] -= price

            save_db()

            if db["auto_send"]:

                ok = deliver_config(

                    context,

                    uid,

                    plan,

                    state[uid]["account_name"]

                )

                if ok:

                    query.message.reply_text(

                        "✅ سرویس ارسال شد"

                    )

                else:

                    query.message.reply_text(

                        "❌ خطا در ساخت"

                    )

            else:

                txt = db["texts"]["wait_admin"]

                query.message.reply_text(txt)

            state[uid] = {}

            return

        # =====================================
        # PAY MIX BUY
        # =====================================

        if data == "pay_mix_buy":

            plan = state[uid]["plan"]

            price = plan["price"]

            wallet = db["users"][uid]["wallet"]

            remain = price - wallet

            if remain <= 0:

                remain = 0

            txt = (

                "🔀 پرداخت ترکیبی\n\n"

                f"💰 مبلغ کل: {price:,}\n"

                f"👛 کیف پول: {wallet:,}\n"

                f"💳 باقی مانده: {remain:,}\n\n"

                f"{db['card']['number']}\n"

                f"{db['card']['name']}\n\n"

                "📸 فیش باقی مانده را ارسال کنید"

            )

            state[uid]["step"] = "mix_receipt"

            state[uid]["remain"] = remain

            query.message.reply_text(txt)

            return

        # =====================================
        # TEST ON
        # =====================================

        if data == "test_on":

            db["test_settings"]["enabled"] = True

            save_db()

            query.message.reply_text(

                "✅ تست فعال شد"

            )

            return

        # =====================================
        # TEST OFF
        # =====================================

        if data == "test_off":

            db["test_settings"]["enabled"] = False

            save_db()

            query.message.reply_text(

                "❌ تست غیرفعال شد"

            )

            return

        # =====================================
        # SET TEST VOLUME
        # =====================================

        if data == "set_test_volume":

            state[uid] = {

                "step": "test_volume"

            }

            query.message.reply_text(

                "📊 حجم تست را وارد کنید"

            )

            return

        # =====================================
        # SET TEST DAYS
        # =====================================

        if data == "set_test_days":

            state[uid] = {

                "step": "test_days"

            }

            query.message.reply_text(

                "📅 تعداد روز تست"

            )

            return
          # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 8
# ادامه مستقیم فایل main.py
# =========================================

        # =====================================
        # PAYMENT METHODS
        # =====================================

        if data == "pay_card":

            db["payment_methods"]["card"] = (

                not db["payment_methods"]["card"]

            )

            save_db()

            query.message.reply_text(

                f"کارت: "

                f"{'فعال' if db['payment_methods']['card'] else 'غیرفعال'}"

            )

            return

        if data == "pay_gateway":

            db["payment_methods"]["gateway"] = (

                not db["payment_methods"]["gateway"]

            )

            save_db()

            query.message.reply_text(

                f"درگاه: "

                f"{'فعال' if db['payment_methods']['gateway'] else 'غیرفعال'}"

            )

            return

        if data == "pay_crypto":

            db["payment_methods"]["crypto"] = (

                not db["payment_methods"]["crypto"]

            )

            save_db()

            query.message.reply_text(

                f"رمزارز: "

                f"{'فعال' if db['payment_methods']['crypto'] else 'غیرفعال'}"

            )

            return

        # =====================================
        # DELETE CATEGORY
        # =====================================

        if data.startswith("delcat_"):

            cat_id = int(

                data.split("_")[1]

            )

            new_cats = []

            for c in db["categories"]:

                if c["id"] != cat_id:

                    new_cats.append(c)

            db["categories"] = new_cats

            new_plans = []

            for p in db["plans"]:

                if p["cat"] != cat_id:

                    new_plans.append(p)

            db["plans"] = new_plans

            save_db()

            query.message.reply_text(

                "✅ حذف شد"

            )

            return

        # =====================================
        # ADD CATEGORY
        # =====================================

        if data == "add_category":

            state[uid] = {

                "step": "add_category"

            }

            query.message.reply_text(

                "📝 نام دسته را وارد کنید"

            )

            return

        # =====================================
        # DELETE PLAN
        # =====================================

        if data.startswith("delplan_"):

            plan_id = int(

                data.split("_")[1]

            )

            new_plans = []

            for p in db["plans"]:

                if p["id"] != plan_id:

                    new_plans.append(p)

            db["plans"] = new_plans

            save_db()

            query.message.reply_text(

                "✅ پلن حذف شد"

            )

            return

        # =====================================
        # ADD PLAN
        # =====================================

        if data == "add_plan":

            keyboard = []

            for cat in db["categories"]:

                keyboard.append([

                    InlineKeyboardButton(

                        cat["name"],

                        callback_data=f"pickcat_{cat['id']}"

                    )

                ])

            query.message.reply_text(

                "🗂 دسته را انتخاب کنید",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # PICK CATEGORY
        # =====================================

        if data.startswith("pickcat_"):

            cat_id = int(

                data.split("_")[1]

            )

            state[uid] = {

                "step": "plan_name",

                "cat": cat_id

            }

            query.message.reply_text(

                "📝 نام پلن را وارد کنید"

            )

            return

        # =====================================
        # EDIT TEXTS
        # =====================================

        if data.startswith("text_"):

            text_key = data.replace(

                "text_",

                ""

            )

            state[uid] = {

                "step": "edit_text",

                "key": text_key

            }

            current = db["texts"].get(

                text_key,

                ""

            )

            query.message.reply_text(

                f"متن فعلی:\n\n{current}\n\n"

                "متن جدید را ارسال کنید"

            )

            return

    except Exception as e:

        logger.error(traceback.format_exc())

        query.message.reply_text(

            "❌ خطا"
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

        step = state.get(uid, {}).get("step")

        # =====================================
        # WALLET RECEIPT
        # =====================================

        if step == "wallet_receipt":

            amount = state[uid]["amount"]

            caption = (

                "💰 درخواست شارژ کیف پول\n\n"

                f"👤 کاربر: {uid}\n"

                f"💰 مبلغ: {amount:,}"

            )

            keyboard = [

                [

                    InlineKeyboardButton(

                        "✅ تایید",

                        callback_data=f"walletok_{uid}_{amount}"

                    ),

                    InlineKeyboardButton(

                        "❌ رد",

                        callback_data=f"walletreject_{uid}"

                    )

                ]

            ]

            context.bot.send_photo(

                MAIN_ADMIN,

                update.message.photo[-1].file_id,

                caption=caption,

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            update.message.reply_text(

                "✅ فیش ارسال شد"

            )

            state[uid] = {}

            return

        # =====================================
        # BUY RECEIPT
        # =====================================

        if step == "buy_receipt":

            plan = state[uid]["plan"]

            account_name = state[uid]["account_name"]

            caption = (

                "🛒 خرید جدید\n\n"

                f"👤 کاربر: {uid}\n"

                f"📦 پلن: {plan['name']}\n"

                f"👤 اکانت: {account_name}\n"

                f"💰 مبلغ: {plan['price']:,}"

            )

            keyboard = [

                [

                    InlineKeyboardButton(

                        "✅ تایید",

                        callback_data=f"buyok_{uid}"

                    ),

                    InlineKeyboardButton(

                        "❌ رد",

                        callback_data=f"buyreject_{uid}"

                    )

                ]

            ]

            context.bot.send_photo(

                MAIN_ADMIN,

                update.message.photo[-1].file_id,

                caption=caption,

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            update.message.reply_text(

                db["texts"]["wait_admin"]

            )

            return
# =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 9
# ادامه مستقیم فایل main.py
# =========================================

        # =====================================
        # MIX RECEIPT
        # =====================================

        if step == "mix_receipt":

            plan = state[uid]["plan"]

            remain = state[uid]["remain"]

            account_name = state[uid]["account_name"]

            caption = (

                "🔀 خرید ترکیبی\n\n"

                f"👤 کاربر: {uid}\n"

                f"📦 پلن: {plan['name']}\n"

                f"👤 اکانت: {account_name}\n"

                f"💰 باقی مانده: {remain:,}"

            )

            keyboard = [

                [

                    InlineKeyboardButton(

                        "✅ تایید",

                        callback_data=f"mixok_{uid}"

                    ),

                    InlineKeyboardButton(

                        "❌ رد",

                        callback_data=f"mixreject_{uid}"

                    )

                ]

            ]

            context.bot.send_photo(

                MAIN_ADMIN,

                update.message.photo[-1].file_id,

                caption=caption,

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            update.message.reply_text(

                db["texts"]["wait_admin"]

            )

            return

        # =====================================
        # BROADCAST PHOTO
        # =====================================

        if step == "broadcast_photo":

            file_id = update.message.photo[-1].file_id

            caption = state[uid].get(

                "caption",

                ""

            )

            success = 0

            failed = 0

            for user_id in db["users"]:

                try:

                    context.bot.send_photo(

                        int(user_id),

                        file_id,

                        caption=caption

                    )

                    success += 1

                except:

                    failed += 1

            update.message.reply_text(

                f"✅ ارسال شد\n\n"

                f"موفق: {success}\n"

                f"ناموفق: {failed}"

            )

            state[uid] = {}

            return

        # =====================================
        # PRIVATE MESSAGE PHOTO
        # =====================================

        if step == "send_private_photo":

            target = state[uid]["target"]

            file_id = update.message.photo[-1].file_id

            caption = update.message.caption or ""

            try:

                context.bot.send_photo(

                    int(target),

                    file_id,

                    caption=caption

                )

                update.message.reply_text(

                    "✅ ارسال شد"

                )

            except:

                update.message.reply_text(

                    "❌ خطا"

                )

            state[uid] = {}

            return

    except Exception as e:

        logger.error(traceback.format_exc())

# =========================================
# ADMIN CALLBACKS
# =========================================

def admin_callbacks(

    update,

    context

):

    try:

        query = update.callback_query

        data = query.data

        uid = str(

            query.from_user.id

        )

        # =====================================
        # WALLET OK
        # =====================================

        if data.startswith("walletok_"):

            parts = data.split("_")

            target = parts[1]

            amount = int(parts[2])

            ensure_user(target)

            db["users"][target]["wallet"] += amount

            save_db()

            context.bot.send_message(

                int(target),

                f"✅ کیف پول شما شارژ شد\n\n"

                f"💰 مبلغ: {amount:,}"

            )

            query.edit_message_caption(

                caption=query.message.caption + "\n\n✅ تایید شد"

            )

            return

        # =====================================
        # BUY OK
        # =====================================

        if data.startswith("buyok_"):

            target = data.split("_")[1]

            ensure_user(target)

            st = state.get(target)

            if not st:

                query.message.reply_text(

                    "❌ اطلاعات خرید یافت نشد"

                )

                return

            plan = st["plan"]

            account_name = st["account_name"]

            # =================================
            # AUTO SEND CONFIG
            # =================================

            if db["auto_send"]:

                ok = deliver_config(

                    context,

                    target,

                    plan,

                    account_name

                )

                if ok:

                    query.message.reply_text(

                        "✅ کانفیگ ارسال شد"

                    )

                else:

                    query.message.reply_text(

                        "❌ کانفیگ موجود نیست"

                    )

            else:

                context.bot.send_message(

                    int(target),

                    db["texts"]["wait_manual"]

                )

                state[MAIN_ADMIN_STR] = {

                    "step": "manual_send",

                    "target": target,

                    "plan": plan

                }

                query.message.reply_text(

                    "📨 کانفیگ را دستی ارسال کنید"

                )

            query.edit_message_caption(

                caption=query.message.caption + "\n\n✅ تایید شد"

            )

            return

        # =====================================
        # MIX OK
        # =====================================

        if data.startswith("mixok_"):

            target = data.split("_")[1]

            ensure_user(target)

            st = state.get(target)

            if not st:

                query.message.reply_text(

                    "❌ اطلاعات یافت نشد"

                )

                return

            plan = st["plan"]

            account_name = st["account_name"]

            wallet = db["users"][target]["wallet"]

            db["users"][target]["wallet"] = 0

            save_db()

            if db["auto_send"]:

                ok = deliver_config(

                    context,

                    target,

                    plan,

                    account_name

                )

                if ok:

                    query.message.reply_text(

                        "✅ کانفیگ ارسال شد"

                    )

                else:

                    query.message.reply_text(

                        "❌ کانفیگ موجود نیست"

                    )

            else:

                context.bot.send_message(

                    int(target),

                    db["texts"]["wait_manual"]

                )

            query.edit_message_caption(

                caption=query.message.caption + "\n\n✅ تایید شد"

            )

            return
            # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 10
# ادامه مستقیم فایل main.py
# =========================================

        # =====================================
        # BUY REJECT
        # =====================================

        if data.startswith("buyreject_"):

            target = data.split("_")[1]

            state[uid] = {

                "step": "reject_reason",

                "target": target

            }

            query.message.reply_text(

                "❌ دلیل رد را وارد کنید"

            )

            return

        # =====================================
        # MIX REJECT
        # =====================================

        if data.startswith("mixreject_"):

            target = data.split("_")[1]

            state[uid] = {

                "step": "reject_reason",

                "target": target

            }

            query.message.reply_text(

                "❌ دلیل رد را وارد کنید"

            )

            return

        # =====================================
        # WALLET REJECT
        # =====================================

        if data.startswith("walletreject_"):

            target = data.split("_")[1]

            state[uid] = {

                "step": "wallet_reject_reason",

                "target": target

            }

            query.message.reply_text(

                "❌ دلیل رد شارژ کیف پول"

            )

            return

        # =====================================
        # ADD CONFIG
        # =====================================

        if data == "add_config":

            keyboard = []

            for plan in db["plans"]:

                keyboard.append([

                    InlineKeyboardButton(

                        plan["name"],

                        callback_data=f"cfgplan_{plan['id']}"

                    )

                ])

            query.message.reply_text(

                "📦 انتخاب پلن",

                reply_markup=InlineKeyboardMarkup(

                    keyboard

                )

            )

            return

        # =====================================
        # CONFIG PLAN
        # =====================================

        if data.startswith("cfgplan_"):

            plan_id = int(

                data.split("_")[1]

            )

            state[uid] = {

                "step": "config_count",

                "plan_id": plan_id

            }

            query.message.reply_text(

                "📥 چند کانفیگ می‌خواهید اضافه کنید؟"

            )

            return

        # =====================================
        # AUTO SEND TOGGLE
        # =====================================

        if data == "toggle_auto_send":

            db["auto_send"] = (

                not db["auto_send"]

            )

            save_db()

            query.message.reply_text(

                f"ارسال خودکار: "

                f"{'فعال' if db['auto_send'] else 'غیرفعال'}"

            )

            return

        # =====================================
        # MANUAL SEND TOGGLE
        # =====================================

        if data == "toggle_manual_send":

            db["manual_send"] = (

                not db["manual_send"]

            )

            save_db()

            query.message.reply_text(

                f"ارسال دستی: "

                f"{'فعال' if db['manual_send'] else 'غیرفعال'}"

            )

            return

        # =====================================
        # BACKUP CREATE
        # =====================================

        if data == "backup_create":

            backup_name = (

                f"backup_"

                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

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

            context.bot.send_document(

                MAIN_ADMIN,

                open(backup_name, "rb")

            )

            query.message.reply_text(

                "✅ بکاپ ارسال شد"

            )

            return

        # =====================================
        # BACKUP RESTORE
        # =====================================

        if data == "backup_restore":

            state[uid] = {

                "step": "restore_backup"

            }

            query.message.reply_text(

                "📤 فایل بکاپ را ارسال کنید"

            )

            return

        # =====================================
        # BOT OFF
        # =====================================

        if data == "bot_off":

            db["bot_enabled"] = False

            save_db()

            query.message.reply_text(

                "🔴 ربات خاموش شد"

            )

            return

        # =====================================
        # BOT ON
        # =====================================

        if data == "bot_on":

            db["bot_enabled"] = True

            save_db()

            query.message.reply_text(

                "🟢 ربات روشن شد"

            )

            return

        # =====================================
        # PIN MESSAGE
        # =====================================

        if data == "pin_message":

            state[uid] = {

                "step": "pin_message"

            }

            query.message.reply_text(

                "📌 پیام را ارسال کنید"

            )

            return

    except Exception as e:

        logger.error(traceback.format_exc())

# =========================================
# SEND CONFIG FUNCTION
# =========================================

def deliver_config(

    context,

    user_id,

    plan,

    account_name

):

    try:

        plan_id = plan["id"]

        if str(plan_id) not in db["configs"]:

            return False

        configs = db["configs"][str(plan_id)]

        if len(configs) == 0:

            return False

        config = configs.pop(0)

        save_db()

        txt = db["texts"]["config_send"]

        txt = txt.replace(

            "{config}",

            config

        )

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

        context.bot.send_message(

            int(user_id),

            txt

        )

        # SAVE SERVICE

        db["users"][str(user_id)]["services"].append({

            "name": plan["name"],

            "volume": plan["volume"],

            "days": plan["days"],

            "date": str(datetime.now())

        })

        save_db()

        return True

    except Exception as e:

        logger.error(e)

        return False
        # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 11
# ادامه مستقیم فایل main.py
# =========================================

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

        step = state.get(uid, {}).get("step")

        # =====================================
        # RESTORE BACKUP
        # =====================================

        if step == "restore_backup":

            file = update.message.document.get_file()

            file.download(

                "restore.json"

            )

            with open(

                "restore.json",

                "r",

                encoding="utf-8"

            ) as f:

                new_db = json.load(f)

            db.clear()

            db.update(new_db)

            save_db()

            state[uid] = {}

            update.message.reply_text(

                "✅ بکاپ با موفقیت بازگردانی شد"

            )

            return

    except Exception as e:

        logger.error(traceback.format_exc())

# =========================================
# FINAL MESSAGE STEPS
# =========================================

def final_steps(

    update,

    context

):

    try:

        uid = str(

            update.effective_user.id

        )

        text = update.message.text

        step = state.get(uid, {}).get("step")

        # =====================================
        # CONFIG COUNT
        # =====================================

        if step == "config_count":

            try:

                count = int(text)

                if count < 1:

                    update.message.reply_text(

                        "❌ حداقل 1"

                    )

                    return

                state[uid]["count"] = count

                state[uid]["step"] = "configs_text"

                update.message.reply_text(

                    "📥 کانفیگ‌ها را ارسال کنید\n\n"

                    "بین هر کانفیگ دو خط خالی بگذارید"

                )

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

            return

        # =====================================
        # CONFIGS TEXT
        # =====================================

        if step == "configs_text":

            plan_id = state[uid]["plan_id"]

            configs = [

                x.strip()

                for x in text.split("\n\n")

                if x.strip()

            ]

            if len(configs) == 0:

                update.message.reply_text(

                    "❌ کانفیگی یافت نشد"

                )

                return

            if str(plan_id) not in db["configs"]:

                db["configs"][str(plan_id)] = []

            added = 0

            for cfg in configs:

                if cfg not in db["configs"][str(plan_id)]:

                    db["configs"][str(plan_id)].append(

                        cfg

                    )

                    added += 1

            save_db()

            state[uid] = {}

            update.message.reply_text(

                f"✅ {added} کانفیگ ذخیره شد",

                reply_markup=admin_menu()

            )

            return

        # =====================================
        # REJECT REASON
        # =====================================

        if step == "reject_reason":

            target = state[uid]["target"]

            context.bot.send_message(

                int(target),

                f"❌ خرید شما رد شد\n\n"

                f"دلیل:\n{text}"

            )

            update.message.reply_text(

                "✅ ارسال شد"

            )

            state[uid] = {}

            return

        # =====================================
        # WALLET REJECT REASON
        # =====================================

        if step == "wallet_reject_reason":

            target = state[uid]["target"]

            context.bot.send_message(

                int(target),

                f"❌ شارژ کیف پول رد شد\n\n"

                f"دلیل:\n{text}"

            )

            update.message.reply_text(

                "✅ ارسال شد"

            )

            state[uid] = {}

            return

        # =====================================
        # EDIT TEXT
        # =====================================

        if step == "edit_text":

            key = state[uid]["key"]

            db["texts"][key] = text

            save_db()

            state[uid] = {}

            update.message.reply_text(

                "✅ متن ذخیره شد",

                reply_markup=admin_menu()

            )

            return

        # =====================================
        # CUSTOM WALLET
        # =====================================

        if step == "custom_wallet":

            try:

                amount = int(text)

                if amount < 50000:

                    update.message.reply_text(

                        "❌ حداقل 50 هزار"

                    )

                    return

                if amount > 5000000:

                    update.message.reply_text(

                        "❌ حداکثر 5 میلیون"

                    )

                    return

                state[uid] = {

                    "step": "wallet_receipt",

                    "amount": amount

                }

                txt = (

                    "💳 پرداخت\n\n"

                    f"💰 مبلغ: {amount:,}\n\n"

                    f"{db['card']['number']}\n"

                    f"{db['card']['name']}\n\n"

                    "📸 فیش را ارسال کنید"

                )

                update.message.reply_text(txt)

            except:

                update.message.reply_text(

                    "❌ فقط عدد"

                )

            return

        # =====================================
        # MANUAL CONFIG SEND
        # =====================================

        if step == "manual_send":

            target = state[uid]["target"]

            context.bot.send_message(

                int(target),

                text

            )

            update.message.reply_text(

                "✅ کانفیگ ارسال شد"

            )

            state[uid] = {}

            return
            # =========================================
# VPN SHOP BOT - PRODUCTION VERSION
# PART 12 (FINAL)
# ادامه مستقیم فایل main.py
# =========================================

        # =====================================
        # PIN MESSAGE
        # =====================================

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

            update.message.reply_text(

                f"📌 انجام شد\n\n"

                f"✅ موفق: {success}\n"

                f"❌ ناموفق: {failed}"

            )

            state[uid] = {}

            return

        # =====================================
        # SEND PRIVATE USER ID
        # =====================================

        if step == "send_private_id":

            state[uid] = {

                "step": "send_private_message",

                "target": text

            }

            update.message.reply_text(

                "📨 پیام را ارسال کنید\n"

                "متن / عکس / فایل"

            )

            return

        # =====================================
        # SEND PRIVATE TEXT
        # =====================================

        if step == "send_private_message":

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

                    "❌ خطا"

                )

            state[uid] = {}

            return

        # =====================================
        # BROADCAST TEXT
        # =====================================

        if step == "broadcast_text":

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

            update.message.reply_text(

                f"✅ ارسال شد\n\n"

                f"موفق: {success}\n"

                f"ناموفق: {failed}"

            )

            state[uid] = {}

            return

    except Exception as e:

        logger.error(traceback.format_exc())

# =========================================
# MAIN
# =========================================

def main():

    try:

        logger.info(

            "BOT STARTED"

        )

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

            CallbackQueryHandler(

                admin_callbacks

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

                final_steps

            )

        )

        dp.add_handler(

            MessageHandler(

                Filters.text & ~Filters.command,

                text_handler

            )

        )

        # =====================================
        # START POLLING
        # =====================================

        updater.start_polling(

            drop_pending_updates=True

        )

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

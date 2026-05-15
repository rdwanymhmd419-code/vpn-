# =========================
# FILE: main.py
# =========================

import os
import json
import logging
from datetime import datetime

from telegram import *
from telegram.ext import *

TOKEN = os.getenv("8681405252:AAH7ONTudaE34evtbxWeLdk0dtZc_XkULEA")
ADMIN_ID = int(os.getenv("5993860770"))

DB_FILE = "db.json"

logging.basicConfig(
    level=logging.INFO
)

state = {}

# =========================
# DATABASE
# =========================

def load_db():

    global db

    if not os.path.exists(DB_FILE):

        db = {

            "users": {},

            "categories": [],

            "plans": [],

            "configs": {},

            "test_requests": [],

            "used_test_users": [],

            "texts": {

                "welcome":
                "👋 سلام {name}\n"
                "به فروشگاه VPN خوش آمدید",

                "support":
                "🆘 پشتیبانی:\n@support"

            }

        }

        save_db()

    else:

        with open(
            DB_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            db = json.load(f)

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

load_db()

# =========================
# HELPERS
# =========================

def ensure_user(uid):

    uid = str(uid)

    if uid not in db["users"]:

        db["users"][uid] = {

            "services": []

        }

        save_db()

def is_admin(uid):

    return int(uid) == ADMIN_ID

# =========================
# MENUS
# =========================

def main_menu():

    keyboard = [

        ["🛒 خرید سرویس"],

        ["📦 سرویس های من"],

        ["🎁 تست"],

        ["🆘 پشتیبانی"]

    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

def admin_menu():

    keyboard = [

        ["📁 مدیریت دسته بندی"],

        ["📦 مدیریت پلن ها"],

        ["🔗 افزودن کانفیگ"],

        ["🧪 لیست تست ها"],

        ["👤 حذف محدودیت تست"],

        ["📨 ارسال همگانی"]

    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

# =========================
# START
# =========================

def start(update, context):

    uid = str(
        update.effective_user.id
    )

    ensure_user(uid)

    txt = db["texts"]["welcome"]

    txt = txt.replace(
        "{name}",
        update.effective_user.first_name
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

# =========================
# TEXT HANDLER
# =========================

def text_handler(update, context):

    try:

        uid = str(
            update.effective_user.id
        )

        ensure_user(uid)

        text = update.message.text

        # =====================
        # BUY SERVICE
        # =====================

        if text == "🛒 خرید سرویس":

            if len(db["categories"]) == 0:

                update.message.reply_text(
                    "❌ دسته بندی وجود ندارد"
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

                "📁 دسته بندی را انتخاب کنید",

                reply_markup=
                InlineKeyboardMarkup(
                    keyboard
                )

            )

            return

        # =====================
        # SERVICES
        # =====================

        if text == "📦 سرویس های من":

            services = db["users"][uid]["services"]

            if len(services) == 0:

                update.message.reply_text(
                    "❌ سرویسی ندارید"
                )

                return

            msg = "📦 سرویس های شما\n\n"

            for srv in services:

                msg += (

                    f"📦 {srv['name']}\n\n"

                    f"{srv['config']}\n\n"

                )

            update.message.reply_text(msg)

            return

        # =====================
        # SUPPORT
        # =====================

        if text == "🆘 پشتیبانی":

            update.message.reply_text(
                db["texts"]["support"]
            )

            return

        # =====================
        # TEST
        # =====================

        if text == "🎁 تست":

            if uid in db["used_test_users"]:

                update.message.reply_text(
                    "❌ شما قبلاً تست گرفته اید"
                )

                return

            exists = False

            for t in db["test_requests"]:

                if t["user_id"] == uid:

                    exists = True

            if exists:

                update.message.reply_text(
                    "⏳ درخواست شما ثبت شده"
                )

                return

            db["test_requests"].append({

                "user_id": uid,

                "name":
                update.effective_user.first_name,

                "time":
                str(datetime.now())

            })

            save_db()

            update.message.reply_text(
                "✅ درخواست تست ثبت شد"
            )

            context.bot.send_message(

                ADMIN_ID,

                f"🧪 درخواست تست جدید\n\n"

                f"👤 "
                f"{update.effective_user.first_name}\n"

                f"🆔 {uid}"

            )

            return

        # =====================
        # CATEGORY MENU
        # =====================

        if text == "📁 مدیریت دسته بندی":

            keyboard = [

                ["➕ افزودن دسته"],

                ["🗑 حذف دسته"],

                ["🔙 برگشت"]

            ]

            update.message.reply_text(

                "📁 مدیریت دسته بندی",

                reply_markup=
                ReplyKeyboardMarkup(
                    keyboard,
                    resize_keyboard=True
                )

            )

            return

        # =====================
        # ADD CATEGORY
        # =====================

        if text == "➕ افزودن دسته":

            state[uid] = {

                "step":
                "add_category"

            }

            update.message.reply_text(
                "📁 نام دسته را ارسال کنید"
            )

            return

        # =====================
        # DELETE CATEGORY
        # =====================

        if text == "🗑 حذف دسته":

            keyboard = []

            for cat in db["categories"]:

                keyboard.append([

                    InlineKeyboardButton(

                        cat["name"],

                        callback_data=
                        f"delcat_{cat['id']}"

                    )

                ])

            update.message.reply_text(

                "🗑 انتخاب دسته",

                reply_markup=
                InlineKeyboardMarkup(
                    keyboard
                )

            )

            return

        # =====================
        # PLAN MENU
        # =====================

        if text == "📦 مدیریت پلن ها":

            keyboard = [

                ["➕ افزودن پلن"],

                ["🗑 حذف پلن"],

                ["🔙 برگشت"]

            ]

            update.message.reply_text(

                "📦 مدیریت پلن ها",

                reply_markup=
                ReplyKeyboardMarkup(
                    keyboard,
                    resize_keyboard=True
                )

            )

            return

        # =====================
        # ADD PLAN
        # =====================

        if text == "➕ افزودن پلن":

            keyboard = []

            for cat in db["categories"]:

                keyboard.append([

                    InlineKeyboardButton(

                        cat["name"],

                        callback_data=
                        f"addplan_{cat['id']}"

                    )

                ])

            update.message.reply_text(

                "📁 دسته را انتخاب کنید",

                reply_markup=
                InlineKeyboardMarkup(
                    keyboard
                )

            )

            return

        # =====================
        # DELETE PLAN
        # =====================

        if text == "🗑 حذف پلن":

            keyboard = []

            for plan in db["plans"]:

                keyboard.append([

                    InlineKeyboardButton(

                        plan["name"],

                        callback_data=
                        f"delplan_{plan['id']}"

                    )

                ])

            update.message.reply_text(

                "🗑 انتخاب پلن",

                reply_markup=
                InlineKeyboardMarkup(
                    keyboard
                )

            )

            return

        # =====================
        # ADD CONFIG
        # =====================

        if text == "🔗 افزودن کانفیگ":

            keyboard = []

            for plan in db["plans"]:

                keyboard.append([

                    InlineKeyboardButton(

                        plan["name"],

                        callback_data=
                        f"cfg_{plan['id']}"

                    )

                ])

            update.message.reply_text(

                "📦 انتخاب پلن",

                reply_markup=
                InlineKeyboardMarkup(
                    keyboard
                )

            )

            return

        # =====================
        # TEST LIST
        # =====================

        if text == "🧪 لیست تست ها":

            msg = "🧪 لیست تست ها\n\n"

            if len(db["test_requests"]) == 0:

                msg += "❌ خالی"

            else:

                for i, t in enumerate(

                    db["test_requests"],

                    start=1

                ):

                    msg += (

                        f"{i} - "

                        f"{t['user_id']}\n"

                    )

            keyboard = [

                ["📤 ارسال تست"],

                ["🔙 برگشت"]

            ]

            state[uid] = {

                "step":
                "wait_test_user"

            }

            update.message.reply_text(

                msg,

                reply_markup=
                ReplyKeyboardMarkup(
                    keyboard,
                    resize_keyboard=True
                )

            )

            return

        # =====================
        # SEND TEST
        # =====================

        if text == "📤 ارسال تست":

            state[uid] = {

                "step":
                "test_user"

            }

            update.message.reply_text(
                "🆔 آیدی کاربر را ارسال کنید"
            )

            return

        # =====================
        # REMOVE TEST LIMIT
        # =====================

        if text == "👤 حذف محدودیت تست":

            state[uid] = {

                "step":
                "remove_test"

            }

            update.message.reply_text(
                "🆔 آیدی کاربر را ارسال کنید"
            )

            return

        # =====================
        # BROADCAST
        # =====================

        if text == "📨 ارسال همگانی":

            state[uid] = {

                "step":
                "broadcast"

            }

            update.message.reply_text(
                "📨 پیام را ارسال کنید"
            )

            return

        # =====================
        # BACK
        # =====================

        if text == "🔙 برگشت":

            state[uid] = {}

            if is_admin(uid):

                update.message.reply_text(

                    "🏠 پنل مدیریت",

                    reply_markup=
                    admin_menu()

                )

            else:

                update.message.reply_text(

                    "🏠 منوی اصلی",

                    reply_markup=
                    main_menu()

                )

            return

        # =====================
        # STATES
        # =====================

        if uid in state:

            step = state[uid].get("step")

            # ADD CATEGORY

            if step == "add_category":

                new_id = len(
                    db["categories"]
                ) + 1

                db["categories"].append({

                    "id": new_id,

                    "name": text

                })

                save_db()

                state[uid] = {}

                update.message.reply_text(
                    "✅ دسته اضافه شد"
                )

                return

            # ADD PLAN NAME

            if step == "add_plan_name":

                state[uid]["name"] = text

                state[uid]["step"] = \
                    "add_plan_price"

                update.message.reply_text(
                    "💰 قیمت را ارسال کنید"
                )

                return

            # ADD PLAN PRICE

            if step == "add_plan_price":

                new_id = len(
                    db["plans"]
                ) + 1

                db["plans"].append({

                    "id": new_id,

                    "cat":
                    state[uid]["cat"],

                    "name":
                    state[uid]["name"],

                    "price":
                    int(text)

                })

                save_db()

                state[uid] = {}

                update.message.reply_text(
                    "✅ پلن اضافه شد"
                )

                return

            # CONFIG TEXT

            if step == "config_text":

                plan_id = str(
                    state[uid]["plan"]
                )

                if plan_id not in db["configs"]:

                    db["configs"][plan_id] = []

                lines = text.split("\n")

                for line in lines:

                    line = line.strip()

                    if line:

                        db["configs"][plan_id]\
                            .append(line)

                save_db()

                state[uid] = {}

                update.message.reply_text(
                    "✅ کانفیگ ها ذخیره شدند"
                )

                return

            # TEST USER

            if step == "test_user":

                state[uid] = {

                    "step":
                    "test_config",

                    "target":
                    text

                }

                update.message.reply_text(
                    "🔗 کانفیگ تست را ارسال کنید"
                )

                return

            # SEND TEST CONFIG

            if step == "test_config":

                target = state[uid]["target"]

                context.bot.send_message(

                    int(target),

                    f"🧪 تست شما آماده شد\n\n"

                    f"{text}"

                )

                if target not in \
                    db["used_test_users"]:

                    db["used_test_users"]\
                        .append(target)

                db["test_requests"] = [

                    x for x in
                    db["test_requests"]

                    if x["user_id"] != target

                ]

                save_db()

                state[uid] = {}

                update.message.reply_text(
                    "✅ تست ارسال شد"
                )

                return

            # REMOVE TEST

            if step == "remove_test":

                if text in \
                    db["used_test_users"]:

                    db["used_test_users"]\
                        .remove(text)

                    save_db()

                    update.message.reply_text(
                        "✅ حذف شد"
                    )

                else:

                    update.message.reply_text(
                        "❌ پیدا نشد"
                    )

                state[uid] = {}

                return

            # BROADCAST

            if step == "broadcast":

                for user_id in db["users"]:

                    try:

                        context.bot.send_message(

                            int(user_id),

                            text

                        )

                    except:

                        pass

                state[uid] = {}

                update.message.reply_text(
                    "✅ ارسال شد"
                )

                return

    except Exception as e:

        logging.error(str(e))

# =========================
# CALLBACK
# =========================

def callback_handler(update, context):

    query = update.callback_query

    query.answer()

    uid = str(
        query.from_user.id
    )

    data = query.data

    # SHOW PLANS

    if data.startswith("cat_"):

        cat_id = int(
            data.split("_")[1]
        )

        keyboard = []

        for plan in db["plans"]:

            if plan["cat"] == cat_id:

                keyboard.append([

                    InlineKeyboardButton(

                        f"{plan['name']} | "
                        f"{plan['price']}",

                        callback_data=
                        f"buy_{plan['id']}"

                    )

                ])

        query.message.reply_text(

            "📦 پلن را انتخاب کنید",

            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )

        )

    # BUY

    elif data.startswith("buy_"):

        plan_id = int(
            data.split("_")[1]
        )

        plan = None

        for p in db["plans"]:

            if p["id"] == plan_id:

                plan = p

                break

        if not plan:

            return

        configs = db["configs"].get(
            str(plan_id),
            []
        )

        if len(configs) == 0:

            query.message.reply_text(
                "❌ کانفیگ موجود نیست"
            )

            return

        config = configs.pop(0)

        db["configs"][
            str(plan_id)
        ] = configs

        db["users"][uid]["services"]\
            .append({

                "name":
                plan["name"],

                "config":
                config

            })

        save_db()

        query.message.reply_text(

            "✅ خرید انجام شد\n\n"

            f"{config}"

        )

    # ADD PLAN

    elif data.startswith("addplan_"):

        cat_id = int(
            data.split("_")[1]
        )

        state[uid] = {

            "step":
            "add_plan_name",

            "cat":
            cat_id

        }

        query.message.reply_text(
            "📦 نام پلن را ارسال کنید"
        )

    # DELETE CATEGORY

    elif data.startswith("delcat_"):

        cat_id = int(
            data.split("_")[1]
        )

        db["categories"] = [

            x for x in
            db["categories"]

            if x["id"] != cat_id

        ]

        save_db()

        query.message.reply_text(
            "✅ حذف شد"
        )

    # DELETE PLAN

    elif data.startswith("delplan_"):

        plan_id = int(
            data.split("_")[1]
        )

        db["plans"] = [

            x for x in
            db["plans"]

            if x["id"] != plan_id

        ]

        save_db()

        query.message.reply_text(
            "✅ حذف شد"
        )

    # CONFIG

    elif data.startswith("cfg_"):

        plan_id = int(
            data.split("_")[1]
        )

        state[uid

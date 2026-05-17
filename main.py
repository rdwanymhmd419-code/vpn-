# main.py

import json
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

# =========================
# CONFIG
# =========================

TOKEN = "8681405252:AAH7ONTudaE34evtbxWeLdk0dtZc_XkULEA"

ADMIN_ID = 5993860770

DB_FILE = "db.json"

# =========================
# DATABASE
# =========================

def load_db():

    if not os.path.exists(DB_FILE):

        data = {

            "categories": [],

            "plans": [],

            "support": "@support"

        }

        save_db(data)

        return data

    with open(DB_FILE, "r", encoding="utf-8") as f:

        return json.load(f)

def save_db(data):

    with open(DB_FILE, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )

db = load_db()

# =========================
# STATES
# =========================

user_state = {}

# =========================
# HELPERS
# =========================

def is_admin(user_id):

    return int(user_id) == ADMIN_ID

def main_menu():

    keyboard = [

        [

            InlineKeyboardButton(
                "🟢 خرید سرویس",
                callback_data="buy"
            )

        ],

        [

            InlineKeyboardButton(
                "🔴 پشتیبانی",
                callback_data="support"
            )

        ],

        [

            InlineKeyboardButton(
                "🔵 تست",
                callback_data="test"
            )

        ],

        [

            InlineKeyboardButton(
                "👤 حساب من",
                callback_data="account"
            )

        ]

    ]

    return InlineKeyboardMarkup(keyboard)

def admin_menu():

    keyboard = [

        [

            InlineKeyboardButton(
                "📁 افزودن دسته بندی",
                callback_data="add_category"
            )

        ],

        [

            InlineKeyboardButton(
                "🗑 حذف دسته بندی",
                callback_data="delete_category"
            )

        ],

        [

            InlineKeyboardButton(
                "📦 افزودن پلن",
                callback_data="add_plan"
            )

        ],

        [

            InlineKeyboardButton(
                "🗑 حذف پلن",
                callback_data="delete_plan"
            )

        ]

    ]

    return InlineKeyboardMarkup(keyboard)

# =========================
# START
# =========================

def start(update: Update, context: CallbackContext):

    user_id = update.effective_user.id

    if is_admin(user_id):

        update.message.reply_text(

            "👑 پنل مدیریت",

            reply_markup=admin_menu()

        )

    else:

        update.message.reply_text(

            "🏠 خوش آمدید",

            reply_markup=main_menu()

        )

# =========================
# CALLBACKS
# =========================

def callbacks(update: Update, context: CallbackContext):

    query = update.callback_query

    query.answer()

    data = query.data

    user_id = query.from_user.id

    # =========================
    # BUY
    # =========================

    if data == "buy":

        if len(db["categories"]) == 0:

            query.message.reply_text(
                "❌ دسته بندی وجود ندارد"
            )

            return

        keyboard = []

        for category in db["categories"]:

            keyboard.append([

                InlineKeyboardButton(

                    category["name"],

                    callback_data=
                    f"cat_{category['id']}"

                )

            ])

        query.message.reply_text(

            "📁 دسته بندی را انتخاب کنید",

            reply_markup=
            InlineKeyboardMarkup(keyboard)

        )

    # =========================
    # SUPPORT
    # =========================

    elif data == "support":

        query.message.reply_text(

            f"🆘 پشتیبانی:\n{db['support']}"

        )

    # =========================
    # TEST
    # =========================

    elif data == "test":

        query.message.reply_text(

            "✅ درخواست تست ثبت شد"

        )

    # =========================
    # ACCOUNT
    # =========================

    elif data == "account":

        query.message.reply_text(

            f"👤 آیدی شما:\n{user_id}"

        )

    # =========================
    # CATEGORY SHOW
    # =========================

    elif data.startswith("cat_"):

        category_id = int(
            data.split("_")[1]
        )

        keyboard = []

        found = False

        for plan in db["plans"]:

            if plan["category_id"] == category_id:

                found = True

                keyboard.append([

                    InlineKeyboardButton(

                        f"{plan['name']} | {plan['price']} تومان",

                        callback_data=
                        f"buyplan_{plan['id']}"

                    )

                ])

        if not found:

            query.message.reply_text(
                "❌ پلنی وجود ندارد"
            )

            return

        query.message.reply_text(

            "📦 پلن را انتخاب کنید",

            reply_markup=
            InlineKeyboardMarkup(keyboard)

        )

    # =========================
    # BUY PLAN
    # =========================

    elif data.startswith("buyplan_"):

        plan_id = int(
            data.split("_")[1]
        )

        selected_plan = None

        for plan in db["plans"]:

            if plan["id"] == plan_id:

                selected_plan = plan

                break

        if selected_plan is None:

            query.message.reply_text(
                "❌ پلن پیدا نشد"
            )

            return

        query.message.reply_text(

            f"✅ سفارش ثبت شد\n\n"

            f"📦 {selected_plan['name']}\n"

            f"💰 {selected_plan['price']} تومان\n\n"

            f"کانفیگ توسط ادمین ارسال می‌شود"

        )

    # =========================
    # ADD CATEGORY
    # =========================

    elif data == "add_category":

        user_state[user_id] = "add_category"

        query.message.reply_text(

            "📁 نام دسته بندی را ارسال کنید"

        )

    # =========================
    # DELETE CATEGORY
    # =========================

    elif data == "delete_category":

        if len(db["categories"]) == 0:

            query.message.reply_text(
                "❌ دسته بندی وجود ندارد"
            )

            return

        keyboard = []

        for category in db["categories"]:

            keyboard.append([

                InlineKeyboardButton(

                    category["name"],

                    callback_data=
                    f"delcat_{category['id']}"

                )

            ])

        query.message.reply_text(

            "🗑 انتخاب دسته بندی",

            reply_markup=
            InlineKeyboardMarkup(keyboard)

        )

    # =========================
    # DELETE CATEGORY ACTION
    # =========================

    elif data.startswith("delcat_"):

        category_id = int(
            data.split("_")[1]
        )

        db["categories"] = [

            x for x in db["categories"]

            if x["id"] != category_id

        ]

        save_db(db)

        query.message.reply_text(
            "✅ حذف شد"
        )

    # =========================
    # ADD PLAN
    # =========================

    elif data == "add_plan":

        if len(db["categories"]) == 0:

            query.message.reply_text(
                "❌ ابتدا دسته بندی بسازید"
            )

            return

        keyboard = []

        for category in db["categories"]:

            keyboard.append([

                InlineKeyboardButton(

                    category["name"],

                    callback_data=
                    f"selectcat_{category['id']}"

                )

            ])

        query.message.reply_text(

            "📁 دسته بندی پلن را انتخاب کنید",

            reply_markup=
            InlineKeyboardMarkup(keyboard)

        )

    # =========================
    # SELECT CATEGORY FOR PLAN
    # =========================

    elif data.startswith("selectcat_"):

        category_id = int(
            data.split("_")[1]
        )

        user_state[user_id] = {

            "step": "plan_name",

            "category_id": category_id

        }

        query.message.reply_text(

            "📦 نام پلن را ارسال کنید"

        )

    # =========================
    # DELETE PLAN
    # =========================

    elif data == "delete_plan":

        if len(db["plans"]) == 0:

            query.message.reply_text(
                "❌ پلنی وجود ندارد"
            )

            return

        keyboard = []

        for plan in db["plans"]:

            keyboard.append([

                InlineKeyboardButton(

                    plan["name"],

                    callback_data=
                    f"delplan_{plan['id']}"

                )

            ])

        query.message.reply_text(

            "🗑 انتخاب پلن",

            reply_markup=
            InlineKeyboardMarkup(keyboard)

        )

    # =========================
    # DELETE PLAN ACTION
    # =========================

    elif data.startswith("delplan_"):

        plan_id = int(
            data.split("_")[1]
        )

        db["plans"] = [

            x for x in db["plans"]

            if x["id"] != plan_id

        ]

        save_db(db)

        query.message.reply_text(
            "✅ پلن حذف شد"
        )

# =========================
# TEXTS
# =========================

def texts(update: Update, context: CallbackContext):

    user_id = update.effective_user.id

    text = update.message.text

    if user_id not in user_state:

        return

    state = user_state[user_id]

    # =========================
    # ADD CATEGORY
    # =========================

    if state == "add_category":

        new_id = len(db["categories"]) + 1

        db["categories"].append({

            "id": new_id,

            "name": text

        })

        save_db(db)

        del user_state[user_id]

        update.message.reply_text(
            "✅ دسته بندی اضافه شد"
        )

    # =========================
    # ADD PLAN
    # =========================

    elif isinstance(state, dict):

        if state["step"] == "plan_name":

            state["name"] = text

            state["step"] = "plan_price"

            user_state[user_id] = state

            update.message.reply_text(

                "💰 قیمت پلن را ارسال کنید"

            )

        elif state["step"] == "plan_price":

            new_id = len(db["plans"]) + 1

            db["plans"].append({

                "id": new_id,

                "name": state["name"],

                "price": text,

                "category_id":
                state["category_id"]

            })

            save_db(db)

            del user_state[user_id]

            update.message.reply_text(
                "✅ پلن اضافه شد"
            )

# =========================
# MAIN
# =========================

def main():

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
            callbacks
        )
    )

    dp.add_handler(
        MessageHandler(
            Filters.text &
            ~Filters.command,
            texts
        )
    )

    updater.start_polling()

    print("BOT STARTED")

    updater.idle()

if __name__ == "__main__":

    main()

# main.py
import os
import json
import logging
from datetime import datetime
from threading import Thread
from flask import Flask

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from telegram.error import TelegramError

# ==================== تنظیمات ====================
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask for keeping alive
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "✅ VPN Bot is Running!", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==================== توکن و تنظیمات ====================
TOKEN = '8681405252:AAH7ONTudaE34evtbxWeLdk0dtZc_XkULEA'
ADMIN_ID = 5993860770
ADMINS = {str(ADMIN_ID): "مالک"}

DB_FILE = 'data.json'

# ==================== دیتابیس پیش فرض ====================
DEFAULT_DATA = {
    "users": {},
    "brand": "تک نت وی‌پی‌ان",
    "card": {"number": "6277601368776066", "name": "محمد رضوانی"},
    "support": "@Support_Admin",
    "guide": "@Guide_Channel",
    "bot_status": {"enabled": True, "message": "ربات موقتاً غیرفعال است"},
    "test_mode": {"enabled": True, "reason": "تست رایگان غیرفعال شده است"},
    "auto_send": True,
    "categories": {
        "🚀 قوی": [
            {"id": 1, "name": "⚡️ پلن قوی 20GB", "price": 80000, "volume": "20GB", "days": 30, "users": 1},
            {"id": 2, "name": "🔥 پلن قوی 50GB", "price": 140000, "volume": "50GB", "days": 30, "users": 1}
        ],
        "💎 ارزان": [
            {"id": 3, "name": "💎 پلن اقتصادی 10GB", "price": 45000, "volume": "10GB", "days": 30, "users": 1},
            {"id": 4, "name": "💎 پلن اقتصادی 20GB", "price": 75000, "volume": "20GB", "days": 30, "users": 1}
        ]
    },
    "configs": {},
    "force_join": {"enabled": False, "link": "", "username": "", "channel_id": ""},
    "texts": {
        "welcome": "🔰 به {brand} خوش آمدید\n\n✅ فروش ویژه فیلترشکن\n✅ پشتیبانی 24 ساعته",
        "support": "🆘 پشتیبانی: {support}",
        "guide": "📚 آموزش: {guide}",
        "test": "🎁 درخواست تست شما ثبت شد",
        "force": "🔒 برای استفاده از ربات در کانال زیر عضو شوید:\n{link}\n\nسپس دکمه ✅ را بزنید.",
        "invite": "🤝 لینک دعوت شما:\n{link}\n\nبه ازای هر دعوت 1 روز هدیه",
        "receipt_sent": "✅ فیش شما ارسال شد، پس از تایید سرویس فعال می‌شود",
        "waiting": "⏳ درخواست شما ثبت شد، به زودی کانفیگ ارسال می‌شود",
        "config_sent": "🎉 سرویس شما آماده شد\n━━━━━━━━━━━━━━━━\n📦 {plan}\n📅 {date}\n👤 {account}\n━━━━━━━━━━━━━━━━\n🔗 {config}\n━━━━━━━━━━━━━━━━\n📚 {guide}",
        "rejected": "❌ فیش شما رد شد\nدلیل: {reason}"
    }
}

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # اطمینان از وجود تمام کلیدها
            for key in DEFAULT_DATA:
                if key not in data:
                    data[key] = DEFAULT_DATA[key]
            logger.info("✅ Database loaded")
            return data
        except Exception as e:
            logger.error(f"Load error: {e}")
    logger.info("📁 Creating new database")
    return DEFAULT_DATA.copy()

def save_db():
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Save error: {e}")
        return False

db = load_db()
user_data = {}

# ==================== منوهای رنگی ====================
def main_menu(uid):
    keyboard = [
        ['💰 خرید', '🎁 تست'],
        ['💳 کیف پول', '📂 سرویس‌ها'],
        ['👤 پشتیبانی', '📚 آموزش'],
        ['🤝 دعوت دوستان']
    ]
    if str(uid) in ADMINS:
        keyboard.append(['⚙️ مدیریت'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_menu():
    keyboard = [
        ['➕ افزودن پلن', '✏️ ویرایش پلن', '➖ حذف پلن'],
        ['📁 دسته جدید', '🗑 حذف دسته'],
        ['➕ افزودن ادمین', '➖ حذف ادمین'],
        ['🎁 مدیریت تست', '🤖 ارسال خودکار'],
        ['🔒 عضویت اجباری', '💳 ویرایش کارت'],
        ['📝 ویرایش متن‌ها', '🏷 ویرایش برند'],
        ['👤 پشتیبانی', '📚 آموزش'],
        ['➕ افزودن کانفیگ', '📊 آمار'],
        ['📨 ارسال همگانی', '📨 ارسال تست همگانی'],
        ['🗑 پاکسازی تست‌ها', '📤 بکاپ'],
        ['⚡ وضعیت ربات', '🔙 برگشت']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def back_button():
    return ReplyKeyboardMarkup([['🔙 برگشت']], resize_keyboard=True)

# ==================== بررسی عضویت ====================
def check_join(user_id, bot):
    if not db["force_join"]["enabled"]:
        return True
    channel = db["force_join"].get("username", "")
    if not channel:
        return True
    try:
        member = bot.get_chat_member(chat_id=channel, user_id=int(user_id))
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ==================== ثبت لاگ ====================
def add_log(action, user_id, detail):
    if "logs" not in db:
        db["logs"] = []
    db["logs"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "user_id": user_id,
        "detail": detail
    })
    if len(db["logs"]) > 500:
        db["logs"] = db["logs"][-500:]
    save_db()

# ==================== ارسال کانفیگ از استخر ====================
def send_config_from_pool(user_id, plan_id, account_name, plan_name, bot):
    configs = db["configs"].get(str(plan_id), [])
    if configs:
        config = configs.pop(0)
        db["configs"][str(plan_id)] = configs
        save_db()
        
        msg = db["texts"]["config_sent"].format(
            plan=plan_name,
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            account=account_name,
            config=config,
            guide=db["guide"]
        )
        try:
            bot.send_message(int(user_id), msg)
            add_log("config_sent", user_id, f"ارسال کانفیگ {plan_name}")
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False
    else:
        # اطلاع به ادمین برای افزودن کانفیگ
        bot.send_message(ADMIN_ID, f"⚠️ کانفیگ {plan_name} تمام شد!\nکاربر: {user_id}\nلطفاً کانفیگ جدید اضافه کنید")
        add_log("need_config", user_id, f"نیاز به کانفیگ {plan_name}")
        return False

# ==================== دستور استارت ====================
def start(update: Update, context):
    uid = str(update.effective_user.id)
    
    if uid not in db["users"]:
        db["users"][uid] = {
            "name": update.effective_user.first_name or "کاربر",
            "username": update.effective_user.username,
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "wallet": 0,
            "purchases": [],
            "tests": [],
            "test_count": 0,
            "invite_count": 0
        }
        save_db()
        add_log("register", uid, "ثبت نام جدید")
    
    user_data[uid] = {}
    
    # عضویت اجباری
    if db["force_join"]["enabled"] and db["force_join"]["link"]:
        if not check_join(uid, context.bot):
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 عضویت در کانال", url=db["force_join"]["link"]),
                InlineKeyboardButton("✅ تایید عضویت", callback_data="check_join")
            ]])
            msg = db["texts"]["force"].format(link=db["force_join"]["link"])
            update.message.reply_text(msg, reply_markup=btn)
            return
    
    welcome = db["texts"]["welcome"].format(brand=db["brand"])
    update.message.reply_text(welcome, reply_markup=main_menu(uid))

# ==================== کیف پول ====================
def wallet_menu(update: Update):
    uid = str(update.effective_user.id)
    wallet = db["users"][uid].get("wallet", 0)
    keyboard = [
        [InlineKeyboardButton("💰 100,000 تومان", callback_data="charge_100000")],
        [InlineKeyboardButton("💰 300,000 تومان", callback_data="charge_300000")],
        [InlineKeyboardButton("💰 500,000 تومان", callback_data="charge_500000")],
        [InlineKeyboardButton("💰 1,000,000 تومان", callback_data="charge_1000000")],
        [InlineKeyboardButton("💰 2,000,000 تومان", callback_data="charge_2000000")],
        [InlineKeyboardButton("✏️ مبلغ دلخواه", callback_data="charge_custom")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back")]
    ]
    update.message.reply_text(
        f"💳 موجودی کیف پول شما:\n━━━━━━━━━━━━━━━━\n💰 {wallet:,} تومان\n━━━━━━━━━━━━━━━━\nمبلغ مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==================== خرید ====================
def show_categories(update: Update):
    cats = list(db["categories"].keys())
    keyboard = [[cat] for cat in cats] + [['🔙 برگشت']]
    update.message.reply_text("📦 دسته مورد نظر را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

def show_plans(update: Update, category):
    plans = db["categories"][category]
    keyboard = []
    for p in plans:
        keyboard.append([InlineKeyboardButton(f"{p['name']} - {p['price']:,} تومان", callback_data=f"plan_{p['id']}")])
    update.message.reply_text(f"📦 {category}\n━━━━━━━━━━━━━━━━\nپلن مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

def payment_methods(update: Update, plan):
    uid = str(update.effective_user.id)
    user_data[uid]["temp_plan"] = plan
    
    keyboard = [
        [InlineKeyboardButton("💳 پرداخت با کارت", callback_data=f"pay_card_{plan['id']}")],
        [InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data=f"pay_wallet_{plan['id']}")],
        [InlineKeyboardButton("⚡ خرید ترکیبی", callback_data=f"pay_mix_{plan['id']}")],
        [InlineKeyboardButton("🔙 انصراف", callback_data="back")]
    ]
    update.message.reply_text(
        f"💰 {plan['name']}\n━━━━━━━━━━━━━━━━\n💵 قیمت: {plan['price']:,} تومان\n━━━━━━━━━━━━━━━━\nروش پرداخت را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def ask_account_name(update: Update, plan, method):
    uid = str(update.effective_user.id)
    user_data[uid]["temp_purchase"] = {"plan": plan, "method": method}
    update.message.reply_text("📝 لطفاً نام اکانت خود را وارد کنید:", reply_markup=back_button())
    user_data[uid]["step"] = "waiting_account_name"

def process_payment(update: Update, plan, account_name, method):
    uid = str(update.effective_user.id)
    wallet = db["users"][uid].get("wallet", 0)
    
    if method == "wallet":
        if wallet >= plan["price"]:
            db["users"][uid]["wallet"] = wallet - plan["price"]
            save_db()
            update.message.reply_text(f"✅ مبلغ {plan['price']:,} تومان از کیف پول شما کسر شد\n💰 موجودی جدید: {db['users'][uid]['wallet']:,} تومان")
            add_log("purchase_wallet", uid, f"خرید {plan['name']} با کیف پول")
            
            if db["auto_send"]:
                send_config_from_pool(uid, plan["id"], account_name, plan["name"], update.context.bot)
            else:
                update.message.reply_text(db["texts"]["waiting"])
                update.context.bot.send_message(ADMIN_ID, f"⚠️ کاربر {uid} در انتظار کانفیگ دستی\nپلن: {plan['name']}\nاکانت: {account_name}")
            return True
        else:
            update.message.reply_text(f"❌ موجودی کیف پول شما کافی نیست\n💰 موجودی: {wallet:,} تومان\n💵 نیاز: {plan['price'] - wallet:,} تومان اضافی")
            return False
    
    elif method == "card":
        msg = (
            f"🧾 پیش فاکتور خرید\n━━━━━━━━━━━━━━━━\n"
            f"📦 پلن: {plan['name']}\n"
            f"💰 مبلغ: {plan['price']:,} تومان\n"
            f"👤 نام اکانت: {account_name}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💳 شماره کارت:\n{db['card']['number']}\n"
            f"👤 {db['card']['name']}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"پس از واریز، عکس فیش را بفرستید"
        )
        user_data[uid]["pending_receipt"] = {"plan": plan, "account": account_name, "method": "card"}
        user_data[uid]["step"] = "waiting_receipt"
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="send_receipt")]])
        update.message.reply_text(msg, reply_markup=btn)
        return True
    
    elif method == "mix":
        used = min(wallet, plan["price"])
        remaining = plan["price"] - used
        if used > 0:
            db["users"][uid]["wallet"] = wallet - used
            save_db()
        
        msg = (
            f"🧾 پیش فاکتور خرید (ترکیبی)\n━━━━━━━━━━━━━━━━\n"
            f"📦 پلن: {plan['name']}\n"
            f"💰 کل مبلغ: {plan['price']:,} تومان\n"
            f"✅ از کیف پول: {used:,} تومان\n"
            f"💵 باقیمانده: {remaining:,} تومان\n"
            f"👤 نام اکانت: {account_name}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💳 شماره کارت:\n{db['card']['number']}\n"
            f"👤 {db['card']['name']}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"مبلغ {remaining:,} تومان را واریز کنید و فیش را بفرستید"
        )
        user_data[uid]["pending_receipt"] = {"plan": plan, "account": account_name, "method": "mix", "used_wallet": used}
        user_data[uid]["step"] = "waiting_receipt"
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="send_receipt")]])
        update.message.reply_text(msg, reply_markup=btn)
        return True
    
    return False

# ==================== هندلر اصلی پیام‌ها ====================
def handle_message(update: Update, context):
    try:
        uid = str(update.effective_user.id)
        text = update.message.text
        
        # بررسی وضعیت ربات
        if not db["bot_status"]["enabled"] and uid not in ADMINS:
            update.message.reply_text(db["bot_status"]["message"])
            return
        
        # بررسی عضویت
        if db["force_join"]["enabled"] and db["force_join"]["link"]:
            if not check_join(uid, context.bot) and text != '/start':
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 عضویت در کانال", url=db["force_join"]["link"]),
                    InlineKeyboardButton("✅ تایید عضویت", callback_data="check_join")
                ]])
                update.message.reply_text(db["texts"]["force"].format(link=db["force_join"]["link"]), reply_markup=btn)
                return
        
        # ========== منوی اصلی ==========
        if text == '🔙 برگشت':
            user_data[uid] = {}
            start(update, context)
            return
        
        if text == '💰 خرید':
            show_categories(update)
            return
        
        if text == '🎁 تست':
            if not db["test_mode"]["enabled"]:
                update.message.reply_text(f"❌ {db['test_mode']['reason']}")
                return
            if db["users"][uid]["test_count"] >= 1:
                update.message.reply_text("❌ شما قبلاً تست گرفته‌اید")
                return
            
            db["users"][uid]["test_count"] += 1
            db["users"][uid]["tests"].append(datetime.now().strftime("%Y-%m-%d %H:%M"))
            save_db()
            update.message.reply_text(db["texts"]["test"])
            add_log("test", uid, "درخواست تست")
            
            # اطلاع به ادمین
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال تست", callback_data=f"send_test_{uid}")]])
            context.bot.send_message(ADMIN_ID, f"🎁 درخواست تست\n👤 {db['users'][uid]['name']}\n🆔 {uid}", reply_markup=btn)
            return
        
        if text == '💳 کیف پول':
            wallet_menu(update)
            return
        
        if text == '📂 سرویس‌ها':
            purchases = db["users"][uid].get("purchases", [])
            tests = db["users"][uid].get("tests", [])
            msg = "📂 سرویس‌های شما:\n━━━━━━━━━━━━━━━━\n"
            if purchases:
                msg += "✅ خریدها:\n"
                for i, p in enumerate(purchases[-10:], 1):
                    msg += f"{i}. {p}\n"
            else:
                msg += "❌ خریدی ندارید\n"
            if tests:
                msg += f"\n🎁 تست‌ها:\n"
                for i, t in enumerate(tests[-5:], 1):
                    msg += f"{i}. {t}\n"
            update.message.reply_text(msg)
            return
        
        if text == '👤 پشتیبانی':
            update.message.reply_text(db["texts"]["support"].format(support=db["support"]))
            return
        
        if text == '📚 آموزش':
            update.message.reply_text(db["texts"]["guide"].format(guide=db["guide"]))
            return
        
        if text == '🤝 دعوت دوستان':
            bot_username = context.bot.get_me().username
            link = f"https://t.me/{bot_username}?start={uid}"
            invites = db["users"][uid].get("invite_count", 0)
            msg = db["texts"]["invite"].format(link=link)
            msg += f"\n━━━━━━━━━━━━━━━━\n👥 تعداد دعوت: {invites}\n🎁 هر دعوت = 1 روز هدیه"
            update.message.reply_text(msg)
            return
        
        # ========== نمایش دسته و پلن ==========
        if text in db["categories"]:
            show_plans(update, text)
            return
        
        # ========== منتظر نام اکانت ==========
        if user_data.get(uid, {}).get("step") == "waiting_account_name":
            account_name = text
            temp = user_data[uid].get("temp_purchase", {})
            if temp:
                process_payment(update, temp["plan"], account_name, temp["method"])
                user_data[uid] = {}
            return
        
        # ========== منتظر فیش ==========
        if user_data.get(uid, {}).get("step") == "waiting_receipt":
            update.message.reply_text("📸 لطفاً عکس فیش را ارسال کنید")
            return
        
        # ========== مدیریت ادمین ==========
        if uid in ADMINS:
            # مدیریت پلن
            if text == '➕ افزودن پلن':
                user_data[uid] = {"step": "add_plan_cat"}
                cats = list(db["categories"].keys())
                kb = [[c] for c in cats] + [['➕ دسته جدید'], ['🔙 برگشت']]
                update.message.reply_text("دسته را انتخاب کنید یا دسته جدید بسازید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                return
            
            if text == '✏️ ویرایش پلن':
                keyboard = []
                for cat, plans in db["categories"].items():
                    for p in plans:
                        keyboard.append([InlineKeyboardButton(f"✏️ {cat} - {p['name']}", callback_data=f"edit_plan_{p['id']}")])
                update.message.reply_text("پلن را برای ویرایش انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if text == '➖ حذف پلن':
                keyboard = []
                for cat, plans in db["categories"].items():
                    for p in plans:
                        keyboard.append([InlineKeyboardButton(f"❌ {cat} - {p['name']}", callback_data=f"del_plan_{p['id']}")])
                update.message.reply_text("پلن را برای حذف انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if text == '📁 دسته جدید':
                user_data[uid] = {"step": "add_category"}
                update.message.reply_text("نام دسته جدید را وارد کنید:", reply_markup=back_button())
                return
            
            if text == '🗑 حذف دسته':
                cats = list(db["categories"].keys())
                kb = [[c] for c in cats] + [['🔙 برگشت']]
                user_data[uid] = {"step": "del_category"}
                update.message.reply_text("دسته را برای حذف انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                return
            
            # مدیریت ادمین
            if text == '➕ افزودن ادمین':
                user_data[uid] = {"step": "add_admin"}
                update.message.reply_text("🆔 آیدی عددی ادمین جدید را بفرستید:", reply_markup=back_button())
                return
            
            if text == '➖ حذف ادمین':
                user_data[uid] = {"step": "del_admin"}
                update.message.reply_text("🆔 آیدی ادمین را برای حذف بفرستید:", reply_markup=back_button())
                return
            
            # مدیریت تست
            if text == '🎁 مدیریت تست':
                status = "✅ فعال" if db["test_mode"]["enabled"] else "❌ غیرفعال"
                keyboard = [['✅ فعال کردن تست', '❌ غیرفعال کردن تست'], ['✏️ ویرایش پیام غیرفعال'], ['🔙 برگشت']]
                update.message.reply_text(f"🎁 وضعیت تست رایگان:\n{status}\n\nپیام غیرفعال: {db['test_mode']['reason']}", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
                return
            
            if text == '✅ فعال کردن تست':
                db["test_mode"]["enabled"] = True
                save_db()
                update.message.reply_text("✅ تست رایگان فعال شد", reply_markup=admin_menu())
                return
            
            if text == '❌ غیرفعال کردن تست':
                db["test_mode"]["enabled"] = False
                save_db()
                update.message.reply_text("✅ تست رایگان غیرفعال شد", reply_markup=admin_menu())
                return
            
            if text == '✏️ ویرایش پیام غیرفعال':
                user_data[uid] = {"step": "edit_test_reason"}
                update.message.reply_text("متن جدید پیام غیرفعال بودن تست را بفرستید:", reply_markup=back_button())
                return
            
            # ارسال خودکار
            if text == '🤖 ارسال خودکار':
                status = "✅ روشن" if db["auto_send"] else "❌ خاموش"
                keyboard = [['✅ روشن کردن', '❌ خاموش کردن'], ['🔙 برگشت']]
                update.message.reply_text(f"🤖 وضعیت ارسال خودکار کانفیگ:\n{status}", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
                return
            
            if text == '✅ روشن کردن':
                db["auto_send"] = True
                save_db()
                update.message.reply_text("✅ ارسال خودکار کانفیگ روشن شد", reply_markup=admin_menu())
                return
            
            if text == '❌ خاموش کردن':
                db["auto_send"] = False
                save_db()
                update.message.reply_text("✅ ارسال خودکار کانفیگ خاموش شد", reply_markup=admin_menu())
                return
            
            # عضویت اجباری
            if text == '🔒 عضویت اجباری':
                status = "✅ فعال" if db["force_join"]["enabled"] else "❌ غیرفعال"
                keyboard = [['✅ فعال', '❌ غیرفعال'], ['🔗 تنظیم لینک'], ['🔙 برگشت']]
                update.message.reply_text(f"🔒 وضعیت عضویت اجباری:\n{status}\nلینک: {db['force_join']['link'] or 'تنظیم نشده'}", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
                return
            
            if text == '✅ فعال':
                if db["force_join"]["link"]:
                    db["force_join"]["enabled"] = True
                    save_db()
                    update.message.reply_text("✅ عضویت اجباری فعال شد", reply_markup=admin_menu())
                else:
                    update.message.reply_text("❌ ابتدا لینک کانال را تنظیم کنید")
                return
            
            if text == '❌ غیرفعال':
                db["force_join"]["enabled"] = False
                save_db()
                update.message.reply_text("✅ عضویت اجباری غیرفعال شد", reply_markup=admin_menu())
                return
            
            if text == '🔗 تنظیم لینک':
                user_data[uid] = {"step": "set_force_link"}
                update.message.reply_text("🔗 لینک کانال را بفرستید:\nمثال: https://t.me/mychannel", reply_markup=back_button())
                return
            
            # ویرایش کارت
            if text == '💳 ویرایش کارت':
                keyboard = [['شماره کارت', 'نام صاحب کارت'], ['🔙 برگشت']]
                current = f"شماره: {db['card']['number']}\nنام: {db['card']['name']}"
                update.message.reply_text(current, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
                return
            
            if text == 'شماره کارت':
                user_data[uid] = {"step": "edit_card_number"}
                update.message.reply_text("شماره کارت 16 رقمی را بفرستید:", reply_markup=back_button())
                return
            
            if text == 'نام صاحب کارت':
                user_data[uid] = {"step": "edit_card_name"}
                update.message.reply_text("نام صاحب کارت را بفرستید:", reply_markup=back_button())
                return
            
            # ویرایش متن‌ها
            if text == '📝 ویرایش متن‌ها':
                keyboard = [
                    ['خوش‌آمدگویی', 'پشتیبانی', 'آموزش'],
                    ['تست رایگان', 'عضویت اجباری', 'دعوت دوستان'],
                    ['پیام فیش', 'پیام کانفیگ', 'رد فیش'],
                    ['پیام انتظار', '🔙 برگشت']
                ]
                update.message.reply_text("📝 کدام متن را ویرایش کنیم؟", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
                return
            
            text_map = {
                'خوش‌آمدگویی': 'welcome', 'پشتیبانی': 'support', 'آموزش': 'guide',
                'تست رایگان': 'test', 'عضویت اجباری': 'force', 'دعوت دوستان': 'invite',
                'پیام فیش': 'receipt_sent', 'پیام کانفیگ': 'config_sent', 'رد فیش': 'rejected',
                'پیام انتظار': 'waiting'
            }
            if text in text_map:
                user_data[uid] = {"step": f"edit_text_{text_map[text]}"}
                current = db["texts"][text_map[text]]
                update.message.reply_text(f"متن فعلی:\n{current}\n\nمتن جدید را بفرستید:", reply_markup=back_button())
                return
            
            # ویرایش برند
            if text == '🏷 ویرایش برند':
                user_data[uid] = {"step": "edit_brand"}
                update.message.reply_text(f"برند فعلی: {db['brand']}\nبرند جدید را بفرستید:", reply_markup=back_button())
                return
            
            if text == '👤 پشتیبانی':
                user_data[uid] = {"step": "edit_support"}
                update.message.reply_text(f"پشتیبان فعلی: {db['support']}\nآیدی جدید پشتیبان را بفرستید:", reply_markup=back_button())
                return
            
            if text == '📚 آموزش':
                user_data[uid] = {"step": "edit_guide"}
                update.message.reply_text(f"کانال آموزش فعلی: {db['guide']}\nآیدی جدید کانال آموزش را بفرستید:", reply_markup=back_button())
                return
            
            # افزودن کانفیگ
            if text == '➕ افزودن کانفیگ':
                keyboard = []
                for cat, plans in db["categories"].items():
                    for p in plans:
                        keyboard.append([InlineKeyboardButton(f"📦 {cat} - {p['name']}", callback_data=f"add_config_{p['id']}")])
                update.message.reply_text("برای کدام پلن می‌خواهید کانفیگ اضافه کنید؟", reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            # آمار
            if text == '📊 آمار':
                total_users = len(db["users"])
                total_purchases = sum(len(u.get("purchases", [])) for u in db["users"].values())
                total_tests = sum(len(u.get("tests", [])) for u in db["users"].values())
                total_wallet = sum(u.get("wallet", 0) for u in db["users"].values())
                total_configs = sum(len(c) for c in db["configs"].values())
                
                msg = f"📊 آمار ربات\n━━━━━━━━━━━━━━━━\n"
                msg += f"👥 کل کاربران: {total_users}\n"
                msg += f"💰 خریدها: {total_purchases}\n"
                msg += f"🎁 تست‌ها: {total_tests}\n"
                msg += f"💳 کل کیف پول: {total_wallet:,} تومان\n"
                msg += f"🔗 کانفیگ‌های موجود: {total_configs}\n"
                msg += f"📜 لاگ‌ها: {len(db.get('logs', []))}"
                update.message.reply_text(msg)
                return
            
            # ارسال همگانی
            if text == '📨 ارسال همگانی':
                user_data[uid] = {"step": "broadcast"}
                update.message.reply_text("📨 پیام همگانی را بفرستید:", reply_markup=back_button())
                return
            
            # ارسال تست همگانی
            if text == '📨 ارسال تست همگانی':
                user_data[uid] = {"step": "broadcast_test"}
                update.message.reply_text("📨 کانفیگ تست را برای همه کاربرانی که درخواست تست داشتند بفرستید:", reply_markup=back_button())
                return
            
            # پاکسازی تست‌ها
            if text == '🗑 پاکسازی تست‌ها':
                for uid2 in db["users"]:
                    db["users"][uid2]["test_count"] = 0
                save_db()
                update.message.reply_text("✅ تمام تست‌های کاربران پاکسازی شد\nکاربران می‌توانند دوباره تست بگیرند", reply_markup=admin_menu())
                add_log("clear_tests", uid, "پاکسازی همه تست‌ها")
                return
            
            # بکاپ
            if text == '📤 بکاپ':
                backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(db, f, ensure_ascii=False, indent=4)
                with open(backup_file, 'rb') as f:
                    context.bot.send_document(uid, f, caption=f"📦 بکاپ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                os.remove(backup_file)
                add_log("backup", uid, "گرفتن بکاپ")
                return
            
            # وضعیت ربات
            if text == '⚡ وضعیت ربات':
                status = "🟢 فعال" if db["bot_status"]["enabled"] else "🔴 غیرفعال"
                keyboard = [['🔴 خاموش کردن', '🟢 روشن کردن'], ['✏️ ویرایش پیام غیرفعال'], ['🔙 برگشت']]
                update.message.reply_text(f"⚡ وضعیت ربات:\n{status}\n\nپیام غیرفعال: {db['bot_status']['message']}", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
                return
            
            if text == '🔴 خاموش کردن':
                db["bot_status"]["enabled"] = False
                save_db()
                update.message.reply_text("✅ ربات غیرفعال شد (فقط ادمین‌ها دسترسی دارند)", reply_markup=admin_menu())
                return
            
            if text == '🟢 روشن کردن':
                db["bot_status"]["enabled"] = True
                save_db()
                update.message.reply_text("✅ ربات فعال شد", reply_markup=admin_menu())
                return
            
            if text == '✏️ ویرایش پیام غیرفعال':
                user_data[uid] = {"step": "edit_disable_msg"}
                update.message.reply_text("متن جدید پیام غیرفعال بودن ربات را بفرستید:", reply_markup=back_button())
                return
            
            if text == '⚙️ مدیریت':
                update.message.reply_text("🛠 پنل مدیریت:", reply_markup=admin_menu())
                return
        
        # ========== مراحل ویرایش ==========
        step = user_data.get(uid, {}).get("step")
        
        if step == "edit_card_number":
            if text.isdigit() and len(text) == 16:
                db["card"]["number"] = text
                save_db()
                update.message.reply_text("✅ شماره کارت ذخیره شد", reply_markup=admin_menu())
            else:
                update.message.reply_text("❌ شماره کارت باید 16 رقم باشد")
            user_data[uid] = {}
            return
        
        if step == "edit_card_name":
            db["card"]["name"] = text
            save_db()
            update.message.reply_text("✅ نام صاحب کارت ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == "edit_brand":
            db["brand"] = text
            save_db()
            update.message.reply_text("✅ برند ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == "edit_support":
            db["support"] = text
            save_db()
            update.message.reply_text("✅ پشتیبان ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == "edit_guide":
            db["guide"] = text
            save_db()
            update.message.reply_text("✅ کانال آموزش ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == "edit_test_reason":
            db["test_mode"]["reason"] = text
            save_db()
            update.message.reply_text("✅ پیام غیرفعال تست ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == "edit_disable_msg":
            db["bot_status"]["message"] = text
            save_db()
            update.message.reply_text("✅ پیام غیرفعال ربات ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step and step.startswith("edit_text_"):
            key = step.replace("edit_text_", "")
            db["texts"][key] = text
            save_db()
            update.message.reply_text("✅ متن ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == "set_force_link":
            db["force_join"]["link"] = text
            if "t.me/" in text:
                username = text.split("t.me/")[-1].split("/")[0].replace("@", "")
                db["force_join"]["username"] = f"@{username}"
                try:
                    chat = context.bot.get_chat(f"@{username}")
                    db["force_join"]["channel_id"] = str(chat.id)
                    update.message.reply_text(f"✅ کانال شناسایی شد: {chat.title}")
                except:
                    update.message.reply_text("⚠️ ربات در کانال ادمین نیست!")
            save_db()
            update.message.reply_text("✅ لینک کانال ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == "add_admin":
            if text.isdigit():
                ADMINS[text] = "ادمین"
                update.message.reply_text(f"✅ ادمین {text} اضافه شد", reply_markup=admin_menu())
                add_log("add_admin", uid, f"ادمین جدید: {text}")
            else:
                update.message.reply_text("❌ آیدی باید عددی باشد")
            user_data[uid] = {}
            return
        
        if step == "del_admin":
            if text == str(ADMIN_ID):
                update.message.reply_text("❌ نمی‌توانید مالک اصلی را حذف کنید")
            elif text in ADMINS:
                del ADMINS[text]
                update.message.reply_text(f"✅ ادمین {text} حذف شد", reply_markup=admin_menu())
            else:
                update.message.reply_text("❌ ادمین یافت نشد")
            user_data[uid] = {}
            return
        
        if step == "add_category":
            if text not in db["categories"]:
                db["categories"][text] = []
                save_db()
                update.message.reply_text(f"✅ دسته {text} اضافه شد", reply_markup=admin_menu())
            else:
                update.message.reply_text("❌ این دسته قبلاً وجود دارد")
            user_data[uid] = {}
            return
        
        if step == "del_category":
            if text in db["categories"]:
                del db["categories"][text]
                save_db()
                update.message.reply_text(f"✅ دسته {text} حذف شد", reply_markup=admin_menu())
            else:
                update.message.reply_text("❌ دسته یافت نشد")
            user_data[uid] = {}
            return
        
        if step == "broadcast":
            success = 0
            fail = 0
            for uid2 in db["users"]:
                try:
                    context.bot.send_message(int(uid2), text)
                    success += 1
                except:
                    fail += 1
            update.message.reply_text(f"✅ ارسال همگانی\nموفق: {success}\nناموفق: {fail}")
            add_log("broadcast", uid, f"ارسال همگانی")
            user_data[uid] = {}
            return
        
        if step == "broadcast_test":
            # پیدا کردن کاربرانی که تست گرفته‌اند
            test_users = []
            for uid2, data in db["users"].items():
                if data.get("test_count", 0) > 0:
                    test_users.append(uid2)
            
            success = 0
            fail = 0
            for uid2 in test_users:
                try:
                    context.bot.send_message(int(uid2), text)
                    success += 1
                except:
                    fail += 1
            update.message.reply_text(f"✅ ارسال تست همگانی\nموفق: {success}\nناموفق: {fail}\nتعداد کاربران تست داده: {len(test_users)}")
            add_log("broadcast_test", uid, f"ارسال تست همگانی")
            user_data[uid] = {}
            return
        
        # مراحل افزودن پلن
        if step == "add_plan_cat":
            if text == '➕ دسته جدید':
                user_data[uid] = {"step": "add_plan_new_cat"}
                update.message.reply_text("نام دسته جدید را وارد کنید:", reply_markup=back_button())
                return
            if text in db["categories"]:
                user_data[uid] = {"step": "add_plan_name", "cat": text}
                update.message.reply_text("نام پلن را وارد کنید:", reply_markup=back_button())
            return
        
        if step == "add_plan_new_cat":
            db["categories"][text] = []
            save_db()
            user_data[uid] = {"step": "add_plan_name", "cat": text}
            update.message.reply_text(f"✅ دسته {text} اضافه شد\nحالا نام پلن را وارد کنید:")
            return
        
        if step == "add_plan_name":
            user_data[uid]["name"] = text
            user_data[uid]["step"] = "add_plan_price"
            update.message.reply_text("قیمت پلن را به تومان وارد کنید:")
            return
        
        if step == "add_plan_price":
            try:
                user_data[uid]["price"] = int(text)
                user_data[uid]["step"] = "add_plan_volume"
                update.message.reply_text("حجم پلن را وارد کنید (مثال: 20GB):")
            except:
                update.message.reply_text("❌ عدد وارد کنید")
            return
        
        if step == "add_plan_volume":
            user_data[uid]["volume"] = text
            user_data[uid]["step"] = "add_plan_days"
            update.message.reply_text("مدت اعتبار به روز را وارد کنید:")
            return
        
        if step == "add_plan_days":
            try:
                user_data[uid]["days"] = int(text)
                user_data[uid]["step"] = "add_plan_users"
                update.message.reply_text("تعداد کاربران همزمان را وارد کنید:")
            except:
                update.message.reply_text("❌ عدد وارد کنید")
            return
        
        if step == "add_plan_users":
            try:
                users_count = int(text)
                # پیدا کردن بزرگترین ID
                max_id = 0
                for plans in db["categories"].values():
                    for p in plans:
                        if p["id"] > max_id:
                            max_id = p["id"]
                
                new_plan = {
                    "id": max_id + 1,
                    "name": user_data[uid]["name"],
                    "price": user_data[uid]["price"],
                    "volume": user_data[uid]["volume"],
                    "days": user_data[uid]["days"],
                    "users": users_count
                }
                cat = user_data[uid]["cat"]
                db["categories"][cat].append(new_plan)
                save_db()
                update.message.reply_text(f"✅ پلن {new_plan['name']} با موفقیت اضافه شد", reply_markup=admin_menu())
                add_log("add_plan", uid, f"پلن جدید: {new_plan['name']}")
            except:
                update.message.reply_text("❌ خطا در ایجاد پلن")
            user_data[uid] = {}
            return
        
    except Exception as e:
        logger.error(f"Message error: {e}")
        update.message.reply_text("❌ خطا، لطفاً دوباره تلاش کنید")

# ==================== هندلر عکس ====================
def handle_photo(update: Update, context):
    try:
        uid = str(update.effective_user.id)
        
        if user_data.get(uid, {}).get("step") == "waiting_receipt":
            pending = user_data[uid].get("pending_receipt")
            if not pending:
                update.message.reply_text("❌ اطلاعات خرید یافت نشد")
                return
            
            plan = pending["plan"]
            account = pending["account"]
            method = pending["method"]
            
            caption = (
                f"💰 فیش جدید\n━━━━━━━━━━━━━━━━\n"
                f"👤 {db['users'][uid]['name']}\n"
                f"🆔 {uid}\n"
                f"📦 {plan['name']}\n"
                f"👤 اکانت: {account}\n"
                f"💰 {plan['price']:,} تومان\n"
                f"💳 روش: {'ترکیبی' if method == 'mix' else 'کارت'}"
            )
            
            if method == "mix" and pending.get("used_wallet"):
                caption += f"\n✅ از کیف پول: {pending['used_wallet']:,} تومان"
            
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{uid}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{uid}")
            ]])
            
            context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=caption, reply_markup=btn)
            update.message.reply_text(db["texts"]["receipt_sent"])
            add_log("receipt", uid, f"ارسال فیش برای {plan['name']}")
            
            # ذخیره برای تایید
            user_data[uid]["pending_confirm"] = pending
            user_data[uid] = {}
            return
        
    except Exception as e:
        logger.error(f"Photo error: {e}")
        update.message.reply_text("❌ خطا در ارسال فیش")

# ==================== کالبک ====================
def handle_callback(update: Update, context):
    try:
        query = update.callback_query
        uid = str(query.from_user.id)
        data = query.data
        query.answer()
        
        # تایید عضویت
        if data == "check_join":
            if check_join(uid, context.bot):
                query.message.delete()
                welcome = db["texts"]["welcome"].format(brand=db["brand"])
                context.bot.send_message(uid, welcome, reply_markup=main_menu(uid))
            else:
                query.message.reply_text("❌ هنوز عضو کانال نشده‌اید! لطفاً عضو شوید و دکمه را بزنید.")
            return
        
        # برگشت
        if data == "back":
            query.message.delete()
            start(update, context)
            return
        
        # شارژ کیف پول
        if data.startswith("charge_"):
            if data == "charge_custom":
                user_data[uid] = {"step": "custom_charge"}
                query.message.reply_text("💰 مبلغ دلخواه (حداقل 50,000 و حداکثر 5,000,000 تومان) را وارد کنید:", reply_markup=back_button())
                return
            
            amount = int(data.split("_")[1])
            user_data[uid]["temp_charge"] = amount
            
            msg = (
                f"💰 درخواست شارژ کیف پول\n━━━━━━━━━━━━━━━━\n"
                f"👤 {query.from_user.first_name}\n"
                f"🆔 {uid}\n"
                f"💵 مبلغ: {amount:,} تومان\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"💳 شماره کارت:\n{db['card']['number']}\n"
                f"👤 {db['card']['name']}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"پس از واریز، عکس فیش را بفرستید"
            )
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش شارژ", callback_data="send_charge_receipt")]])
            query.message.reply_text(msg, reply_markup=btn)
            return
        
        if data == "send_charge_receipt":
            user_data[uid]["step"] = "waiting_charge_receipt"
            query.message.reply_text("📸 عکس فیش شارژ را بفرستید:")
            return
        
        # انتخاب پلن
        if data.startswith("plan_"):
            plan_id = int(data.split("_")[1])
            for cat in db["categories"].values():
                for p in cat:
                    if p["id"] == plan_id:
                        payment_methods(update, p)
                        return
            return
        
        # روش پرداخت
        if data.startswith("pay_"):
            parts = data.split("_")
            method = parts[1]
            plan_id = int(parts[2])
            for cat in db["categories"].values():
                for p in cat:
                    if p["id"] == plan_id:
                        ask_account_name(update, p, method)
                        return
            return
        
        # ارسال فیش
        if data == "send_receipt":
            if user_data.get(uid, {}).get("step") == "waiting_receipt":
                query.message.reply_text("📸 عکس فیش را بفرستید:")
            else:
                query.message.reply_text("❌ اطلاعات خرید یافت نشد")
            return
        
        # تایید فیش (ادمین)
        if data.startswith("confirm_"):
            if uid not in ADMINS:
                return
            target_uid = data.split("_")[1]
            pending = user_data.get(target_uid, {}).get("pending_confirm")
            if not pending:
                query.message.reply_text("❌ اطلاعات یافت نشد")
                return
            
            plan = pending["plan"]
            account = pending["account"]
            
            if db["auto_send"]:
                result = send_config_from_pool(target_uid, plan["id"], account, plan["name"], context.bot)
                if result:
                    # ثبت خرید
                    purchase_record = f"{plan['name']}|{plan['volume']}|{datetime.now().strftime('%Y-%m-%d')}|{account}"
                    if "purchases" not in db["users"][target_uid]:
                        db["users"][target_uid]["purchases"] = []
                    db["users"][target_uid]["purchases"].append(purchase_record)
                    save_db()
                    add_log("purchase_confirm", target_uid, f"تایید فیش {plan['name']}")
                    query.message.reply_text(f"✅ فیش تایید شد و کانفیگ برای کاربر ارسال شد")
                else:
                    query.message.reply_text(f"⚠️ فیش تایید شد اما کانفیگ موجود نیست، لطفاً کانفیگ اضافه کنید")
            else:
                context.bot.send_message(target_uid, db["texts"]["waiting"])
                context.bot.send_message(ADMIN_ID, f"⚠️ فیش تایید شد، لطفاً کانفیگ {plan['name']} را برای کاربر {target_uid} ارسال کنید")
                add_log("confirm_wait", target_uid, f"تایید فیش در انتظار کانفیگ دستی")
                query.message.reply_text(f"✅ فیش تایید شد، منتظر ارسال دستی کانفیگ")
            
            # حذف pending
            if target_uid in user_data:
                del user_data[target_uid]["pending_confirm"]
            query.message.edit_reply_markup(reply_markup=None)
            return
        
        # رد فیش
        if data.startswith("reject_"):
            if uid not in ADMINS:
                return
            target_uid = data.split("_")[1]
            user_data[uid] = {"step": "reject_reason", "target": target_uid}
            query.message.reply_text("دلیل رد فیش را وارد کنید:")
            return
        
        # ارسال تست (ادمین)
        if data.startswith("send_test_"):
            if uid not in ADMINS:
                return
            target_uid = data.split("_")[2]
            user_data[uid] = {"step": "send_test_config", "target": target_uid}
            query.message.reply_text("📨 کانفیگ تست را بفرستید:")
            query.message.edit_reply_markup(reply_markup=None)
            return
        
        # حذف پلن
        if data.startswith("del_plan_"):
            if uid not in ADMINS:
                return
            plan_id = int(data.split("_")[3])
            for cat, plans in db["categories"].items():
                for i, p in enumerate(plans):
                    if p["id"] == plan_id:
                        del plans[i]
                        save_db()
                        query.message.reply_text(f"✅ پلن {p['name']} حذف شد", reply_markup=admin_menu())
                        add_log("del_plan", uid, f"حذف پلن {p['name']}")
                        return
            query.message.reply_text("❌ پلن یافت نشد")
            return
        
        # ویرایش پلن - نمایش فرم
        if data.startswith("edit_plan_"):
            if uid not in ADMINS:
                return
            plan_id = int(data.split("_")[3])
            for cat, plans in db["categories"].items():
                for p in plans:
                    if p["id"] == plan_id:
                        user_data[uid] = {"step": "edit_plan", "plan_id": plan_id, "cat": cat, "plan": p}
                        keyboard = [
                            ['نام', 'قیمت'],
                            ['حجم', 'مدت'],
                            ['تعداد کاربران'],
                            ['🔙 برگشت']
                        ]
                        query.message.reply_text(
                            f"✏️ ویرایش پلن: {p['name']}\n"
                            f"قیمت: {p['price']:,} تومان\n"
                            f"حجم: {p['volume']}\n"
                            f"مدت: {p['days']} روز\n"
                            f"تعداد کاربران: {p['users']}\n"
                            f"\nکدام بخش را ویرایش می‌کنید؟",
                            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                        )
                        return
            query.message.reply_text("❌ پلن یافت نشد")
            return
        
        # افزودن کانفیگ - دریافت تعداد
        if data.startswith("add_config_"):
            if uid not in ADMINS:
                return
            plan_id = int(data.split("_")[2])
            user_data[uid] = {"step": "add_config_count", "plan_id": plan_id}
            query.message.reply_text("چند تا کانفیگ می‌خواهید اضافه کنید؟\n(عدد را وارد کنید)", reply_markup=back_button())
            return
        
    except Exception as e:
        logger.error(f"Callback error: {e}")
        query.message.reply_text("❌ خطا")

# ==================== پیام‌های مرحله‌ای (ادمین) ====================
def handle_step_messages(update: Update, context):
    try:
        uid = str(update.effective_user.id)
        text = update.message.text
        step = user_data.get(uid, {}).get("step")
        
        if not step:
            return False
        
        # شارژ دلخواه
        if step == "custom_charge":
            try:
                amount = int(text)
                if 50000 <= amount <= 5000000:
                    user_data[uid]["temp_charge"] = amount
                    msg = (
                        f"💰 درخواست شارژ کیف پول\n━━━━━━━━━━━━━━━━\n"
                        f"👤 {update.effective_user.first_name}\n"
                        f"🆔 {uid}\n"
                        f"💵 مبلغ: {amount:,} تومان\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"💳 شماره کارت:\n{db['card']['number']}\n"
                        f"👤 {db['card']['name']}\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"پس از واریز، عکس فیش را بفرستید"
                    )
                    btn = InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش شارژ", callback_data="send_charge_receipt")]])
                    update.message.reply_text(msg, reply_markup=btn)
                    del user_data[uid]["step"]
                else:
                    update.message.reply_text("❌ مبلغ باید بین 50,000 تا 5,000,000 تومان باشد")
            except:
                update.message.reply_text("❌ عدد وارد کنید")
            return True
        
        # دریافت عکس فیش شارژ
        if step == "waiting_charge_receipt":
            update.message.reply_text("📸 لطفاً عکس فیش را ارسال کنید")
            return True
        
        # دریافت دلیل رد
        if step == "reject_reason":
            target = user_data[uid].get("target")
            if target:
                msg = db["texts"]["rejected"].format(reason=text)
                try:
                    context.bot.send_message(int(target), msg)
                    update.message.reply_text(f"✅ فیش کاربر {target} رد شد")
                    add_log("reject", target, f"رد فیش: {text}")
                except:
                    update.message.reply_text("❌ خطا در ارسال پیام رد")
            del user_data[uid]
            return True
        
        # ارسال کانفیگ تست
        if step == "send_test_config":
            target = user_data[uid].get("target")
            if target:
                try:
                    context.bot.send_message(int(target), f"🎁 کانفیگ تست شما:\n\n{text}")
                    update.message.reply_text(f"✅ کانفیگ تست برای {target} ارسال شد")
                    add_log("send_test", target, "ارسال کانفیگ تست")
                except:
                    update.message.reply_text("❌ خطا در ارسال")
            del user_data[uid]
            return True
        
        # افزودن کانفیگ - تعداد
        if step == "add_config_count":
            try:
                count = int(text)
                if count > 0 and count <= 100:
                    user_data[uid]["config_count"] = count
                    user_data[uid]["config_received"] = []
                    user_data[uid]["step"] = "add_config_receive"
                    update.message.reply_text(f"✅ {count} تا کانفیگ را یکی یکی بفرستید.\n(هر بار یک کانفیگ بفرستید)\nبرای لغو /cancel را بزنید")
                else:
                    update.message.reply_text("❌ تعداد باید بین 1 تا 100 باشد")
            except:
                update.message.reply_text("❌ عدد وارد کنید")
            return True
        
        # دریافت کانفیگ‌ها
        if step == "add_config_receive":
            received = user_data[uid].get("config_received", [])
            count = user_data[uid].get("config_count", 0)
            
            if text == "/cancel":
                del user_data[uid]
                update.message.reply_text("❌ افزودن کانفیگ لغو شد", reply_markup=admin_menu())
                return True
            
            received.append(text)
            user_data[uid]["config_received"] = received
            
            remaining = count - len(received)
            if remaining > 0:
                update.message.reply_text(f"✅ کانفیگ {len(received)} ذخیره شد.\n{remaining} کانفیگ دیگر بفرستید:")
            else:
                # ذخیره همه کانفیگ‌ها
                plan_id = user_data[uid].get("plan_id")
                if str(plan_id) not in db["configs"]:
                    db["configs"][str(plan_id)] = []
                db["configs"][str(plan_id)].extend(received)
                save_db()
                update.message.reply_text(f"✅ {count} کانفیگ برای پلن مورد نظر ذخیره شد\nموجودی فعلی: {len(db['configs'][str(plan_id)])}", reply_markup=admin_menu())
                add_log("add_config", uid, f"افزودن {count} کانفیگ برای پلن {plan_id}")
                del user_data[uid]
            return True
        
        # ویرایش پلن
        if step == "edit_plan":
            plan_id = user_data[uid].get("plan_id")
            cat = user_data[uid].get("cat")
            field_map = {"نام": "name", "قیمت": "price", "حجم": "volume", "مدت": "days", "تعداد کاربران": "users"}
            
            if text in field_map:
                user_data[uid]["edit_field"] = field_map[text]
                user_data[uid]["step"] = "edit_plan_value"
                update.message.reply_text(f"مقدار جدید {text} را وارد کنید:", reply_markup=back_button())
                return True
            
            if text == "🔙 برگشت":
                del user_data[uid]
                update.message.reply_text("✅ ویرایش لغو شد", reply_markup=admin_menu())
                return True
            
            update.message.reply_text("❌ گزینه نامعتبر")
            return True
        
        if step == "edit_plan_value":
            plan_id = user_data[uid].get("plan_id")
            cat = user_data[uid].get("cat")
            field = user_data[uid].get("edit_field")
            
            for i, p in enumerate(db["categories"][cat]):
                if p["id"] == plan_id:
                    if field == "price" or field == "days" or field == "users":
                        try:
                            value = int(text)
                            db["categories"][cat][i][field] = value
                        except:
                            update.message.reply_text("❌ عدد وارد کنید")
                            return True
                    else:
                        db["categories"][cat][i][field] = text
                    
                    save_db()
                    update.message.reply_text(f"✅ {field} با موفقیت ویرایش شد", reply_markup=admin_menu())
                    add_log("edit_plan", uid, f"ویرایش پلن {p['name']} - {field}")
                    del user_data[uid]
                    return True
            
            update.message.reply_text("❌ خطا")
            del user_data[uid]
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Step message error: {e}")
        update.message.reply_text("❌ خطا")
        return True

# ==================== عکس برای فیش شارژ ====================
def handle_charge_photo(update: Update, context):
    try:
        uid = str(update.effective_user.id)
        
        if user_data.get(uid, {}).get("step") == "waiting_charge_receipt":
            amount = user_data[uid].get("temp_charge", 0)
            if amount > 0:
                caption = (
                    f"💰 فیش شارژ کیف پول\n━━━━━━━━━━━━━━━━\n"
                    f"👤 {update.effective_user.first_name}\n"
                    f"🆔 {uid}\n"
                    f"💵 مبلغ: {amount:,} تومان"
                )
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ تایید شارژ", callback_data=f"confirm_charge_{uid}"),
                    InlineKeyboardButton("❌ رد", callback_data=f"reject_charge_{uid}")
                ]])
                context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=caption, reply_markup=btn)
                update.message.reply_text("✅ فیش شارژ شما ارسال شد، پس از تایید کیف پول شما شارژ می‌شود")
                user_data[uid]["pending_charge"] = amount
                del user_data[uid]["step"]
                return True
    except Exception as e:
        logger.error(f"Charge photo error: {e}")
        update.message.reply_text("❌ خطا")
    return False

# ==================== کالبک شارژ ====================
def handle_charge_callback(update: Update, context):
    try:
        query = update.callback_query
        uid = str(query.from_user.id)
        data = query.data
        query.answer()
        
        # تایید شارژ
        if data.startswith("confirm_charge_"):
            if uid not in ADMINS:
                return
            target_uid = data.split("_")[2]
            if target_uid in user_data and "pending_charge" in user_data[target_uid]:
                amount = user_data[target_uid]["pending_charge"]
                db["users"][target_uid]["wallet"] = db["users"][target_uid].get("wallet", 0) + amount
                save_db()
                context.bot.send_message(int(target_uid), f"✅ کیف پول شما به مبلغ {amount:,} تومان شارژ شد\n💰 موجودی جدید: {db['users'][target_uid]['wallet']:,} تومان")
                add_log("charge", target_uid, f"شارژ کیف پول {amount} تومان")
                query.message.reply_text(f"✅ شارژ {target_uid} تایید شد")
                del user_data[target_uid]["pending_charge"]
                query.message.edit_reply_markup(reply_markup=None)
            return True
        
        # رد شارژ
        if data.startswith("reject_charge_"):
            if uid not in ADMINS:
                return
            target_uid = data.split("_")[2]
            user_data[uid] = {"step": "reject_charge_reason", "target": target_uid}
            query.message.reply_text("دلیل رد فیش شارژ را وارد کنید:")
            return
        
    except Exception as e:
        logger.error(f"Charge callback error: {e}")
    
    return False

# ==================== دلیل رد شارژ ====================
def handle_reject_reason(update: Update, context):
    try:
        uid = str(update.effective_user.id)
        if user_data.get(uid, {}).get("step") == "reject_charge_reason":
            target = user_data[uid].get("target")
            if target:
                context.bot.send_message(int(target), f"❌ فیش شارژ شما رد شد\nدلیل: {update.message.text}")
                update.message.reply_text(f"✅ فیش شارژ {target} رد شد")
                add_log("reject_charge", target, f"رد فیش شارژ: {update.message.text}")
            del user_data[uid]
            return True
    except Exception as e:
        logger.error(f"Reject reason error: {e}")
    return False

# ==================== اجرا ====================
def main():
    try:
        logger.info("🚀 Starting VPN Bot...")
        
        # Flask thread
        Thread(target=run_web, daemon=True).start()
        
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # Handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        dp.add_handler(MessageHandler(Filters.photo, handle_photo))
        dp.add_handler(CallbackQueryHandler(handle_callback))
        
        # Start polling
        updater.start_polling()
        logger.info("✅ Bot is running!")
        updater.idle()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == '__main__':
    main()

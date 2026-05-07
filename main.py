# main.py
import os
import json
import logging
import shutil
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from telegram.error import TelegramError

# ==================== تنظیمات لاگینگ ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== وب سرور ====================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "✅ VPN Bot is Running!", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==================== تنظیمات اصلی ====================
TOKEN = '8681405252:AAH7ONTudaE34evtbxWeLdk0dtZc_XkULEA'
ADMIN_ID = 5993860770
ADMINS = {str(ADMIN_ID): "مالک"}

DB_FILE = 'data.json'
BACKUP_DIR = 'backups'

# ==================== پلن‌های پیش‌فرض ====================
DEFAULT_PLANS = {
    "🚀 قوی": [
        {"id": 1, "name": "⚡️ پلن قوی 20GB", "price": 80000, "volume": "20GB", "days": 30, "users": 1},
        {"id": 2, "name": "🔥 پلن قوی 50GB", "price": 140000, "volume": "50GB", "days": 30, "users": 1}
    ],
    "💎 ارزان": [
        {"id": 3, "name": "💎 پلن اقتصادی 10GB", "price": 45000, "volume": "10GB", "days": 30, "users": 1},
        {"id": 4, "name": "💎 پلن اقتصادی 20GB", "price": 75000, "volume": "20GB", "days": 30, "users": 1}
    ],
    "🎯 به صرفه": [
        {"id": 5, "name": "🎯 پلن ویژه 30GB", "price": 110000, "volume": "30GB", "days": 30, "users": 1},
        {"id": 6, "name": "🎯 پلن ویژه 60GB", "price": 190000, "volume": "60GB", "days": 30, "users": 1}
    ],
    "👥 چند کاربره": [
        {"id": 7, "name": "👥 2 کاربره 40GB", "price": 150000, "volume": "40GB", "days": 30, "users": 2},
        {"id": 8, "name": "👥 3 کاربره 60GB", "price": 210000, "volume": "60GB", "days": 30, "users": 3}
    ]
}

DEFAULT_CONFIGS = {}  # {plan_id: [config1, config2, ...]}

# ==================== دیتابیس ====================
def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info("✅ Database loaded")
            
            # اضافه کردن فیلدهای جدید
            if "bot_status" not in data:
                data["bot_status"] = {"enabled": True, "disable_message": "ربات موقتاً غیرفعال است"}
            if "auto_send_config" not in data:
                data["auto_send_config"] = True
            if "test_mode" not in data:
                data["test_mode"] = {"enabled": True, "disable_reason": "تست رایگان غیرفعال شده است"}
            if "payment_methods" not in data:
                data["payment_methods"] = [{"type": "card", "name": "💳 کارت به کارت", "active": True}]
            if "configs" not in data:
                data["configs"] = DEFAULT_CONFIGS.copy()
            if "logs" not in data:
                data["logs"] = []
            return data
    except Exception as e:
        logger.error(f"❌ Error loading: {e}")
    
    # دیتابیس پیش‌فرض
    return {
        "users": {},
        "brand": "تک نت وی‌پی‌ان",
        "card": {"number": "6277601368776066", "name": "محمد رضوانی"},
        "support": "@Support_Admin",
        "guide": "@Guide_Channel",
        "categories": DEFAULT_PLANS.copy(),
        "force_join": {"enabled": False, "channel_id": "", "channel_link": "", "channel_username": ""},
        "bot_status": {"enabled": True, "disable_message": "ربات موقتاً غیرفعال است"},
        "auto_send_config": True,
        "test_mode": {"enabled": True, "disable_reason": "تست رایگان غیرفعال شده است"},
        "payment_methods": [{"type": "card", "name": "💳 کارت به کارت", "active": True}],
        "configs": DEFAULT_CONFIGS.copy(),
        "texts": {
            "welcome": "🔰 به {brand} خوش آمدید\n\n✅ فروش ویژه فیلترشکن\n✅ پشتیبانی 24 ساعته\n✅ نصب آسان",
            "support": "🆘 پشتیبانی: {support}",
            "guide": "📚 آموزش: {guide}",
            "test": "🎁 درخواست تست شما ثبت شد",
            "force": "🔒 برای استفاده از ربات باید در کانال زیر عضو شوید:\n{link}\n\nپس از عضویت، دکمه ✅ تایید را بزنید.",
            "invite": "🤝 لینک دعوت شما:\n{link}\n\nبه ازای هر دعوت 1 روز هدیه",
            "receipt_sent": "✅ فیش شما ارسال شد، پس از تایید سرویس فعال می‌شود",
            "waiting_for_config": "⏳ درخواست شما ثبت شد، به زودی کانفیگ ارسال می‌شود",
            "config_sent": "🎉 سرویس شما آماده شد\n━━━━━━━━━━━━━━━━\n📦 {plan_name}\n📅 {date}\n👤 {account_name}\n━━━━━━━━━━━━━━━━\n🔗 {config}\n━━━━━━━━━━━━━━━━\n📚 {guide}",
            "receipt_rejected": "❌ فیش شما رد شد\nدلیل: {reason}"
        },
        "logs": []
    }

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

def add_log(action, user_id, details):
    """ثبت لاگ"""
    log_entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "user_id": user_id,
        "details": details
    }
    db["logs"].append(log_entry)
    if len(db["logs"]) > 1000:
        db["logs"] = db["logs"][-500:]
    save_db()

# ==================== منوها ====================
def main_menu(uid):
    kb = [
        ['💰 خرید', '🎁 تست', '💳 کیف پول'],
        ['📂 سرویس‌ها', '⏳ تمدید'],
        ['👤 پشتیبانی', '📚 آموزش'],
        ['🤝 دعوت دوستان']
    ]
    if str(uid) in ADMINS:
        kb.append(['⚙️ مدیریت'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def back_btn():
    return ReplyKeyboardMarkup([['🔙 برگشت']], resize_keyboard=True)

def admin_menu():
    kb = [
        ['➕ پلن جدید', '✏️ ویرایش پلن', '➖ حذف پلن'],
        ['📁 دسته‌بندی', '👥 مدیریت ادمین'],
        ['💳 ویرایش کارت', '📝 ویرایش متن‌ها'],
        ['👤 ویرایش پشتیبان', '📢 ویرایش کانال'],
        ['🔒 عضویت اجباری', '🏷 ویرایش برند'],
        ['🎁 مدیریت تست', '🤖 ارسال خودکار'],
        ['📊 آمار', '📨 ارسال همگانی'],
        ['📤 بکاپ', '⚡ وضعیت ربات'],
        ['🔙 برگشت']
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def payment_methods_menu():
    kb = []
    for method in db["payment_methods"]:
        if method["active"]:
            kb.append([InlineKeyboardButton(method["name"], callback_data=f"pay_{method['type']}")])
    kb.append([InlineKeyboardButton("🔙 انصراف", callback_data="cancel_pay")])
    return InlineKeyboardMarkup(kb)

# ==================== بررسی عضویت ====================
def check_join(user_id, context):
    if not db["force_join"]["enabled"]:
        return True
    
    channel_id = db["force_join"].get("channel_id", "")
    channel_username = db["force_join"].get("channel_username", "")
    
    if not channel_id and not channel_username:
        return True
    
    if channel_id:
        try:
            member = context.bot.get_chat_member(chat_id=int(channel_id), user_id=int(user_id))
            if member.status in ['member', 'administrator', 'creator']:
                return True
        except:
            pass
    
    if channel_username:
        try:
            member = context.bot.get_chat_member(chat_id=channel_username, user_id=int(user_id))
            if member.status in ['member', 'administrator', 'creator']:
                return True
        except:
            pass
    
    return False

def check_bot_status(update):
    """بررسی وضعیت ربات"""
    if db["bot_status"]["enabled"]:
        return True
    uid = str(update.effective_user.id)
    if uid in ADMINS:
        return True
    update.message.reply_text(db["bot_status"]["disable_message"])
    return False

# ==================== دستور استارت ====================
def start(update, context):
    uid = str(update.effective_user.id)
    
    # ثبت کاربر جدید
    if uid not in db["users"]:
        db["users"][uid] = {
            "first_name": update.effective_user.first_name or "کاربر",
            "username": update.effective_user.username,
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "wallet": 0,
            "purchases": [],
            "tests": [],
            "test_count": 0,
            "invite_count": 0,
            "invites": [],
            "referred_by": None
        }
        # بررسی referral
        if context.args and len(context.args) > 0:
            ref_id = context.args[0]
            if ref_id != uid and ref_id in db["users"]:
                db["users"][uid]["referred_by"] = ref_id
                db["users"][ref_id]["invite_count"] += 1
                db["users"][ref_id]["invites"].append(uid)
                add_log("invite", ref_id, f"کاربر {uid} دعوت شد")
        save_db()
        add_log("register", uid, "ثبت نام جدید")
    
    user_data[uid] = {}
    
    # بررسی عضویت اجباری
    if db["force_join"]["enabled"] and db["force_join"]["channel_link"]:
        if not check_join(uid, context):
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 عضویت در کانال", url=db["force_join"]["channel_link"]),
                InlineKeyboardButton("✅ تایید عضویت", callback_data="join_check")
            ]])
            msg = db["texts"]["force"].format(link=db["force_join"]["channel_link"])
            update.message.reply_text(msg, reply_markup=btn)
            return
    
    welcome = db["texts"]["welcome"].format(brand=db["brand"])
    update.message.reply_text(welcome, reply_markup=main_menu(uid))

# ==================== کیف پول ====================
def show_wallet(update):
    uid = str(update.effective_user.id)
    wallet = db["users"][uid].get("wallet", 0)
    kb = [
        [InlineKeyboardButton("➕ 100,000 تومان", callback_data="wallet_100000")],
        [InlineKeyboardButton("➕ 300,000 تومان", callback_data="wallet_300000")],
        [InlineKeyboardButton("➕ 500,000 تومان", callback_data="wallet_500000")],
        [InlineKeyboardButton("➕ 1,000,000 تومان", callback_data="wallet_1000000")],
        [InlineKeyboardButton("➕ 2,000,000 تومان", callback_data="wallet_2000000")],
        [InlineKeyboardButton("💰 مبلغ دلخواه", callback_data="wallet_custom")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="wallet_back")]
    ]
    update.message.reply_text(
        f"💳 موجودی کیف پول شما:\n━━━━━━━━━━━━━━━━\n💰 {wallet:,} تومان\n━━━━━━━━━━━━━━━━\nمبلغ مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ==================== خرید ====================
def purchase(update):
    categories = list(db["categories"].keys())
    kb = [[c] for c in categories] + [['🔙 برگشت']]
    update.message.reply_text(
        "📦 دسته را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

def show_plans(update, category):
    plans = db["categories"][category]
    keyboard = []
    for p in plans:
        btn = InlineKeyboardButton(
            f"{p['name']} - {p['price']:,} تومان",
            callback_data=f"plan_{p['id']}"
        )
        keyboard.append([btn])
    update.message.reply_text(
        f"📦 {category}\n━━━━━━━━━━━━━━━━\nپلن مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def payment_options(update, plan_id):
    uid = str(update.effective_user.id)
    for cat in db["categories"].values():
        for p in cat:
            if p["id"] == plan_id:
                user_data[uid]["temp_plan"] = p
                
                keyboard = [
                    [InlineKeyboardButton("💳 پرداخت با کارت", callback_data=f"paymethod_card_{plan_id}")],
                    [InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data=f"paymethod_wallet_{plan_id}")],
                    [InlineKeyboardButton("⚡ خرید ترکیبی", callback_data=f"paymethod_mix_{plan_id}")],
                    [InlineKeyboardButton("🔙 انصراف", callback_data="cancel_pay")]
                ]
                update.message.reply_text(
                    f"💰 {p['name']}\n━━━━━━━━━━━━━━━━\n💵 قیمت: {p['price']:,} تومان\n━━━━━━━━━━━━━━━━\nروش پرداخت را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return

def process_card_payment(update, context, plan):
    uid = str(update.effective_user.id)
    user_data[uid]["temp_purchase"] = {
        "plan": plan,
        "account_name": None,
        "payment_method": "card"
    }
    update.message.reply_text("📝 لطفاً نام اکانت خود را وارد کنید:")

def process_wallet_payment(update, plan):
    uid = str(update.effective_user.id)
    wallet = db["users"][uid].get("wallet", 0)
    
    if wallet >= plan["price"]:
        db["users"][uid]["wallet"] = wallet - plan["price"]
        save_db()
        add_log("purchase_wallet", uid, f"خرید {plan['name']} با کیف پول")
        # درخواست نام اکانت
        user_data[uid]["temp_purchase"] = {
            "plan": plan,
            "account_name": None,
            "payment_method": "wallet",
            "wallet_paid": True
        }
        update.message.reply_text("📝 لطفاً نام اکانت خود را وارد کنید:")
    else:
        remaining = plan["price"] - wallet
        update.message.reply_text(
            f"❌ موجودی کیف پول شما کافی نیست\n"
            f"💰 موجودی: {wallet:,} تومان\n"
            f"💵 نیاز: {remaining:,} تومان اضافی\n"
            f"لطفاً کیف پول خود را شارژ کنید یا از روش کارت استفاده کنید."
        )

def process_mix_payment(update, plan):
    uid = str(update.effective_user.id)
    user_data[uid]["temp_purchase"] = {
        "plan": plan,
        "account_name": None,
        "payment_method": "mix"
    }
    wallet = db["users"][uid].get("wallet", 0)
    remaining = max(0, plan["price"] - wallet)
    update.message.reply_text(
        f"💰 موجودی کیف پول: {wallet:,} تومان\n"
        f"💵 مبلغ باقیمانده: {remaining:,} تومان\n"
        f"لطفاً نام اکانت خود را وارد کنید:\n"
        f"(پس از وارد کردن نام اکانت، اطلاعات کارت برای واریز مبلغ باقیمانده ارسال می‌شود)"
    )

def request_account_name(update, context, plan, payment_method, wallet_paid=False):
    uid = str(update.effective_user.id)
    user_data[uid]["temp_purchase"] = {
        "plan": plan,
        "payment_method": payment_method,
        "wallet_paid": wallet_paid
    }
    update.message.reply_text("📝 لطفاً نام اکانت خود را وارد کنید:")

def show_invoice(update, context, plan, account_name, payment_method, wallet_paid=0):
    uid = str(update.effective_user.id)
    wallet = db["users"][uid].get("wallet", 0)
    remaining = max(0, plan["price"] - wallet) if payment_method == "mix" else plan["price"]
    
    msg = (
        f"🧾 پیش فاکتور خرید\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📦 پلن: {plan['name']}\n"
        f"💰 مبلغ: {plan['price']:,} تومان\n"
        f"👤 نام اکانت: {account_name}\n"
    )
    
    if payment_method == "wallet":
        msg += f"💳 پرداخت از کیف پول\n"
        msg += f"━━━━━━━━━━━━━━━━\n"
        msg += f"✅ مبلغ {plan['price']:,} تومان از کیف پول شما کسر شد\n"
        msg += f"💰 موجودی جدید: {db['users'][uid]['wallet']:,} تومان"
        update.message.reply_text(msg)
        # ادامه برای دریافت کانفیگ
        if db["auto_send_config"]:
            send_config_from_pool(update, context, uid, plan, account_name)
        else:
            update.message.reply_text(db["texts"]["waiting_for_config"])
            add_log("config_waiting", uid, f"در انتظار کانفیگ {plan['name']}")
    elif payment_method == "mix":
        msg += (
            f"💳 روش پرداخت: ترکیبی\n"
            f"💰 استفاده از کیف پول: {wallet:,} تومان\n"
            f"💵 مبلغ قابل پرداخت: {remaining:,} تومان\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💳 شماره کارت:\n{db['card']['number']}\n"
            f"👤 {db['card']['name']}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"پس از واریز، عکس فیش را بفرستید"
        )
        user_data[uid]["temp_purchase"]["account_name"] = account_name
        user_data[uid]["temp_purchase"]["awaiting_receipt"] = True
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("📤 ارسال فیش", callback_data="send_receipt")
        ]])
        update.message.reply_text(msg, reply_markup=btn)
    else:  # card
        msg += (
            f"💳 روش پرداخت: کارت به کارت\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💳 شماره کارت:\n{db['card']['number']}\n"
            f"👤 {db['card']['name']}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"پس از واریز، عکس فیش را بفرستید"
        )
        user_data[uid]["temp_purchase"]["account_name"] = account_name
        user_data[uid]["temp_purchase"]["awaiting_receipt"] = True
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("📤 ارسال فیش", callback_data="send_receipt")
        ]])
        update.message.reply_text(msg, reply_markup=btn)

def send_config_from_pool(update, context, user_id, plan, account_name):
    """ارسال کانفیگ از استخر"""
    plan_id = plan["id"]
    configs = db["configs"].get(str(plan_id), [])
    
    if configs:
        config = configs.pop(0)
        db["configs"][str(plan_id)] = configs
        save_db()
        
        # ثبت سرویس
        service_record = f"{plan['name']}|{plan['volume']}|{datetime.now().strftime('%Y-%m-%d')}|{account_name}"
        if "purchases" not in db["users"][user_id]:
            db["users"][user_id]["purchases"] = []
        db["users"][user_id]["purchases"].append(service_record)
        save_db()
        
        msg = db["texts"]["config_sent"].format(
            plan_name=plan['name'],
            date=datetime.now().strftime('%Y-%m-%d %H:%M'),
            account_name=account_name,
            config=config,
            guide=db["guide"]
        )
        try:
            context.bot.send_message(int(user_id), msg)
            add_log("config_sent", user_id, f"ارسال خودکار {plan['name']}")
        except Exception as e:
            logger.error(f"Send config error: {e}")
            add_log("config_error", user_id, f"خطا در ارسال کانفیگ: {e}")
    else:
        # موجودی کانفیگ تمام شده
        if str(plan_id) not in db["configs"]:
            db["configs"][str(plan_id)] = []
        # ثبت درخواست و اطلاع به ادمین
        add_log("config_needed", user_id, f"موجودی کانفیگ {plan['name']} تمام شد")
        try:
            context.bot.send_message(
                ADMIN_ID,
                f"⚠️ موجودی کانفیگ {plan['name']} تمام شد!\n"
                f"کاربر: {user_id}\n"
                f"لطفاً کانفیگ جدید اضافه کنید"
            )
        except:
            pass
        update.message.reply_text("⚠️ در حال آماده‌سازی سرویس، به زودی کانفیگ ارسال می‌شود")

# ==================== مدیریت کانفیگ ====================
def add_config(update, context, plan_id, config_text):
    """افزودن کانفیگ به استخر"""
    if str(plan_id) not in db["configs"]:
        db["configs"][str(plan_id)] = []
    db["configs"][str(plan_id)].append(config_text)
    save_db()
    update.message.reply_text(f"✅ کانفیگ با موفقیت اضافه شد\nموجودی: {len(db['configs'][str(plan_id)])}")

# ==================== پیام‌ها ====================
def handle_msg(update, context):
    try:
        if not check_bot_status(update):
            return
            
        text = update.message.text
        uid = str(update.effective_user.id)
        name = update.effective_user.first_name or "کاربر"
        step = user_data.get(uid, {}).get('step')
        
        # بررسی عضویت
        if db["force_join"]["enabled"] and db["force_join"]["channel_link"]:
            if not check_join(uid, context) and text != '/start':
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 عضویت در کانال", url=db["force_join"]["channel_link"]),
                    InlineKeyboardButton("✅ تایید عضویت", callback_data="join_check")
                ]])
                update.message.reply_text(
                    db["texts"]["force"].format(link=db["force_join"]["channel_link"]),
                    reply_markup=btn
                )
                return
        
        # برگشت
        if text == '🔙 برگشت':
            user_data[uid] = {}
            start(update, context)
            return
        
        # کیف پول
        if text == '💳 کیف پول':
            show_wallet(update)
            return
        
        # تست رایگان
        if text == '🎁 تست':
            if not db["test_mode"]["enabled"]:
                update.message.reply_text(f"❌ {db['test_mode']['disable_reason']}")
                return
            if db["users"][uid]["test_count"] >= 1:
                update.message.reply_text("❌ شما قبلاً تست گرفته‌اید")
                return
            
            db["users"][uid]["test_count"] += 1
            db["users"][uid]["tests"].append(datetime.now().strftime("%Y-%m-%d"))
            save_db()
            update.message.reply_text(db["texts"]["test"])
            add_log("test_request", uid, "درخواست تست")
            
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 ارسال تست", callback_data=f"send_test_{uid}")
            ]])
            context.bot.send_message(ADMIN_ID, f"🎁 درخواست تست\n👤 {name}\n🆔 {uid}", reply_markup=btn)
            return
        
        # سرویس‌ها
        if text == '📂 سرویس‌ها':
            purchases = db["users"][uid].get("purchases", [])
            tests = db["users"][uid].get("tests", [])
            msg = "📂 سرویس‌های شما:\n━━━━━━━━━━━━━━━━\n"
            if purchases:
                msg += "✅ خریدها:\n"
                for i, p in enumerate(purchases[-10:], 1):
                    parts = p.split('|')
                    if len(parts) >= 2:
                        msg += f"{i}. {parts[0]} - {parts[1]} ({parts[2] if len(parts) > 2 else 'نامشخص'})\n"
                    else:
                        msg += f"{i}. {p}\n"
            else:
                msg += "❌ خریدی ندارید\n"
            if tests:
                msg += f"\n🎁 تست‌ها:\n"
                for i, t in enumerate(tests[-5:], 1):
                    msg += f"{i}. {t}\n"
            update.message.reply_text(msg)
            return
        
        # تمدید
        if text == '⏳ تمدید':
            purchases = db["users"][uid].get("purchases", [])
            if not purchases:
                update.message.reply_text("❌ سرویسی برای تمدید ندارید")
                return
            keyboard = []
            for i, p in enumerate(purchases[-5:]):
                parts = p.split('|')
                display = parts[0] if parts else p[:30]
                keyboard.append([InlineKeyboardButton(f"🔄 {display}", callback_data=f"renew_{i}")])
            update.message.reply_text(
                "سرویس مورد نظر را برای تمدید انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # پشتیبانی
        if text == '👤 پشتیبانی':
            update.message.reply_text(db["texts"]["support"].format(support=db["support"]))
            return
        
        # آموزش
        if text == '📚 آموزش':
            update.message.reply_text(db["texts"]["guide"].format(guide=db["guide"]))
            return
        
        # دعوت
        if text == '🤝 دعوت دوستان':
            bot = context.bot.get_me().username
            link = f"https://t.me/{bot}?start={uid}"
            invites = db["users"][uid].get("invite_count", 0)
            msg = db["texts"]["invite"].format(link=link)
            msg += f"\n━━━━━━━━━━━━━━━━\n👥 تعداد دعوت: {invites}\n🎁 هر دعوت = 1 روز هدیه"
            update.message.reply_text(msg)
            return
        
        # خرید
        if text == '💰 خرید':
            purchase(update)
            return
        
        # نمایش پلن‌ها
        if text in db["categories"] and not step:
            show_plans(update, text)
            return
        
        # ==================== مدیریت ====================
        if uid in ADMINS:
            if text == '⚙️ مدیریت':
                update.message.reply_text("🛠 پنل مدیریت:", reply_markup=admin_menu())
                return
            
            # ویرایش کارت
            if text == '💳 ویرایش کارت':
                keyboard = [['شماره کارت', 'نام صاحب کارت'], ['🔙 برگشت']]
                current = f"شماره: {db['card']['number']}\nنام: {db['card']['name']}"
                update.message.reply_text(current, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
                return
            if text == 'شماره کارت':
                user_data[uid] = {'step': 'card_num'}
                update.message.reply_text("شماره کارت 16 رقمی را بفرستید:", reply_markup=back_btn())
                return
            if text == 'نام صاحب کارت':
                user_data[uid] = {'step': 'card_name'}
                update.message.reply_text("نام صاحب کارت را بفرستید:", reply_markup=back_btn())
                return
            
            # ویرایش پشتیبان
            if text == '👤 ویرایش پشتیبان':
                user_data[uid] = {'step': 'support'}
                update.message.reply_text("آیدی پشتیبان را بفرستید:", reply_markup=back_btn())
                return
            
            # ویرایش کانال
            if text == '📢 ویرایش کانال':
                user_data[uid] = {'step': 'guide'}
                update.message.reply_text("آیدی کانال آموزش را بفرستید:", reply_markup=back_btn())
                return
            
            # ویرایش برند
            if text == '🏷 ویرایش برند':
                user_data[uid] = {'step': 'brand'}
                update.message.reply_text("نام برند را بفرستید:", reply_markup=back_btn())
                return
            
            # ویرایش متن‌ها
            if text == '📝 ویرایش متن‌ها':
                keyboard = [
                    ['خوش‌آمدگویی', 'پشتیبانی', 'آموزش'],
                    ['تست رایگان', 'عضویت اجباری', 'دعوت دوستان'],
                    ['پیام فیش', 'پیام کانفیگ', 'رد فیش'],
                    ['🔙 برگشت']
                ]
                update.message.reply_text(
                    "📝 کدام متن را ویرایش کنیم؟",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return
            
            text_map = {
                'خوش‌آمدگویی': 'welcome',
                'پشتیبانی': 'support',
                'آموزش': 'guide',
                'تست رایگان': 'test',
                'عضویت اجباری': 'force',
                'دعوت دوستان': 'invite',
                'پیام فیش': 'receipt_sent',
                'پیام کانفیگ': 'config_sent',
                'رد فیش': 'receipt_rejected'
            }
            if text in text_map:
                user_data[uid] = {'step': f'edit_{text_map[text]}'}
                current_text = db["texts"][text_map[text]]
                update.message.reply_text(
                    f"متن فعلی:\n{current_text}\n\nمتن جدید را بفرستید:",
                    reply_markup=back_btn()
                )
                return
            
            # عضویت اجباری
            if text == '🔒 عضویت اجباری':
                keyboard = [['✅ فعال', '❌ غیرفعال'], ['🔗 تنظیم لینک'], ['🔙 برگشت']]
                status = "✅ فعال" if db["force_join"]["enabled"] else "❌ غیرفعال"
                channel = db["force_join"]["channel_username"] or "تنظیم نشده"
                update.message.reply_text(
                    f"🔒 وضعیت:\nوضعیت: {status}\nکانال: {channel}",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return
            if text == '✅ فعال':
                if db["force_join"]["channel_link"]:
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
                user_data[uid] = {'step': 'set_link'}
                update.message.reply_text("🔗 لینک کانال را بفرستید:\nمثال: https://t.me/mychannel", reply_markup=back_btn())
                return
            
            # مدیریت تست
            if text == '🎁 مدیریت تست':
                keyboard = [['✅ فعال کردن تست', '❌ غیرفعال کردن تست'], ['✏️ ویرایش پیام غیرفعال'], ['🔙 برگشت']]
                status = "✅ فعال" if db["test_mode"]["enabled"] else "❌ غیرفعال"
                update.message.reply_text(
                    f"🎁 وضعیت تست رایگان:\n{status}\n\nدلیل غیرفعال: {db['test_mode']['disable_reason']}",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
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
                user_data[uid] = {'step': 'edit_test_reason'}
                update.message.reply_text("متن جدید برای پیام غیرفعال بودن تست را بفرستید:", reply_markup=back_btn())
                return
            
            # ارسال خودکار
            if text == '🤖 ارسال خودکار':
                status = "روشن" if db["auto_send_config"] else "خاموش"
                keyboard = [['✅ روشن کردن', '❌ خاموش کردن'], ['🔙 برگشت']]
                update.message.reply_text(
                    f"🤖 وضعیت ارسال خودکار کانفیگ:\n{status}\n\nدر حالت خودکار، پس از تایید پرداخت کانفیگ ارسال می‌شود.\nدر حالت دستی، کاربر پیام انتظار می‌گیرد.",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return
            if text == '✅ روشن کردن':
                db["auto_send_config"] = True
                save_db()
                update.message.reply_text("✅ ارسال خودکار کانفیگ روشن شد", reply_markup=admin_menu())
                return
            if text == '❌ خاموش کردن':
                db["auto_send_config"] = False
                save_db()
                update.message.reply_text("✅ ارسال خودکار کانفیگ خاموش شد", reply_markup=admin_menu())
                return
            
            # آمار
            if text == '📊 آمار':
                total = len(db["users"])
                purchases = sum(len(u.get("purchases", [])) for u in db["users"].values())
                tests = sum(len(u.get("tests", [])) for u in db["users"].values())
                today = datetime.now().strftime("%Y-%m-%d")
                today_users = sum(1 for u in db["users"].values() if u.get("join_date", "").startswith(today))
                total_wallet = sum(u.get("wallet", 0) for u in db["users"].values())
                configs_count = sum(len(c) for c in db["configs"].values())
                
                update.message.reply_text(
                    f"📊 آمار ربات\n━━━━━━━━━━━━━━━━\n"
                    f"👥 کل کاربران: {total}\n"
                    f"🆕 امروز: {today_users}\n"
                    f"💰 خریدها: {purchases}\n"
                    f"🎁 تست‌ها: {tests}\n"
                    f"💳 کل کیف پول: {total_wallet:,} تومان\n"
                    f"🔗 کانفیگ‌های موجود: {configs_count}\n"
                    f"📜 لاگ‌ها: {len(db['logs'])}"
                )
                return
            
            # ارسال همگانی
            if text == '📨 ارسال همگانی':
                user_data[uid] = {'step': 'broadcast'}
                update.message.reply_text("📨 پیام همگانی را بفرستید:\n(میتواند متن یا عکس باشد)", reply_markup=back_btn())
                return
            
            # پلن جدید
            if text == '➕ پلن جدید':
                categories = list(db["categories"].keys())
                kb = [[c] for c in categories] + [['➕ دسته جدید'], ['🔙 برگشت']]
                user_data[uid] = {'step': 'new_cat'}
                update.message.reply_text(
                    "دسته را انتخاب کنید یا دسته جدید بسازید:",
                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
                )
                return
            
            # ویرایش پلن
            if text == '✏️ ویرایش پلن':
                keyboard = []
                for cat, plans in db["categories"].items():
                    for p in plans:
                        btn = InlineKeyboardButton(
                            f"✏️ {cat} - {p['name']}",
                            callback_data=f"edit_plan_{p['id']}"
                        )
                        keyboard.append([btn])
                if keyboard:
                    update.message.reply_text(
                        "پلن را برای ویرایش انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    update.message.reply_text("❌ پلنی نیست")
                return
            
            # حذف پلن
            if text == '➖ حذف پلن':
                keyboard = []
                for cat, plans in db["categories"].items():
                    for p in plans:
                        btn = InlineKeyboardButton(
                            f"❌ {cat} - {p['name']}",
                            callback_data=f"del_plan_{p['id']}"
                        )
                        keyboard.append([btn])
                if keyboard:
                    update.message.reply_text(
                        "پلن را برای حذف انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    update.message.reply_text("❌ پلنی نیست")
                return
            
            # دسته‌بندی
            if text == '📁 دسته‌بندی':
                keyboard = [['➕ دسته جدید', '➖ حذف دسته'], ['🔙 برگشت']]
                update.message.reply_text(
                    "مدیریت دسته‌بندی‌ها:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return
            if text == '➕ دسته جدید':
                user_data[uid] = {'step': 'new_cat_name'}
                update.message.reply_text("نام دسته جدید را وارد کنید:", reply_markup=back_btn())
                return
            if text == '➖ حذف دسته':
                cats = list(db["categories"].keys())
                kb = [[c] for c in cats] + [['🔙 برگشت']]
                user_data[uid] = {'step': 'del_cat'}
                update.message.reply_text(
                    "دسته را برای حذف انتخاب کنید:",
                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
                )
                return
            
            # مدیریت ادمین
            if text == '👥 مدیریت ادمین':
                admins_list = "\n".join([f"🆔 {aid}: {aname}" for aid, aname in ADMINS.items()])
                keyboard = [['➕ افزودن ادمین', '➖ حذف ادمین'], ['🔙 برگشت']]
                update.message.reply_text(
                    f"👥 لیست ادمین‌ها:\n{admins_list}",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return
            if text == '➕ افزودن ادمین':
                user_data[uid] = {'step': 'add_admin'}
                update.message.reply_text("🆔 آیدی عددی ادمین جدید را بفرستید:", reply_markup=back_btn())
                return
            if text == '➖ حذف ادمین':
                user_data[uid] = {'step': 'del_admin'}
                update.message.reply_text("🆔 آیدی ادمین را برای حذف بفرستید:", reply_markup=back_btn())
                return
            
            # بکاپ
            if text == '📤 بکاپ':
                keyboard = [['📤 گرفتن بکاپ', '📥 بازیابی بکاپ'], ['🔙 برگشت']]
                update.message.reply_text(
                    "مدیریت بکاپ:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return
            if text == '📤 گرفتن بکاپ':
                backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                try:
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        json.dump(db, f, ensure_ascii=False, indent=4)
                    with open(backup_file, 'rb') as f:
                        context.bot.send_document(uid, f, caption=f"📦 بکاپ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                    os.remove(backup_file)
                    add_log("backup", uid, "گرفتن بکاپ")
                except Exception as e:
                    update.message.reply_text(f"❌ خطا در گرفتن بکاپ: {e}")
                return
            if text == '📥 بازیابی بکاپ':
                user_data[uid] = {'step': 'restore_backup'}
                update.message.reply_text("📁 فایل بکاپ JSON را بفرستید:", reply_markup=back_btn())
                return
            
            # وضعیت ربات
            if text == '⚡ وضعیت ربات':
                status = "🟢 فعال" if db["bot_status"]["enabled"] else "🔴 غیرفعال"
                keyboard = [['🔴 خاموش کردن', '🟢 روشن کردن'], ['✏️ ویرایش پیام غیرفعال'], ['🔙 برگشت']]
                update.message.reply_text(
                    f"⚡ وضعیت ربات:\n{status}\n\nپیام غیرفعال: {db['bot_status']['disable_message']}",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
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
                user_data[uid] = {'step': 'edit_disable_msg'}
                update.message.reply_text("متن جدید پیام غیرفعال بودن ربات را بفرستید:", reply_markup=back_btn())
                return
        
        # ==================== مراحل ویرایش ====================
        if step == 'card_num':
            if text.isdigit() and len(text) == 16:
                db["card"]["number"] = text
                save_db()
                update.message.reply_text("✅ شماره کارت ذخیره شد", reply_markup=admin_menu())
            else:
                update.message.reply_text("❌ شماره کارت نامعتبر")
            user_data[uid] = {}
            return
        
        if step == 'card_name':
            db["card"]["name"] = text
            save_db()
            update.message.reply_text("✅ نام صاحب کارت ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == 'support':
            db["support"] = text
            save_db()
            update.message.reply_text("✅ پشتیبان ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == 'guide':
            db["guide"] = text
            save_db()
            update.message.reply_text("✅ کانال آموزش ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == 'brand':
            db["brand"] = text
            save_db()
            update.message.reply_text("✅ برند ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step and step.startswith('edit_'):
            key = step.replace('edit_', '')
            db["texts"][key] = text
            save_db()
            update.message.reply_text("✅ متن ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == 'edit_test_reason':
            db["test_mode"]["disable_reason"] = text
            save_db()
            update.message.reply_text("✅ پیام غیرفعال تست ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == 'edit_disable_msg':
            db["bot_status"]["disable_message"] = text
            save_db()
            update.message.reply_text("✅ پیام غیرفعال ربات ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == 'set_link':
            db["force_join"]["channel_link"] = text
            if 't.me/' in text:
                username = text.split('t.me/')[-1].split('/')[0].replace('@', '')
                db["force_join"]["channel_username"] = f"@{username}"
                try:
                    chat = context.bot.get_chat(f"@{username}")
                    db["force_join"]["channel_id"] = str(chat.id)
                    update.message.reply_text(f"✅ کانال شناسایی شد: {chat.title}")
                except:
                    update.message.reply_text("⚠️ ربات در کانال ادمین نیست!")
            save_db()
            update.message.reply_text("✅ لینک ذخیره شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        if step == 'broadcast':
            success, fail = 0, 0
            for uid2 in db["users"]:
                try:
                    context.bot.send_message(int(uid2), text)
                    success += 1
                except:
                    fail += 1
            update.message.reply_text(f"✅ ارسال همگانی انجام شد\nموفق: {success}\nناموفق: {fail}")
            add_log("broadcast", uid, f"ارسال همگانی: {text[:50]}...")
            user_data[uid] = {}
            return
        
        # اضافه کردن کانفیگ
        if step == 'add_config':
            add_config(update, context, int(step_data), text)
            user_data[uid] = {}
            return
        
        # ==================== مراحل پلن جدید ====================
        if step == 'new_cat':
            if text == '➕ دسته جدید':
                user_data[uid] = {'step': 'new_cat_name'}
                update.message.reply_text("نام دسته جدید را وارد کنید:", reply_markup=back_btn())
                return
            if text in db["categories"]:
                user_data[uid]['cat'] = text
                user_data[uid]['step'] = 'new_name'
                update.message.reply_text("نام پلن:", reply_markup=back_btn())
            return
        
        if step == 'new_cat_name':
            db["categories"][text] = []
            save_db()
            user_data[uid] = {'cat': text, 'step': 'new_name'}
            update.message.reply_text(f"✅ دسته {text} اضافه شد\nحالا نام پلن را وارد کنید:")
            return
        
        if step == 'new_name':
            user_data[uid]['name'] = text
            user_data[uid]['step'] = 'new_vol'
            update.message.reply_text("حجم (مثال: 50GB):")
            return
        
        if step == 'new_vol':
            user_data[uid]['vol'] = text
            user_data[uid]['step'] = 'new_users'
            update.message.reply_text("تعداد کاربران:")
            return
        
        if step == 'new_users':
            try:
                user_data[uid]['users'] = int(text)
                user_data[uid]['step'] = 'new_days'
                update.message.reply_text("مدت اعتبار (روز):")
            except:
                update.message.reply_text("❌ عدد وارد کنید")
            return
        
        if step == 'new_days':
            try:
                user_data[uid]['days'] = int(text)
                user_data[uid]['step'] = 'new_price'
                update.message.reply_text("قیمت (تومان):")
            except:
                update.message.reply_text("❌ عدد وارد کنید")
            return
        
        if step == 'new_price':
            try:
                price = int(text)
                max_id = 0
                for p in db["categories"].values():
                    for plan in p:
                        if plan["id"] > max_id:
                            max_id = plan["id"]
                new_plan = {
                    "id": max_id + 1,
                    "name": user_data[uid]['name'],
                    "price": price,
                    "volume": user_data[uid]['vol'],
                    "days": user_data[uid]['days'],
                    "users": user_data[uid]['users']
                }
                cat = user_data[uid]['cat']
                db["categories"][cat].append(new_plan)
                save_db()
                update.message.reply_text("✅ پلن اضافه شد", reply_markup=admin_menu())
                add_log("add_plan", uid, f"پلن جدید: {new_plan['name']}")
            except:
                update.message.reply_text("❌ خطا")
            user_data[uid] = {}
            return
        
        # حذف دسته
        if step == 'del_cat' and text in db["categories"]:
            del db["categories"][text]
            save_db()
            update.message.reply_text(f"✅ دسته {text} حذف شد", reply_markup=admin_menu())
            user_data[uid] = {}
            return
        
        # افزودن ادمین
        if step == 'add_admin':
            if text.isdigit():
                ADMINS[text] = "ادمین"
                update.message.reply_text(f"✅ ادمین {text} اضافه شد", reply_markup=admin_menu())
                add_log("add_admin", uid, f"ادمین جدید: {text}")
            else:
                update.message.reply_text("❌ آیدی باید عددی باشد")
            user_data[uid] = {}
            return
        
        # حذف ادمین
        if step == 'del_admin':
            if text == str(ADMIN_ID):
                update.message.reply_text("❌ نمی‌توانید مالک اصلی را حذف کنید")
            elif text in ADMINS:
                del ADMINS[text]
                update.message.reply_text(f"✅ ادمین {text} حذف شد", reply_markup=admin_menu())
            else:
                update.message.reply_text("❌ ادمین یافت نشد")
            user_data[uid] = {}
            return
        
        # نام اکانت برای خرید
        if step == 'wait_account_name':
            temp = user_data[uid].get("temp_purchase", {})
            if temp:
                show_invoice(update, context, temp["plan"], text, temp["payment_method"], temp.get("wallet_paid", False))
                user_data[uid] = {}
            return
        
    except Exception as e:
        logger.error(f"Error in handle_msg: {e}")
        update.message.reply_text("❌ خطا، لطفاً دوباره تلاش کنید")

# ==================== عکس ====================
def handle_photo(update, context):
    try:
        uid = str(update.effective_user.id)
        
        if user_data.get(uid, {}).get('step') == 'restore_backup':
            file = update.message.photo[-1].get_file()
            file.download(f"restore_{uid}.json")
            try:
                with open(f"restore_{uid}.json", 'r', encoding='utf-8') as f:
                    new_db = json.load(f)
                global db
                db = new_db
                save_db()
                update.message.reply_text("✅ بکاپ با موفقیت بازیابی شد", reply_markup=admin_menu())
                add_log("restore_backup", uid, "بازیابی بکاپ")
            except Exception as e:
                update.message.reply_text(f"❌ خطا در بازیابی: {e}")
            finally:
                if os.path.exists(f"restore_{uid}.json"):
                    os.remove(f"restore_{uid}.json")
            user_data[uid] = {}
            return
        
        if user_data.get(uid, {}).get('waiting_receipt') or user_data.get(uid, {}).get('temp_purchase', {}).get('awaiting_receipt'):
            temp = user_data[uid].get("temp_purchase", {})
            if not temp:
                update.message.reply_text("❌ اطلاعات خرید یافت نشد")
                return
            
            plan = temp["plan"]
            account_name = temp.get("account_name", "نامشخص")
            price = plan["price"]
            
            cap = (
                f"💰 فیش جدید\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"👤 {update.effective_user.first_name}\n"
                f"🆔 {uid}\n"
                f"📦 {plan['name']}\n"
                f"👤 اکانت: {account_name}\n"
                f"💰 {price:,} تومان\n"
                f"💳 روش: {temp.get('payment_method', 'کارت')}"
            )
            
            btn = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ تایید", callback_data=f"confirm_receipt_{uid}"),
                    InlineKeyboardButton("❌ رد", callback_data=f"reject_receipt_{uid}")
                ]
            ])
            context.bot.send_photo(
                ADMIN_ID,
                update.message.photo[-1].file_id,
                caption=cap,
                reply_markup=btn
            )
            update.message.reply_text(db["texts"]["receipt_sent"])
            add_log("receipt_sent", uid, f"ارسال فیش برای {plan['name']}")
            # ذخیره موقت اطلاعات فیش
            user_data[uid]["pending_receipt"] = temp
            user_data[uid]["receipt_photo_id"] = update.message.photo[-1].file_id
            user_data[uid] = {}
            return
        
        # افزودن کانفیگ
        if user_data.get(uid, {}).get('step') == 'add_config':
            config_text = update.message.caption or ""
            if config_text:
                plan_id = user_data[uid].get("plan_id")
                add_config(update, context, plan_id, config_text)
                user_data[uid] = {}
            else:
                update.message.reply_text("❌ لطفاً کانفیگ را به همراه توضیحات (کپشن) بفرستید")
        
    except Exception as e:
        logger.error(f"Photo error: {e}")
        update.message.reply_text("❌ خطا در ارسال فیش")

# ==================== کالبک ====================
def handle_callback(update, context):
    try:
        query = update.callback_query
        uid = str(query.from_user.id)
        data = query.data
        query.answer()
        
        # بررسی عضویت
        if data == "join_check":
            if check_join(uid, context):
                query.message.delete()
                welcome = db["texts"]["welcome"].format(brand=db["brand"])
                context.bot.send_message(uid, welcome, reply_markup=main_menu(uid))
            else:
                query.message.reply_text("❌ شما هنوز عضو کانال نشده‌اید!\nلطفاً ابتدا عضو شوید سپس دکمه تایید را بزنید.")
            return
        
        # کیف پول
        if data.startswith("wallet_"):
            if data == "wallet_back":
                query.message.delete()
                start(update, context)
                return
            if data == "wallet_custom":
                user_data[uid] = {'step': 'wallet_custom'}
                query.message.reply_text("💰 مبلغ دلخواه (حداقل 50,000 و حداکثر 5,000,000 تومان) را وارد کنید:", reply_markup=back_btn())
                return
            
            amount = int(data.split("_")[1])
            if amount < 50000 or amount > 5000000:
                query.message.reply_text("❌ مبلغ باید بین 50,000 تا 5,000,000 تومان باشد")
                return
            
            # ذخیره درخواست شارژ
            user_data[uid]["temp_charge"] = amount
            msg = (
                f"💰 درخواست شارژ کیف پول\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"👤 {query.from_user.first_name}\n"
                f"🆔 {uid}\n"
                f"💵 مبلغ: {amount:,} تومان\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"💳 شماره کارت:\n{db['card']['number']}\n"
                f"👤 {db['card']['name']}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"پس از واریز، عکس فیش را بفرستید"
            )
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 ارسال فیش شارژ", callback_data="send_charge_receipt")
            ]])
            query.message.reply_text(msg, reply_markup=btn)
            return
        
        # انتخاب پلن
        if data.startswith("plan_"):
            plan_id = int(data.split("_")[1])
            payment_options(update, plan_id)
            return
        
        # روش پرداخت
        if data.startswith("paymethod_"):
            parts = data.split("_")
            method = parts[1]
            plan_id = int(parts[2])
            
            for cat in db["categories"].values():
                for p in cat:
                    if p["id"] == plan_id:
                        if method == "card":
                            user_data[uid] = {'step': 'wait_account_name'}
                            user_data[uid]["temp_purchase"] = {"plan": p, "payment_method": "card"}
                            query.message.reply_text("📝 لطفاً نام اکانت خود را وارد کنید:")
                        elif method == "wallet":
                            uid_str = str(uid)
                            wallet = db["users"][uid_str].get("wallet", 0)
                            if wallet >= p["price"]:
                                user_data[uid] = {'step': 'wait_account_name'}
                                user_data[uid]["temp_purchase"] = {"plan": p, "payment_method": "wallet", "wallet_paid": True}
                                query.message.reply_text("📝 لطفاً نام اکانت خود را وارد کنید:")
                            else:
                                remaining = p["price"] - wallet
                                query.message.reply_text(
                                    f"❌ موجودی کیف پول شما کافی نیست\n"
                                    f"💰 موجودی: {wallet:,} تومان\n"
                                    f"💵 نیاز: {remaining:,} تومان اضافی\n"
                                    f"لطفاً کیف پول خود را شارژ کنید یا از روش کارت استفاده کنید."
                                )
                        elif method == "mix":
                            user_data[uid] = {'step': 'wait_account_name'}
                            user_data[uid]["temp_purchase"] = {"plan": p, "payment_method": "mix"}
                            query.message.reply_text("📝 لطفاً نام اکانت خود را وارد کنید:")
                        return
        
        # ارسال فیش
        if data == "send_receipt":
            if uid in user_data and "temp_purchase" in user_data[uid]:
                user_data[uid]["waiting_receipt"] = True
                query.message.reply_text("📸 عکس فیش را بفرستید:")
            else:
                query.message.reply_text("❌ اطلاعات خرید یافت نشد")
            return
        
        if data == "send_charge_receipt":
            if uid in user_data and "temp_charge" in user_data[uid]:
                user_data[uid]["waiting_charge_receipt"] = True
                query.message.reply_text("📸 عکس فیش شارژ را بفرستید:")
            else:
                query.message.reply_text("❌ اطلاعات شارژ یافت نشد")
            return
        
        # تمدید
        if data.startswith("renew_"):
            index = int(data.split("_")[1])
            purchases = db["users"][uid].get("purchases", [])
            if index < len(purchases):
                service = purchases[index]
                # پیدا کردن پلن مشابه
                for cat in db["categories"].values():
                    for p in cat:
                        if p['name'] in service or p['volume'] in service:
                            user_data[uid] = {'step': 'wait_account_name'}
                            user_data[uid]["temp_purchase"] = {"plan": p, "payment_method": "card", "is_renew": True}
                            query.message.reply_text(f"📝 تمدید {p['name']}\nلطفاً نام اکانت خود را وارد کنید:")
                            return
                query.message.reply_text("❌ پلن یافت نشد")
            else:
                query.message.reply_text("❌ سرویس یافت نشد")
            return
        
        # تایید فیش
        if data.startswith("confirm_receipt_"):
            if uid not in ADMINS:
                return
            target_uid = data.split("_")[2]
            # اطلاعات از pending
            if target_uid in user_data and "pending_receipt" in user_data.get(target_uid, {}):
                temp = user_data[target_uid]["pending_receipt"]
                plan = temp["plan"]
                account_name = temp.get("account_name", "کاربر")
                
                # کسر از کیف پول اگر ترکیبی بود
                if temp.get("payment_method") == "mix":
                    wallet = db["users"][target_uid].get("wallet", 0)
                    used_wallet = min(wallet, plan["price"])
                    if used_wallet > 0:
                        db["users"][target_uid]["wallet"] = wallet - used_wallet
                        save_db()
                
                if db["auto_send_config"]:
                    send_config_from_pool(update, context, target_uid, plan, account_name)
                else:
                    context.bot.send_message(int(target_uid), db["texts"]["waiting_for_config"])
                    # ذخیره برای ارسال دستی
                    user_data[target_uid] = {"waiting_manual_config": True, "plan": plan, "account_name": account_name}
                    add_log("config_needed", target_uid, f"در انتظار کانفیگ دستی {plan['name']}")
                    context.bot.send_message(ADMIN_ID, f"⚠️ کاربر {target_uid} در انتظار کانفیگ دستی {plan['name']}\nلطفاً کانفیگ را بفرستید.")
                
                add_log("receipt_confirmed", target_uid, f"تایید فیش {plan['name']}")
                query.message.edit_reply_markup(reply_markup=None)
                query.message.reply_text(f"✅ فیش تایید شد\nکاربر {target_uid}")
                
                # پاک کردن pending
                if target_uid in user_data:
                    del user_data[target_uid]["pending_receipt"]
            else:
                query.message.reply_text("❌ اطلاعات فیش یافت نشد")
            return
        
        # رد فیش
        if data.startswith("reject_receipt_"):
            if uid not in ADMINS:
                return
            target_uid = data.split("_")[2]
            user_data[uid] = {'step': 'reject_reason', 'target_uid': target_uid}
            query.message.reply_text("دلیل رد فیش را وارد کنید:")
            return
        
        # افزودن کانفیگ توسط ادمین
        if data.startswith("add_config_"):
            if uid not in ADMINS:
                return
            plan_id = int(data.split("_")[2])
            user_data[uid] = {'step': 'add_config', 'plan_id': plan_id}
            query.message.reply_text("📨 کانفیگ را به همراه توضیحات (کپشن) بفرستید:")
            return
        
        # ویرایش پلن
        if data.startswith("edit_plan_"):
            if uid not in ADMINS:
                return
            plan_id = int(data.split("_")[3])
            for cat, plans in db["categories"].items():
                for p in plans:
                    if p["id"] == plan_id:
                        user_data[uid] = {'step': 'edit_plan', 'plan_id': plan_id, 'cat': cat, 'plan': p}
                        keyboard = [
                            ['نام', 'قیمت'],
                            ['حجم', 'مدت'],
                            ['تعداد کاربران'],
                            ['🔙 انصراف']
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
        
        # ارسال تست
        if data.startswith("send_test_"):
            if uid not in ADMINS:
                return
            target_uid = data.split("_")[2]
            user_data[uid] = {'step': 'send_test_config', 'target_uid': target_uid}
            query.message.reply_text("📨 کانفیگ تست را بفرستید:")
            query.message.edit_reply_markup(reply_markup=None)
            return
        
        # انصراف
        if data == "cancel_pay":
            query.message.reply_text("❌ عملیات خرید لغو شد", reply_markup=main_menu(uid))
            return
        
    except Exception as e:
        logger.error(f"Callback error: {e}")
        query.message.reply_text("❌ خطا")

# ==================== عکس برای شارژ و فیش ====================
def handle_photo_receipt(update, context):
    try:
        uid = str(update.effective_user.id)
        
        # فیش شارژ
        if user_data.get(uid, {}).get("waiting_charge_receipt"):
            amount = user_data[uid].get("temp_charge", 0)
            cap = (
                f"💰 فیش شارژ کیف پول\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"👤 {update.effective_user.first_name}\n"
                f"🆔 {uid}\n"
                f"💵 مبلغ: {amount:,} تومان"
            )
            btn = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ تایید شارژ", callback_data=f"confirm_charge_{uid}"),
                    InlineKeyboardButton("❌ رد", callback_data=f"reject_charge_{uid}")
                ]
            ])
            context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=cap, reply_markup=btn)
            update.message.reply_text("✅ فیش شارژ شما ارسال شد، پس از تایید کیف پول شما شارژ می‌شود")
            user_data[uid]["pending_charge"] = amount
            del user_data[uid]["waiting_charge_receipt"]
            return
        
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
                add_log("wallet_charge", target_uid, f"شارژ کیف پول {amount} تومان")
                query.message.edit_reply_markup(reply_markup=None)
                query.message.reply_text(f"✅ شارژ {target_uid} تایید شد")
                del user_data[target_uid]["pending_charge"]
            return
        
        # رد شارژ
        if data.startswith("reject_charge_"):
            if uid not in ADMINS:
                return
            target_uid = data.split("_")[2]
            user_data[uid] = {'step': 'reject_charge_reason', 'target_uid': target_uid}
            query.message.reply_text("دلیل رد فیش شارژ را وارد کنید:")
            return
            
    except Exception as e:
        logger.error(f"Photo receipt error: {e}")

# ==================== اجرا ====================
def main():
    try:
        logger.info("🚀 Starting bot...")
        
        # وب سرور
        Thread(target=run_web, daemon=True).start()
        
        # ربات
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
        dp.add_handler(MessageHandler(Filters.photo, handle_photo))
        dp.add_handler(CallbackQueryHandler(handle_callback))
        
        updater.start_polling()
        logger.info("✅ Bot is running!")
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == '__main__':
    main()

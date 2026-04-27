import os, json, logging, shutil
from flask import Flask
from threading import Thread
from telegram import *
from telegram.ext import *
from datetime import datetime

# ---------- تنظیمات ----------
TOKEN = "8765075222:AAFT6p_zeYmEcahPoezxtUeqMlsGz0Ra35o"
DB_FILE = "data.json"
ADMINS_DEFAULT = [5993860770]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- وب ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "OK"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# ---------- DB ----------
def load_db():
    if os.path.exists(DB_FILE):
        return json.load(open(DB_FILE,'r',encoding='utf-8'))

    return {
        "users": {},
        "admins": ADMINS_DEFAULT.copy(),
        "bot_enabled": True,
        "test_enabled": True,
        "test_reason": "",
        "wallet_settings":{"amounts":[100000,300000,700000,1500000,2000000]},
        "card":{"number":"0000","name":"NAME"},
        "categories":{
            "VIP":[{"id":1,"name":"20GB","price":80,"volume":"20GB"}]
        },
        "configs":{}
    }

def save():
    json.dump(db,open(DB_FILE,'w',encoding='utf-8'),ensure_ascii=False,indent=2)

db=load_db()
user_data={}

# ---------- utils ----------
def is_admin(uid):
    return int(uid) in db["admins"]

def is_owner(uid):
    return int(uid)==db["admins"][0]

# ---------- menus ----------
def main_menu(uid):
    kb=[['💰 خرید','💳 کیف پول'],['📂 سرویس‌ها','🎁 تست']]
    if is_admin(uid):
        kb.append(['⚙️ مدیریت'])
    return ReplyKeyboardMarkup(kb,resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup([
        ['➕ ادمین','➕ کانفیگ'],
        ['💾 بکاپ','📥 ریستور'],
        ['🔴 خاموش ربات','🟢 روشن ربات'],
        ['🎁 خاموش تست','🎁 روشن تست'],
        ['🔙 برگشت']
    ],resize_keyboard=True)

# ---------- start ----------
def start(update,context):
    uid=str(update.effective_user.id)

    if uid not in db["users"]:
        db["users"][uid]={"wallet":0,"purchases":[],"tests":0}
        save()

    update.message.reply_text("خوش آمدی",reply_markup=main_menu(uid))

# ---------- message ----------
def msg(update,context):
    uid=str(update.effective_user.id)
    text=update.message.text
    step=user_data.get(uid,{}).get("step")

    if not db["bot_enabled"] and not is_admin(uid):
        update.message.reply_text("⛔️ ربات خاموشه")
        return

    # منو
    if text=='🔙 برگشت':
        user_data[uid]={}
        start(update,context)
        return

    # مدیریت
    if text=='⚙️ مدیریت' and is_admin(uid):
        update.message.reply_text("پنل",reply_markup=admin_menu())
        return

    # افزودن ادمین
    if text=='➕ ادمین':
        if not is_owner(uid):
            update.message.reply_text("فقط مالک")
            return
        user_data[uid]={"step":"add_admin"}
        update.message.reply_text("آیدی:")
        return

    if step=="add_admin":
        db["admins"].append(int(text))
        save()
        update.message.reply_text("اضافه شد")
        user_data[uid]={}
        return

    # خاموش/روشن
    if text=='🔴 خاموش ربات':
        db["bot_enabled"]=False
        save()
        update.message.reply_text("خاموش شد")
        return

    if text=='🟢 روشن ربات':
        db["bot_enabled"]=True
        save()
        update.message.reply_text("روشن شد")
        return

    # تست
    if text=='🎁 تست':
        if not db["test_enabled"]:
            update.message.reply_text(f"❌ {db['test_reason']}")
            return
        update.message.reply_text("درخواست ثبت شد")
        db["users"][uid]["tests"]+=1
        save()
        return

    if text=='🎁 خاموش تست':
        user_data[uid]={"step":"test_off"}
        update.message.reply_text("دلیل:")
        return

    if step=="test_off":
        db["test_enabled"]=False
        db["test_reason"]=text
        save()
        update.message.reply_text("خاموش شد")
        user_data[uid]={}
        return

    if text=='🎁 روشن تست':
        db["test_enabled"]=True
        save()
        update.message.reply_text("روشن شد")
        return

    # کیف پول
    if text=='💳 کیف پول':
        bal=db["users"][uid]["wallet"]
        btn=[]
        for a in db["wallet_settings"]["amounts"]:
            btn.append([InlineKeyboardButton(f"{a}",callback_data=f"w_{a}")])
        btn.append([InlineKeyboardButton("دلخواه",callback_data="w_custom")])
        update.message.reply_text(f"موجودی: {bal}",reply_markup=InlineKeyboardMarkup(btn))
        return

    if step=="custom_amount":
        amount=int(text)
        user_data[uid]={"step":"wallet_pay","amount":amount}
        update.message.reply_text(f"واریز {amount}")
        return

    # خرید
    if text=='💰 خرید':
        btn=[]
        for cat in db["categories"].values():
            for p in cat:
                btn.append([InlineKeyboardButton(p["name"],callback_data=f"buy_{p['id']}")])
        update.message.reply_text("پلن:",reply_markup=InlineKeyboardMarkup(btn))
        return

# ---------- photo ----------
def photo(update,context):
    uid=str(update.effective_user.id)

    # شارژ
    if user_data.get(uid,{}).get("step")=="wallet_pay":
        amount=user_data[uid]["amount"]

        btn=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ تایید",callback_data=f"ok_{uid}_{amount}"),
            InlineKeyboardButton("❌ رد",callback_data=f"rej_{uid}")
        ]])

        context.bot.send_photo(db["admins"][0],
            update.message.photo[-1].file_id,
            caption=f"شارژ {amount}",
            reply_markup=btn)

        update.message.reply_text("ارسال شد")
        user_data[uid]={}

# ---------- callback ----------
def cb(update,context):
    q=update.callback_query
    uid=str(q.from_user.id)
    q.answer()

    if q.data.startswith("w_"):
        if q.data=="w_custom":
            user_data[uid]={"step":"custom_amount"}
            q.message.reply_text("مبلغ:")
        else:
            amount=int(q.data.split("_")[1])
            user_data[uid]={"step":"wallet_pay","amount":amount}
            q.message.reply_text(f"واریز {amount}")

    if q.data.startswith("ok_"):
        _,u,a=q.data.split("_")
        db["users"][u]["wallet"]+=int(a)
        save()
        context.bot.send_message(u,"شارژ شد")

# ---------- main ----------
def main():
    Thread(target=run_web).start()

    up=Updater(TOKEN,use_context=True)
    dp=up.dispatcher

    dp.add_handler(CommandHandler("start",start))
    dp.add_handler(MessageHandler(Filters.text,msg))
    dp.add_handler(MessageHandler(Filters.photo,photo))
    dp.add_handler(CallbackQueryHandler(cb))

    up.start_polling()
    up.idle()

if __name__=="__main__":
    main()

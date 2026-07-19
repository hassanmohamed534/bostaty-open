import json
import random
import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

# إعدادات الـ Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# التوكن الخاص ببوت BostatyAiBot
TOKEN = "8999570366:AAFmkoVm_iInNXMZrJqTWJuk_KfRo82KGqQ"

# اسم الملف المحلي اللي هيترفع مع الكود على جيت هوب
LOCAL_JSON_FILE = "bostaty.json"

def load_data():
    categories = {}
    
    if not os.path.exists(LOCAL_JSON_FILE):
        print(f"❌ خطأ: ملف {LOCAL_JSON_FILE} مش موجود في الفولدر!")
        return {"⚠️ تنبيه": [{"txt": "ملف ناقص", "map": "يرجى التأكد من رفع ملف bostaty.json على جيت هوب."}]}
        
    try:
        with open(LOCAL_JSON_FILE, "r", encoding="utf-8") as f:
            full_data = json.load(f)
            
        stories = full_data.get("Stories_page_1", {})
        
        for key, post in stories.items():
            p_type = post.get("type", "عام").strip()
            
            # 🛑 حظر وقص قسم الرعب تماماً
            if "رعب" in p_type or p_type.lower() == "horror":
                continue
                
            if p_type not in categories:
                categories[p_type] = []
            categories[p_type].append(post)
            
        print(f"🚀 تم تحميل كل البوستات من جيت هوب بنجاح! الأقسام: {list(categories.keys())}")
        return categories
    except Exception as e:
        print(f"❌ خطأ قراءة الملف: {str(e)}")
        return {"⚠️ تنبيه": [{"txt": "خطأ داخلي", "map": "حدث خطأ أثناء قراءة البيانات."}]}

CATEGORIES = load_data()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = []
    row = []
    for cat_name in CATEGORIES.keys():
        row.append(InlineKeyboardButton(cat_name, callback_data=f"cat_{cat_name}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_msg = "✨ أهلاً بك في بوت تطبيق بوستاتي (@BostatyAiBot)! ✨\n\nاختر القسم من الأسفل:"
    
    if update.message:
        await update.message.reply_text(welcome_msg, reply_markup=reply_markup)
    else:
        await update.callback_query.message.edit_text(welcome_msg, reply_markup=reply_markup)

async def show_post(query, user_data):
    posts = user_data.get('current_list', [])
    idx = user_data.get('index', 0)
    
    if idx < len(posts):
        current_post = posts[idx]
        title = current_post.get("txt", "")
        content = current_post.get("map", "")
        
        share_text = f"📖 {title}\n\n{content}\n\n🤖 عبر بوت بوستاتي: @BostatyAiBot"
        message_text = f"📖 *{title}*\n\n👇 _اضغط على النص بالأسفل لنسخه مباشرة:_\n`{content}`\n\n✨ مقدم لك من تطبيق بوستاتي"
        
        keyboard = [
            [
                InlineKeyboardButton("➡️ البوست التالي", callback_data="next_post"),
                InlineKeyboardButton("🔗 مشاركة البوست", switch_inline_query=share_text)
            ],
            [InlineKeyboardButton("🗂️ القائمة الرئيسية", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(message_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        keyboard = [[InlineKeyboardButton("🗂️ العودة للأقسام", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(f"🏁 خلصت كل البوستات في قسم ({user_data.get('current_cat')})!", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_data = context.user_data

    if data.startswith("cat_"):
        selected_cat = data.replace("cat_", "")
        shuffled_list = list(CATEGORIES.get(selected_cat, []))
        random.shuffle(shuffled_list)
        user_data['current_list'] = shuffled_list
        user_data['index'] = 0
        user_data['current_cat'] = selected_cat
        await show_post(query, user_data)
    elif data == "next_post":
        if 'index' in user_data:
            user_data['index'] += 1
            await show_post(query, user_data)
    elif data == "main_menu":
        await start(update, context)

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

import os
import img2pdf
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI  # Yangi kutubxona

# Tokenlar va Kalitlar
TOKEN = "8855597606:AAGSj6mfjkFWxZgZ_c8SGg9QwSO46ZAroeA"
OPENAI_API_KEY = "BU_YERGA_OPENAI_KALITINI_QO'YING"  # sk-proj-... kalitingizni qo'ying
KANAL_ID = -1003916136926  
KANAL_LINK = "https://t.me/talabalar_uqtuvchilar" 

# Obyektlarni ishga tushiramiz
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
ai_client = OpenAI(api_key=OPENAI_API_KEY)  # ChatGPT mijozini yaratamiz

user_photos = {}

if not os.path.exists("yuklanganlar"):
    os.makedirs("yuklanganlar")

# Kanalga a'zolikni tekshirish
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=KANAL_ID, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
        return False
    except Exception as e:
        print(f"Tekshirishda xatolik: {e}")
        return False

def get_sub_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    btn_link = InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=KANAL_LINK)
    btn_check = InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")
    keyboard.add(btn_link, btn_check)
    return keyboard

def get_convert_keyboard():
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text="📄 Barcha rasmlarni bitta PDF qilish", callback_data="convert_to_pdf")
    keyboard.add(button)
    return keyboard

@dp.message_handler(commands=['start'])
async def start_buyrugi(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_sub(user_id)
    if not is_subscribed:
        await message.answer("🛑 Botdan foydalanishdan oldin homiy kanalimizga a'zo bo'lishingiz kerak!", reply_markup=get_sub_keyboard())
        return

    user_photos[user_id] = []
    await message.answer("Salom! Menga rasm yuborsangiz PDF qilib beraman. 📄\nSavol yozsangiz, ChatGPT orqali javob beraman! 🤖")

@dp.message_handler(content_types=['photo'])
async def rasm_qabul_qilish(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_sub(user_id)
    if not is_subscribed:
        await message.answer("🛑 Botdan foydalanish uchun kanalimizga a'zo bo'lishingiz shart!", reply_markup=get_sub_keyboard())
        return

    if user_id not in user_photos:
        user_photos[user_id] = []
        
    rasm = message.photo[-1]
    file_info = await bot.get_file(rasm.file_id)
    rasm_nomi = f"yuklanganlar/{rasm.file_id}.jpg"
    await bot.download_file(file_info.file_path, rasm_nomi)
    
    user_photos[user_id].append(rasm_nomi)
    rasmlar_soni = len(user_photos[user_id])
    await message.answer(f"Rasm qabul qilindi! Olingan rasmlar: {rasmlar_soni} ta.", reply_markup=get_convert_keyboard())

# 🌐 CHATGPT SHU YERDA ISHLAYDI: Foydalanuvchi matn yozganda javob berish
@dp.message_handler(content_types=['text'])
async def chatgpt_javob(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_sub(user_id)
    if not is_subscribed:
        await message.answer("🛑 Botdan foydalanish uchun kanalimizga a'zo bo'lishingiz shart!", reply_markup=get_sub_keyboard())
        return

    kutish_xabari = await message.answer("🤔 O'ylayapman, iltimos kuting...")

    try:
        # ChatGPT modeliga so'rov yuborish (gpt-4o-mini yoki gpt-3.5-turbo)
        response = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Siz maktab o'qituvchilari va talabalarga yordam beradigan aqlli va muloyim bot hisoblanasiz."},
                {"role": "user", "content": message.text}
            ]
        )
        # Kelgan javobni olish
        javob_matni = response.choices[0].message.content
        
        # "O'ylayapman" degan yozuvni o'chirib, o'rniga ChatGPT javobini yozish
        await kutish_xabari.edit_text(javob_matni)

    except Exception as xato:
        await kutish_xabari.edit_text(f"Kechirasiz, javob qidirishda xatolik yuz berdi: {xato}")

@dp.callback_query_handler(lambda call: call.data == "check_subscription")
async def check_sub_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    is_subscribed = await check_sub(user_id)
    if is_subscribed:
        user_photos[user_id] = []
        try:
            await call.message.delete()
        except:
            pass
        await call.message.answer("Rahmat! Obuna tasdiqlandi. ✅\nEndi menga rasmlar yoki savollaringizni yuborishingiz mumkin.")
    else:
        await call.answer("Siz hali kanalga a'zo bo'lmadingiz! ❌", show_alert=True)

@dp.callback_query_handler(lambda call: call.data == "convert_to_pdf")
async def pdf_ga_aylantirish(call: types.CallbackQuery):
    user_id = call.from_user.id
    is_subscribed = await check_sub(user_id)
    if not is_subscribed:
        await call.message.answer("🛑 Botdan foydalanish uchun kanalga a'zo bo'ling:", reply_markup=get_sub_keyboard())
        await call.answer()
        return

    if user_id not in user_photos or len(user_photos[user_id]) == 0:
        await call.answer("Siz hali rasm yubormadingiz!", show_alert=True)
        return
        
    await call.message.answer("Rasmlar qayta ishlanmoqda, iltimos kuting...")
    pdf_nomi = f"yuklanganlar/fayl_{user_id}.pdf"
    
    try:
        with open(pdf_nomi, "wb") as f:
            f.write(img2pdf.convert(user_photos[user_id]))
            
        with open(pdf_nomi, "rb") as tayyor_pdf:
            await call.message.reply_document(tayyor_pdf, caption="Siz yuborgan barcha rasmlardan tuzilgan PDF tayyor! ✅")
            
        for rasm_path in user_photos[user_id]:
            if os.path.exists(rasm_path):
                os.remove(rasm_path)
        user_photos[user_id] = []
        
    except Exception as xato:
        await call.message.answer(f"Xatolik yuz berdi: {xato}")
    finally:
        if os.path.exists(pdf_nomi):
            os.remove(pdf_nomi)
    await call.answer()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
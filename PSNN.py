import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import openpyxl
from openpyxl import Workbook

# ----------------- SOZLAMALAR -----------------
TOKEN = "8759018218:AAGtg9ubVWVPZCX5p9UceIJX74rPJNWfRLo"
ADMIN_ID = 1927837495

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

EXCEL_FILE = "orders.xlsx"

# Excel fayli mavjudligini tekshirish va yaratish
if not os.path.exists(EXCEL_FILE):
    wb = Workbook()
    ws = wb.active
    ws.title = "Buyurtmalar"
    ws.append(["Ism", "Region", "Email", "Nickname", "Telegram"])
    wb.save(EXCEL_FILE)


# ----------------- FSM (HOLATLAR) -----------------
class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_region = State()
    waiting_for_email = State()
    waiting_for_nickname = State()
    waiting_for_username = State()


# ----------------- KLAVIATURALAR -----------------
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Zakaz berish")],
            [KeyboardButton(text="Narxlar bilan tanishish"), KeyboardButton(text="Admin")]
        ],
        resize_keyboard=True
    )

def get_regions_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="TR"), KeyboardButton(text="USA"), KeyboardButton(text="EU")],
            [KeyboardButton(text="JP"), KeyboardButton(text="KR"), KeyboardButton(text="RU")],
            [KeyboardButton(text="Steam")]
        ],
        resize_keyboard=True
    )


# ----------------- START KOMANDASI -----------------
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Salom! PSN/Steam akkauntlari uchun buyurtma berish botiga xush kelibsiz.",
        reply_markup=get_main_menu()
    )


# ----------------- NARXLAR BILAN TANISHISH -----------------
@dp.message(F.text == "Narxlar bilan tanishish")
async def show_prices(message: types.Message):
    prices_text = (
        "💰 **Akkaunt yaratib berish narxlari:**\n\n"
        "🎮 **PlayStation (PS4/PS5):**\n"
        "• TR (Turkiya) — 80.000 so'm\n"
        "• USA (Amerika) — 50.000 so'm\n"
        "• EU (Yevropa) — 60.000 so'm\n"
        "• JP (Yaponiya) — 65.000 so'm\n"
        "• KR (Koreya) — 80.000 so'm\n"
        "• RU (Rossiya) — 50.000 so'm\n\n"
        "🖥️ **Steam:**\n"
        "• Steam akkaunt yaratish — 40.000 so'm\n\n"
        "✨ _Buyurtma berish uchun 'Zakaz berish' tugmasini bosing._"
    )
    await message.answer(prices_text, parse_mode="Markdown")


# ----------------- ADMIN TUGMASI -----------------
@dp.message(F.text == "Admin")
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        if os.path.exists(EXCEL_FILE):
            file = types.FSInputFile(EXCEL_FILE)
            await message.answer_document(file, caption="Barcha buyurtmalar bazasi.")
        else:
            await message.answer("Hozircha buyurtmalar fayli yo'q.")
    else:
        await message.answer("Siz admin emassiz!")


# ----------------- ZAKAZ BERISH JARAYONI -----------------
@dp.message(F.text == "Zakaz berish")
async def start_order(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(OrderState.waiting_for_name)
    await message.answer("Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())


@dp.message(OrderState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(OrderState.waiting_for_region)
    await message.answer("Regionni yoki Steam xizmatini tanlang:", reply_markup=get_regions_menu())


@dp.message(OrderState.waiting_for_region)
async def process_region(message: types.Message, state: FSMContext):
    regions = ["TR", "USA", "EU", "JP", "KR", "RU", "Steam"]
    if message.text not in regions:
        await message.answer("Iltimos, pastdagi tugmalardan birini bosing:")
        return

    await state.update_data(region=message.text)
    await state.set_state(OrderState.waiting_for_email)
    await message.answer("Email manzilingizni kiriting:", reply_markup=ReplyKeyboardRemove())


@dp.message(OrderState.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await state.set_state(OrderState.waiting_for_nickname)
    await message.answer("Akkaunt uchun xohlagan Nickname kiriting:")


@dp.message(OrderState.waiting_for_nickname)
async def process_nickname(message: types.Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await state.set_state(OrderState.waiting_for_username)

    tg_user = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    await message.answer(
        f"Telegram username kiriting.\n(Nusxalash uchun: `{tg_user}`)",
        parse_mode="Markdown"
    )


@dp.message(OrderState.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)

    data = await state.get_data()
    name = data.get('name')
    region = data.get('region')
    email = data.get('email')
    nickname = data.get('nickname')
    username = data.get('username')

    # Excelga yozish
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        ws = wb.active
        ws.append([name, region, email, nickname, username])
        wb.save(EXCEL_FILE)
    except Exception as e:
        logging.error(f"Excel xatosi: {e}")

        # Adminga xabar yuborish
        admin_text = (
    f"🔔 **YANGI ZAKAZ!**\n\n"
    f"👤 **Ism:** {name}\n"
    f"🌍 **Platforma/Region:** {region}\n"
    f"📧 **Email:** {email}\n"
    f"🎮 **Nickname:** {nickname}\n"
    f"✈️ **Telegram:** {username}"
    )

    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Adminga xabar ketmadi: {e}")

    await message.answer("Rahmat! Buyurtmangiz qabul qilindi. Tez orada admin siz bilan bog'lanadi.",
                         reply_markup=get_main_menu())
    await state.clear()


# ----------------- ISHGA TUSHIRISH -----------------
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
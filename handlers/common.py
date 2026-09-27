from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
from states import Registration
from utils import user_link

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)

    # Telegram profili (tg_id) bazada bo'lsa — botni har doim tanib oladi,
    # ismini, telefonini va rolini qayta so'ramaydi.
    if user and user["role"] and user["phone"]:
        if user["role"] == "driver" and not user["car_brand"]:
            # Ro'yxatdan o'tgan, lekin mashina profili hali to'ldirilmagan
            await message.answer(f"Xush kelibsiz, {user['full_name']}! Avval mashina profilingizni to'ldiramiz.")
            from handlers.driver import start_car_profile
            await start_car_profile(message, state)
            return
        await show_main_menu(message, user["role"])
        return

    await message.answer(
        "Assalomu alaykum! <b>7075.uz</b> — taksi va yo'lovchilarni bog'laydigan botga xush kelibsiz.\n\n"
        "Kim sifatida davom etasiz?",
        reply_markup=kb.role_kb(),
    )
    await state.set_state(Registration.role)


@router.callback_query(Registration.role, F.data.startswith("role:"))
async def choose_role(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split(":")[1]  # driver / client
    await state.update_data(role=role)
    await callback.message.edit_text("Ismingizni kiriting:")
    await state.set_state(Registration.name)
    await callback.answer()


@router.message(Registration.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await message.answer(
        "Endi telefon raqamingizni yuboring 👇",
        reply_markup=kb.phone_kb(),
    )
    await state.set_state(Registration.phone)


@router.message(Registration.phone, F.contact)
async def get_phone_contact(message: Message, state: FSMContext):
    await finish_registration(message, state, message.contact.phone_number)


@router.message(Registration.phone, F.text)
async def get_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not phone.replace("+", "").isdigit() or len(phone) < 9:
        await message.answer("Raqam noto'g'ri. Masalan: +998901234567 yoki tugmadan foydalaning.")
        return
    await finish_registration(message, state, phone)


async def finish_registration(message: Message, state: FSMContext, phone: str):
    data = await state.get_data()
    await db.create_or_update_user(
        tg_id=message.from_user.id,
        role=data["role"],
        full_name=data["full_name"],
        phone=phone,
        username=message.from_user.username,
    )
    await state.clear()
    await message.answer("✅ Ro'yxatdan o'tish yakunlandi!")

    if data["role"] == "driver":
        # Taksichilar uchun endi mashina profili so'raladi (bir martalik)
        from handlers.driver import start_car_profile
        await start_car_profile(message, state)
    else:
        await show_main_menu(message, data["role"])


@router.message(F.text == "🏆 Faol haydovchilar")
async def top_drivers(message: Message):
    drivers = await db.get_top_drivers(10)
    if not drivers:
        await message.answer("Hozircha yakunlangan safarlar yo'q. Birinchi bo'lib safar qiling! 🚖")
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = ["<b>🏆 Eng faol haydovchilar reytingi</b>\n"]
    for i, d in enumerate(drivers):
        rank = medals[i] if i < 3 else f"{i + 1}."
        lines.append(
            f"{rank} <b>{d['full_name']}</b> — {d['trips']} ta yakunlangan safar\n"
            f"    🔗 {user_link(d)}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user or not user["role"]:
        await message.answer("Avval ro'yxatdan o'tishingiz kerak. /start ni bosing.")
        return
    await show_main_menu(message, user["role"])


@router.message(Command("reyting"))
async def cmd_reyting(message: Message):
    await top_drivers(message)


@router.message(Command("elonlar"))
async def cmd_elonlar(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user or not user["role"]:
        await message.answer("Avval ro'yxatdan o'tishingiz kerak. /start ni bosing.")
        return

    # Doiraviy import'dan qochish uchun funksiyalar shu yerda chaqiriladi
    if user["role"] == "client":
        from handlers.client import browse_start
        await browse_start(message, state)
    else:
        from handlers.driver import my_announcements
        await my_announcements(message)


@router.message(Command("yordam"))
async def cmd_yordam(message: Message):
    await message.answer(
        "ℹ️ <b>7075.uz</b> — taksi va yo'lovchilarni bog'lovchi bot.\n\n"
        "🚖 <b>Taksichi</b>: yo'nalish, sana, mashina turi va joylar sonini ko'rsatib e'lon bering.\n"
        "🧍 <b>Yo'lovchi</b>: mos e'lonni tanlang, garov puli to'lab joy band qiling.\n\n"
        "Buyruqlar:\n"
        "/menu — asosiy menyu\n"
        "/elonlar — faol e'lonlar\n"
        "/reyting — faol haydovchilar\n\n"
        "Savollar bo'yicha: @your_admin_username"
    )


async def show_main_menu(message: Message, role: str):
    if role == "driver":
        await message.answer(
            "🚖 Taksichi menyusi. Kerakli bo'limni tanlang:",
            reply_markup=kb.driver_menu_kb(),
        )
    else:
        await message.answer(
            "🧍 Yo'lovchi menyusi. Kerakli bo'limni tanlang:",
            reply_markup=kb.client_menu_kb(),
        )

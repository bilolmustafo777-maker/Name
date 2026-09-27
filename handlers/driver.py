from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
from states import DriverAnnouncement, DriverProfile
from utils import user_contact_text

router = Router()


def format_announcement(ann, driver=None) -> str:
    text = (
        f"🚖 <b>E'lon #{ann['id']}</b>\n"
        f"📍 {ann['from_city']} ➜ {ann['to_city']}\n"
        f"🗓 Sana: {ann['trip_date']}\n"
        f"🚗 Mashina: {ann['car_type']}\n"
        f"💺 Bo'sh joylar: {ann['available_seats']}/{ann['total_seats']}\n"
        f"📌 Holat: {'✅ Faol' if ann['status'] == 'active' else '⛔️ Yopilgan'}"
    )
    if driver:
        text += f"\n👤 Haydovchi: {driver['full_name']}"
        if driver["plate_number"]:
            text += f"\n🔢 Davlat raqami: {driver['plate_number']}"
        luggage_text = "bor ✅" if driver["has_luggage"] else "yo'q ❌"
        parcel_text = "qabul qilinadi ✅" if driver["takes_parcel"] else "qabul qilinmaydi ❌"
        text += f"\n🧳 Bagaj: {luggage_text}"
        text += f"\n📦 Pochta/posilka: {parcel_text}"
    return text


# =========================================================
#   MASHINA PROFILI — bir marta to'ldiriladi, doim saqlanadi
# =========================================================

async def start_car_profile(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🚗 Endi mashinangiz haqida ma'lumot to'ldiramiz.\n"
        "Bu faqat bir marta so'raladi va keyingi barcha e'lonlaringizda avtomatik ishlatiladi.\n\n"
        "Mashina rusumini tanlang:",
        reply_markup=kb.car_kb(),
    )
    await state.set_state(DriverProfile.car_brand)


@router.message(F.text == "⚙️ Mashina profilim")
async def edit_car_profile(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user or user["role"] != "driver":
        await message.answer("Bu bo'lim faqat taksichilar uchun.")
        return
    await start_car_profile(message, state)


@router.callback_query(DriverProfile.car_brand, F.data.startswith("car:"))
async def profile_car_brand(callback: CallbackQuery, state: FSMContext):
    car = callback.data.split(":")[1]
    await state.update_data(car_brand=car)
    await callback.message.edit_text(
        f"Mashina: <b>{car}</b>\n\n"
        f"Mashinangiz rasmini yuboring (ixtiyoriy).\n"
        f"O'tkazib yuborish uchun /skip deb yozing."
    )
    await state.set_state(DriverProfile.car_photo)
    await callback.answer()


@router.message(DriverProfile.car_photo, F.photo)
async def profile_car_photo(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(car_photo=file_id)
    await _ask_plate_number(message, state)


@router.message(DriverProfile.car_photo, Command("skip"))
async def profile_car_photo_skip(message: Message, state: FSMContext):
    await _ask_plate_number(message, state)


@router.message(DriverProfile.car_photo)
async def profile_car_photo_invalid(message: Message, state: FSMContext):
    await message.answer("Iltimos, mashina rasmini (foto) yuboring yoki /skip deb yozing.")


async def _ask_plate_number(message: Message, state: FSMContext):
    await message.answer(
        "Mashina davlat raqamini kiriting (masalan: 01 A 123 BC).\n"
        "Ixtiyoriy — o'tkazib yuborish uchun /skip deb yozing."
    )
    await state.set_state(DriverProfile.plate_number)


@router.message(DriverProfile.plate_number, Command("skip"))
async def profile_plate_skip(message: Message, state: FSMContext):
    await _ask_luggage(message, state)


@router.message(DriverProfile.plate_number, F.text)
async def profile_plate_text(message: Message, state: FSMContext):
    await state.update_data(plate_number=message.text.strip())
    await _ask_luggage(message, state)


async def _ask_luggage(message: Message, state: FSMContext):
    await message.answer(
        "Mashinangizda yo'lovchilar uchun bagaj (yuk xaltasi/chamadon) joyi bormi?",
        reply_markup=kb.yes_no_kb("luggage"),
    )
    await state.set_state(DriverProfile.luggage)


@router.callback_query(DriverProfile.luggage, F.data.startswith("luggage:"))
async def profile_luggage(callback: CallbackQuery, state: FSMContext):
    val = int(callback.data.split(":")[1])
    await state.update_data(has_luggage=val)
    await callback.message.edit_text(
        "Pochta / kichik yuk-posilka olib yura olasizmi?",
        reply_markup=kb.yes_no_kb("parcel"),
    )
    await state.set_state(DriverProfile.parcel)
    await callback.answer()


@router.callback_query(DriverProfile.parcel, F.data.startswith("parcel:"))
async def profile_parcel(callback: CallbackQuery, state: FSMContext):
    val = int(callback.data.split(":")[1])
    data = await state.get_data()

    await db.create_or_update_user(
        tg_id=callback.from_user.id,
        car_brand=data.get("car_brand"),
        car_photo=data.get("car_photo"),
        plate_number=data.get("plate_number"),
        has_luggage=data.get("has_luggage", 0),
        takes_parcel=val,
    )
    await state.clear()
    await callback.message.edit_text("✅ Mashina profilingiz saqlandi!")

    from handlers.common import show_main_menu
    await show_main_menu(callback.message, "driver")
    await callback.answer()


# =========================================================
#              E'LON BERISH (endi qisqartirilgan)
# =========================================================

@router.message(F.text == "🆕 Yangi e'lon berish")
async def new_announcement(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user or user["role"] != "driver":
        await message.answer(
            "Bu bo'lim faqat ro'yxatdan o'tgan taksichilar uchun.\n"
            "Avval /start bosing va \"🚖 Men taksichiman\" ni tanlang."
        )
        return
    if not user["car_brand"]:
        await message.answer("Avval mashina profilingizni to'ldiring.")
        await start_car_profile(message, state)
        return

    await state.clear()
    quick = (user["last_from"], user["last_to"]) if user["last_from"] and user["last_to"] else None
    await message.answer(
        "Qayerdan yo'lga chiqasiz?",
        reply_markup=kb.cities_kb("from", quick_route=quick),
    )
    await state.set_state(DriverAnnouncement.from_city)


@router.callback_query(DriverAnnouncement.from_city, F.data == "quickroute:1")
async def use_quick_route(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    await state.update_data(from_city=user["last_from"], to_city=user["last_to"])
    await callback.message.edit_text(
        f"📍 {user['last_from']} ➜ {user['last_to']}\n\nQachon jo'nab ketasiz?",
        reply_markup=kb.date_kb(),
    )
    await state.set_state(DriverAnnouncement.date_choice)
    await callback.answer()


@router.callback_query(DriverAnnouncement.from_city, F.data.startswith("from:"))
async def set_from_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split(":")[1]
    await state.update_data(from_city=city)
    await callback.message.edit_text(
        f"Qayerdan: <b>{city}</b>\n\nQayerga borasiz?",
        reply_markup=kb.cities_kb("to", exclude=city),
    )
    await state.set_state(DriverAnnouncement.to_city)
    await callback.answer()


@router.callback_query(DriverAnnouncement.to_city, F.data.startswith("to:"))
async def set_to_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split(":")[1]
    await state.update_data(to_city=city)
    await callback.message.edit_text(
        f"Qayerga: <b>{city}</b>\n\nQachon jo'nab ketasiz?",
        reply_markup=kb.date_kb(),
    )
    await state.set_state(DriverAnnouncement.date_choice)
    await callback.answer()


@router.callback_query(DriverAnnouncement.date_choice, F.data.startswith("date:"))
async def set_date(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]
    if choice == "today":
        trip_date = datetime.now().strftime("%d.%m.%Y") + " (Bugun)"
    elif choice == "tomorrow":
        trip_date = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y") + " (Ertaga)"
    else:
        await callback.message.edit_text("Sanani kiriting (masalan: 25.10.2026):")
        await state.set_state(DriverAnnouncement.custom_date)
        await callback.answer()
        return

    await state.update_data(trip_date=trip_date)
    await callback.message.edit_text(
        f"Sana: <b>{trip_date}</b>\n\nNechta bo'sh joy bor? (1-4)",
        reply_markup=kb.seats_kb(),
    )
    await state.set_state(DriverAnnouncement.seats)
    await callback.answer()


@router.message(DriverAnnouncement.custom_date)
async def set_custom_date(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text.strip(), "%d.%m.%Y")
    except ValueError:
        await message.answer("Format noto'g'ri. Masalan: 25.10.2026")
        return
    await state.update_data(trip_date=message.text.strip())
    await message.answer("Nechta bo'sh joy bor? (1-4)", reply_markup=kb.seats_kb())
    await state.set_state(DriverAnnouncement.seats)


@router.callback_query(DriverAnnouncement.seats, F.data.startswith("seats:"))
async def set_seats(callback: CallbackQuery, state: FSMContext):
    seats = int(callback.data.split(":")[1])
    await state.update_data(seats=seats)
    data = await state.get_data()
    user = await db.get_user(callback.from_user.id)

    luggage_text = "bor" if user["has_luggage"] else "yo'q"
    parcel_text = "qabul qilinadi" if user["takes_parcel"] else "yo'q"
    preview = (
        f"📍 {data['from_city']} ➜ {data['to_city']}\n"
        f"🗓 {data['trip_date']}\n"
        f"🚗 {user['car_brand']}"
        + (f" | 🔢 {user['plate_number']}" if user["plate_number"] else "")
        + f"\n💺 {seats} ta bo'sh joy\n"
        f"🧳 Bagaj: {luggage_text}\n"
        f"📦 Pochta: {parcel_text}\n\n"
        f"E'lonni joylashtiraymi?"
    )
    await callback.message.edit_text(preview, reply_markup=kb.confirm_kb())
    await state.set_state(DriverAnnouncement.confirm)
    await callback.answer()


@router.callback_query(DriverAnnouncement.confirm, F.data == "confirm_ann:yes")
async def confirm_announcement(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await db.get_user(callback.from_user.id)

    ann_id = await db.create_announcement(
        driver_id=callback.from_user.id,
        from_city=data["from_city"],
        to_city=data["to_city"],
        trip_date=data["trip_date"],
        car_type=user["car_brand"],
        seats=data["seats"],
    )
    # Keyingi safar uchun yo'nalishni "so'nggi yo'nalish" sifatida saqlaymiz
    await db.create_or_update_user(
        tg_id=callback.from_user.id,
        last_from=data["from_city"],
        last_to=data["to_city"],
    )

    ann = await db.get_announcement(ann_id)
    updated_user = await db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        "✅ E'lon muvaffaqiyatli joylashtirildi!\n\n" + format_announcement(ann, updated_user)
    )
    await state.clear()
    await callback.answer()


@router.callback_query(DriverAnnouncement.confirm, F.data == "confirm_ann:no")
async def cancel_announcement(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Bekor qilindi.")
    await state.clear()
    await callback.answer()


@router.message(F.text == "📋 Mening e'lonlarim")
async def my_announcements(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or user["role"] != "driver":
        return
    anns = await db.get_driver_announcements(message.from_user.id)
    if not anns:
        await message.answer("Sizda hali e'lonlar yo'q.")
        return
    for ann in anns:
        await message.answer(format_announcement(ann))


# ---------------- Yo'lovchi so'rovlariga javob (haydovchi tomondan) ----------------

@router.callback_query(F.data.startswith("driver_accept:"))
async def driver_accept(callback: CallbackQuery):
    booking_id = int(callback.data.split(":")[1])
    booking = await db.get_booking(booking_id)
    if not booking or booking["status"] != "waiting_driver":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    ann = await db.get_announcement(booking["announcement_id"])
    await db.decrease_seats(ann["id"], booking["seats"])
    await db.set_booking_status(booking_id, "confirmed")

    driver = await db.get_user(callback.from_user.id)
    client = await db.get_user(booking["client_id"])

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Siz ushbu so'rovni qabul qildingiz."
    )
    await callback.bot.send_message(
        client["tg_id"],
        f"🎉 Haydovchi so'rovingizni tasdiqladi!\n\n"
        f"{user_contact_text(driver)}\n\n"
        f"Aloqaga chiqib, safar tafsilotlarini kelishib oling.",
    )
    await callback.bot.send_message(
        driver["tg_id"],
        f"📞 Yo'lovchi kontakti:\n\n{user_contact_text(client)}",
    )

    updated_ann = await db.get_announcement(ann["id"])
    if updated_ann["status"] == "closed":
        await callback.bot.send_message(
            driver["tg_id"],
            f"ℹ️ E'lon #{ann['id']} bo'yicha barcha joylar band bo'ldi, e'lon taxtadan olindi.",
        )
    await callback.answer("Qabul qilindi ✅")


@router.callback_query(F.data.startswith("driver_reject:"))
async def driver_reject(callback: CallbackQuery):
    booking_id = int(callback.data.split(":")[1])
    booking = await db.get_booking(booking_id)
    if not booking or booking["status"] != "waiting_driver":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.set_booking_status(booking_id, "rejected")
    client = await db.get_user(booking["client_id"])

    await callback.message.edit_text(callback.message.text + "\n\n❌ Siz ushbu so'rovni rad etdingiz.")
    await callback.bot.send_message(
        client["tg_id"],
        "😔 Haydovchi so'rovingizni rad etdi. Boshqa e'lonlardan tanlashingiz mumkin.\n"
        "Garov puli qaytarilishi administrator bilan alohida tartibga solinadi (v1.0'da qo'lda).",
    )
    await callback.answer("Rad etildi")

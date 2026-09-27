from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import database as db
import keyboards as kb
from handlers.driver import format_announcement
from payments import generate_payment_link
from states import ClientBooking, ClientBrowse

router = Router()

STATUS_MAP = {
    "pending_payment": "⏳ To'lov kutilmoqda",
    "waiting_driver": "⏳ Haydovchi javobini kutmoqda",
    "confirmed": "✅ Tasdiqlangan",
    "rejected": "❌ Rad etilgan",
    "cancelled": "❌ Bekor qilingan",
}


@router.message(F.text == "🔍 E'lonlarni ko'rish")
async def browse_start(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user or user["role"] != "client":
        await message.answer(
            "Bu bo'lim faqat ro'yxatdan o'tgan yo'lovchilar uchun.\n"
            "Avval /start bosing va \"🧍 Men yo'lovchiman\" ni tanlang."
        )
        return
    await state.clear()
    await message.answer(
        "Qayerdan e'lonlarni qidiramiz?",
        reply_markup=kb.cities_kb("bf", with_all=True),
    )
    await state.set_state(ClientBrowse.filter_from)


@router.callback_query(ClientBrowse.filter_from, F.data.startswith("bf:"))
async def browse_from(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split(":")[1]
    await state.update_data(from_city=city)
    await callback.message.edit_text(
        f"Qayerdan: <b>{city}</b>\n\nQayerga?",
        reply_markup=kb.cities_kb("bt", exclude=None if city == "Barchasi" else city, with_all=True),
    )
    await state.set_state(ClientBrowse.filter_to)
    await callback.answer()


@router.callback_query(ClientBrowse.filter_to, F.data.startswith("bt:"))
async def browse_to(callback: CallbackQuery, state: FSMContext):
    to_city = callback.data.split(":")[1]
    data = await state.get_data()
    from_city = data.get("from_city")

    anns = await db.find_announcements(from_city, to_city)
    await callback.message.edit_text(f"🔎 Natijalar: {from_city} ➜ {to_city}")
    await state.clear()

    if not anns:
        await callback.message.answer("Hozircha mos e'lon topilmadi. Keyinroq urinib ko'ring.")
        await callback.answer()
        return

    for ann in anns:
        driver = await db.get_user(ann["driver_id"])
        text = format_announcement(ann, driver)
        if driver["car_photo"]:
            await callback.message.answer_photo(
                driver["car_photo"], caption=text, reply_markup=kb.book_kb(ann["id"])
            )
        else:
            await callback.message.answer(text, reply_markup=kb.book_kb(ann["id"]))
    await callback.answer()


@router.callback_query(F.data.startswith("book:"))
async def book_start(callback: CallbackQuery, state: FSMContext):
    ann_id = int(callback.data.split(":")[1])
    ann = await db.get_announcement(ann_id)
    if not ann or ann["status"] != "active" or ann["available_seats"] <= 0:
        await callback.answer("Kechirasiz, bu e'lon endi mavjud emas.", show_alert=True)
        return

    await state.update_data(announcement_id=ann_id)
    max_seats = min(ann["available_seats"], 4)
    await callback.message.answer(
        "Nechta joy band qilmoqchisiz?",
        reply_markup=kb.seats_kb(prefix="bseats", max_seats=max_seats),
    )
    await state.set_state(ClientBooking.seats)
    await callback.answer()


@router.callback_query(ClientBooking.seats, F.data.startswith("bseats:"))
async def book_seats(callback: CallbackQuery, state: FSMContext):
    seats = int(callback.data.split(":")[1])
    data = await state.get_data()
    ann = await db.get_announcement(data["announcement_id"])

    if not ann or ann["available_seats"] < seats:
        await callback.message.edit_text("Kechirasiz, joylar soni yetarli emas.")
        await state.clear()
        await callback.answer()
        return

    booking_id = await db.create_booking(ann["id"], callback.from_user.id, seats)
    await state.clear()

    amount_str = f"{config.DEPOSIT_AMOUNT:,}".replace(",", " ")
    await callback.message.edit_text(
        f"💺 {seats} ta joy tanlandi.\n\n"
        f"Joyni band qilish uchun <b>{amount_str} so'm</b> garov puli to'lanishi kerak.\n"
        f"To'lov usulini tanlang:",
        reply_markup=kb.payment_kb(booking_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay:"))
async def choose_payment(callback: CallbackQuery):
    _, method, booking_id = callback.data.split(":")
    booking_id = int(booking_id)
    link = generate_payment_link(method, config.DEPOSIT_AMOUNT, booking_id)
    amount_str = f"{config.DEPOSIT_AMOUNT:,}".replace(",", " ")

    await callback.message.edit_text(
        f"💳 To'lov: <b>{amount_str} so'm</b>\n"
        f"Havola: {link}\n\n"
        f"⚠️ v1.0 test rejimi: {method.capitalize()} bilan haqiqiy to'lov localhost'da ishlamaydi "
        f"(webhook uchun ochiq HTTPS server kerak bo'ladi). Hozircha to'lovni tasdiqlash "
        f"uchun quyidagi tugmani bosing.",
        reply_markup=kb.payment_confirm_kb(booking_id, method),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_confirm:"))
async def confirm_payment(callback: CallbackQuery):
    _, method, booking_id = callback.data.split(":")
    booking_id = int(booking_id)
    booking = await db.get_booking(booking_id)
    if not booking or booking["payment_status"] == "paid":
        await callback.answer("Bu to'lov allaqachon tasdiqlangan.", show_alert=True)
        return

    await db.set_booking_payment(booking_id, method)
    ann = await db.get_announcement(booking["announcement_id"])
    client = await db.get_user(callback.from_user.id)
    driver = await db.get_user(ann["driver_id"])

    await callback.message.edit_text(
        "✅ To'lov qabul qilindi. So'rovingiz haydovchiga yuborildi, tasdiqlanishini kuting."
    )

    text = (
        f"🔔 Yangi joy band qilish so'rovi!\n\n"
        f"{format_announcement(ann)}\n\n"
        f"👤 Yo'lovchi: {client['full_name']}\n"
        f"💺 So'ralgan joylar: {booking['seats']}\n"
        f"💳 Garov puli to'landi ({method.capitalize()})"
    )
    await callback.bot.send_message(driver["tg_id"], text, reply_markup=kb.driver_decision_kb(booking_id))
    await callback.answer()


@router.message(F.text == "📄 Mening buyurtmalarim")
async def my_bookings(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or user["role"] != "client":
        return
    bookings = await db.get_client_bookings(message.from_user.id)
    if not bookings:
        await message.answer("Sizda hali buyurtmalar yo'q.")
        return

    for b in bookings:
        ann = await db.get_announcement(b["announcement_id"])
        await message.answer(
            f"📄 Buyurtma #{b['id']}\n"
            f"{ann['from_city']} ➜ {ann['to_city']} | {ann['trip_date']}\n"
            f"💺 {b['seats']} joy\n"
            f"Holat: {STATUS_MAP.get(b['status'], b['status'])}"
        )

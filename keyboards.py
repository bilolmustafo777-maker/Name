from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config


def role_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🚖 Men taksichiman", callback_data="role:driver")
    kb.button(text="🧍 Men yo'lovchiman", callback_data="role:client")
    kb.adjust(1)
    return kb.as_markup()


def phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def driver_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🆕 Yangi e'lon berish")],
            [KeyboardButton(text="📋 Mening e'lonlarim")],
            [KeyboardButton(text="⚙️ Mashina profilim")],
            [KeyboardButton(text="🏆 Faol haydovchilar")],
        ],
        resize_keyboard=True,
    )


def client_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 E'lonlarni ko'rish")],
            [KeyboardButton(text="📄 Mening buyurtmalarim")],
            [KeyboardButton(text="🏆 Faol haydovchilar")],
        ],
        resize_keyboard=True,
    )


def cities_kb(prefix: str, exclude: str = None, with_all: bool = False, quick_route=None):
    kb = InlineKeyboardBuilder()
    if quick_route:
        qfrom, qto = quick_route
        kb.button(text=f"🔁 {qfrom} → {qto} (so'nggi)", callback_data="quickroute:1")
    if with_all:
        kb.button(text="🌍 Barchasi", callback_data=f"{prefix}:Barchasi")
    for city in config.CITIES:
        if city == exclude:
            continue
        kb.button(text=city, callback_data=f"{prefix}:{city}")
    kb.adjust(2)
    return kb.as_markup()


def date_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 Bugun", callback_data="date:today")
    kb.button(text="📅 Ertaga", callback_data="date:tomorrow")
    kb.button(text="🗓 Boshqa sana", callback_data="date:custom")
    kb.adjust(2, 1)
    return kb.as_markup()


def car_kb():
    kb = InlineKeyboardBuilder()
    for car in config.CAR_TYPES:
        kb.button(text=car, callback_data=f"car:{car}")
    kb.adjust(2)
    return kb.as_markup()


def seats_kb(prefix: str = "seats", max_seats: int = 4):
    kb = InlineKeyboardBuilder()
    for n in range(1, max_seats + 1):
        kb.button(text=str(n), callback_data=f"{prefix}:{n}")
    kb.adjust(4)
    return kb.as_markup()


def confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash", callback_data="confirm_ann:yes")
    kb.button(text="❌ Bekor qilish", callback_data="confirm_ann:no")
    kb.adjust(2)
    return kb.as_markup()


def yes_no_kb(prefix: str, yes_text="✅ Ha", no_text="❌ Yo'q"):
    kb = InlineKeyboardBuilder()
    kb.button(text=yes_text, callback_data=f"{prefix}:1")
    kb.button(text=no_text, callback_data=f"{prefix}:0")
    kb.adjust(2)
    return kb.as_markup()


def book_kb(announcement_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Joy band qilish", callback_data=f"book:{announcement_id}")
    return kb.as_markup()


def payment_kb(booking_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Click orqali to'lash", callback_data=f"pay:click:{booking_id}")
    kb.button(text="💳 Payme orqali to'lash", callback_data=f"pay:payme:{booking_id}")
    kb.adjust(1)
    return kb.as_markup()


def payment_confirm_kb(booking_id, method):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ To'lovni tasdiqlash (test)", callback_data=f"pay_confirm:{method}:{booking_id}")
    kb.adjust(1)
    return kb.as_markup()


def driver_decision_kb(booking_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Qabul qilish", callback_data=f"driver_accept:{booking_id}")
    kb.button(text="❌ Rad etish", callback_data=f"driver_reject:{booking_id}")
    kb.adjust(2)
    return kb.as_markup()

from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    role = State()
    name = State()
    phone = State()


class DriverProfile(StatesGroup):
    """Haydovchining mashina profili — faqat bir marta to'ldiriladi va
    keyingi barcha e'lonlarda avtomatik ishlatiladi."""
    car_brand = State()
    car_photo = State()
    plate_number = State()
    luggage = State()
    parcel = State()


class DriverAnnouncement(StatesGroup):
    from_city = State()
    to_city = State()
    date_choice = State()
    custom_date = State()
    seats = State()
    confirm = State()


class ClientBrowse(StatesGroup):
    filter_from = State()
    filter_to = State()


class ClientBooking(StatesGroup):
    seats = State()

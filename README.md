# 7075.uz — Taksi va yo'lovchilar boti (v1.0)

Telegram bot orqali taksichilar va yo'lovchilarni bog'laydigan tizim.
Taksichi safar e'loni beradi (qayerdan → qayerga, sana, mashina turi, joylar soni),
yo'lovchi mos e'lonni topib, joy band qiladi, garov puli to'laydi va shafyor tasdiqlagach
ikkala tomon bir-birining telefon raqamini oladi.

## 1. Talab qilinadigan narsalar

- Python 3.10+
- Telegram bot tokeni ([@BotFather](https://t.me/BotFather) orqali `/newbot` bilan olinadi)

## 2. O'rnatish

```bash
cd 7075_taxi_bot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

`requirements.txt` tarkibi:
- `aiogram` — Telegram bot freymvorki (async, FSM bilan)
- `aiosqlite` — SQLite bazasi bilan async ishlash
- `python-dotenv` — `.env` faylidan sozlamalarni o'qish

## 3. Sozlash

```bash
cp .env.example .env
```

`.env` faylini oching va `BOT_TOKEN` qatoriga BotFather bergan tokenni qo'ying:

```
BOT_TOKEN=123456789:AAExampleTokenHereChangeMe
```

## 4. Ishga tushirish

```bash
python bot.py
```

Konsolda `Bot ishga tushdi...` deb chiqsa — Telegram'da botingizga `/start` yozib sinab ko'rishingiz mumkin.

## 5. Jarayon qanday ishlaydi

**Ro'yxatdan o'tish**: `/start` → rol tanlash (taksichi / yo'lovchi) → ism → telefon raqam.
Taksichi bo'lsa, shundan keyin **mashina profili** so'raladi (faqat bir marta):
mashina rusumi → mashina rasmi (ixtiyoriy, /skip bilan o'tkazish mumkin) →
davlat raqami (ixtiyoriy) → bagaj bormi (Ha/Yo'q) → pochta/posilka qabul qilamanmi (Ha/Yo'q).
Bu ma'lumotlar bazaga saqlanadi va **har bir e'londa avtomatik ishlatiladi** — qayta so'ralmaydi.
Profilni istalgan vaqt "⚙️ Mashina profilim" tugmasi orqali yangilash mumkin.

**Taksichi tomoni**:
1. "🆕 Yangi e'lon berish" → Qayerdan → Qayerga → Qachon (Bugun / Ertaga / Sana) →
   Joylar soni (1-4) → Tasdiqlash. (Mashina turi, bagaj, pochta profildan avtomatik olinadi.)
2. Agar avval e'lon bergan bo'lsangiz, "Qayerdan" bosqichida **"🔁 So'nggi yo'nalish"** tugmasi
   chiqadi — bitta bosishda oldingi yo'nalishingizni qayta ishlatishingiz mumkin.
3. E'lon bazaga saqlanadi va faol e'lonlar ro'yxatida ko'rinadi.
4. Yo'lovchidan so'rov kelganda (to'lovdan keyin) **aynan shu e'lon egasiga** xabar keladi:
   ✅ Qabul qilish / ❌ Rad etish (boshqa haydovchilarga bormaydi).
5. Qabul qilinsa — bo'sh joylar soni kamayadi, ikkala tomonga bir-birining ismi, telefon
   raqami va (agar bor bo'lsa) Telegram profil havolasi yuboriladi. Joylar 0 ga tushsa,
   e'lon avtomatik yopiladi (taxtadan olinadi).

**Yo'lovchi tomoni**:
1. "🔍 E'lonlarni ko'rish" → Qayerdan/Qayerga filtri → mos e'lonlar ro'yxati.
2. "✅ Joy band qilish" → nechta joy kerakligini tanlash → garov pulini to'lash (35 000 so'm).
3. To'lovdan keyin so'rov taksichiga yuboriladi, taksichi javobini kutish.
4. Taksichi qabul qilsa, taksichi raqami yuboriladi va aloqaga chiqish mumkin bo'ladi.
5. "📄 Mening buyurtmalarim" — barcha band qilishlar holatini ko'rish uchun.

**Kontaktlar va Telegram profil havolasi**:
Taksichi so'rovni qabul qilganda, ikkala tomonga ism, telefon raqami va (agar foydalanuvchida
Telegram username bo'lsa) `https://t.me/username` ko'rinishidagi profil havolasi ham yuboriladi.
Username bo'lmasa, faqat telefon raqami orqali bog'lanish tavsiya etiladi.

**"🏆 Faol haydovchilar" reytingi**:
Ikkala menyuda ham mavjud. Har bir haydovchining yakunlangan (taksichi tomonidan qabul qilingan)
safarlari soni bo'yicha TOP-10 reyting ko'rsatiladi, har biriga Telegram havolasi bilan birga.

## 6. Click / Payme to'lovi haqida — MUHIM

`payments.py` fayli **test (mock) rejimida** ishlaydi: foydalanuvchiga soxta to'lov havolasi
ko'rsatiladi va u "✅ To'lovni tasdiqlash (test)" tugmasini bosib, to'lovni o'zi qo'lda
tasdiqlaydi. Bu shunchaki localhost'da sinash uchun.

**Nega haqiqiy Click/Payme localhost'da ishlamaydi:**
Click va Payme to'lov tizimlari to'lov holatini bilish uchun sizning serveringizga
so'rov yuboradi (webhook / callback). Bu server internetdan ochiq (public HTTPS) bo'lishi
shart — `localhost` ularga ko'rinmaydi.

**Productionga chiqishda nima qilish kerak:**
1. Click va Payme'da tadbirkor sifatida ro'yxatdan o'ting, Merchant ID / Service ID /
   Secret key (Click) va Kassa ID (Payme) oling.
2. FastAPI yoki Flask'da kichik webhook server yozing:
   - Click uchun: `/click/prepare` va `/click/complete` endpointlari.
   - Payme uchun: Payme Merchant API (JSON-RPC) endpointi —
     `CheckPerformTransaction`, `CreateTransaction`, `PerformTransaction`, `CancelTransaction`.
3. Bu serverni domenli, HTTPS'ga ega hostingga joylang (yoki sinov uchun `ngrok` bilan
   localhost'ni vaqtincha internetga chiqaring).
4. `payments.py`'dagi `generate_payment_link` funksiyasini haqiqiy Click/Payme
   to'lov havolasini generatsiya qiladigan kodga almashtiring, `pay_confirm` handlerini esa
   webhook orqali kelgan haqiqiy tasdiqni qabul qiladigan qilib o'zgartiring.

## 7. Loyiha tuzilmasi

```
7075_taxi_bot/
├── bot.py              # botni ishga tushiruvchi fayl
├── config.py           # sozlamalar (token, shaharlar, mashina turlari, garov puli)
├── database.py         # SQLite bilan ishlash (foydalanuvchi, e'lon, band qilish)
├── keyboards.py        # barcha inline/reply klaviaturalar
├── states.py           # FSM holatlari (formalar bosqichlari, jumladan mashina profili)
├── payments.py         # Click/Payme uchun test to'lov moduli
├── utils.py            # kontakt matni / Telegram havolasini formatlash
├── handlers/
│   ├── common.py       # /start, ro'yxatdan o'tish, menyular
│   ├── driver.py       # taksichi: e'lon berish, so'rovlarga javob
│   └── client.py       # yo'lovchi: e'lonlarni ko'rish, band qilish, to'lov
├── requirements.txt
├── .env.example
└── taxi.db             # bot birinchi marta ishga tushganda avtomatik yaratiladi
```

## 9. "Faqat admin profilda ishlayapti" muammosi haqida

Agar "Qayerdan yo'lga chiqasiz?" bosqichi bitta Telegram akkauntda ishlab, boshqasida
ishlamasa — sababi odatda shu: o'sha boshqa akkaunt hali **taksichi sifatida to'liq
ro'yxatdan o'tmagan** (ya'ni `/start` → "🚖 Men taksichiman" → ism → telefon → mashina
profili bosqichlarini tugatmagan). v1.0'da endi bu holatda bot jim turmaydi — aniq
xabar chiqaradi: *"Bu bo'lim faqat ro'yxatdan o'tgan taksichilar uchun..."*.

Har bir Telegram profili (`tg_id`) alohida saqlanadi va mustaqil ishlaydi — bitta
akkauntdagi amal boshqasiga ta'sir qilmaydi, e'lon berish jarayoni ham har bir
foydalanuvchi uchun alohida holatda (FSM) yuritiladi.

## 10. v2.0 uchun tavsiyalar (keyingi bosqich)

- Haqiqiy Click/Payme integratsiyasi (yuqorida tushuntirilgan webhook server).
- Admin panel: e'lonlarni moderatsiya qilish, foydalanuvchilarni bloklash, statistikalar.
- Reyting tizimi (taksichi va yo'lovchi bir-birini baholaydi).
- Xarita orqali manzil tanlash (Telegram location).
- Bekor qilingan/eskirgan e'lonlarni avtomatik tozalash (cron/APScheduler).
- Ko'p tilli interfeys (o'zbek / rus).

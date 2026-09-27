# 7075.uz Telegram Bot — Railway'ga Deploy Qilish

Railway — bu Heroku-ga o'xshash, Python botlarni bepul hosting qilish uchun ajoyib platform.

## 1. GitHub repo yaratish

Railway GitHub'dan talab qiladi (free tier uchun kerak). Agar GitHub akkauntingiz bo'lsa:

```bash
cd ~/taxi   # yoki sizning papka nomingiz
git init
git add .
git commit -m "7075.uz bot v1.1 - Railway deploy"
```

GitHub'da yangi repo yarating: https://github.com/new
(masalan: `7075-taxi-bot`)

```bash
git remote add origin https://github.com/YOUR_USERNAME/7075-taxi-bot.git
git branch -M main
git push -u origin main
```

## 2. Railway'ga ulanish

1. **Railway'ga kiring:** https://railway.app (GitHub bilan kirish)
2. **"New Project"** ni bosing
3. **"Deploy from GitHub"** ni tanlang
4. GitHub'dan `7075-taxi-bot` repo'ni tanlang
5. Deploy boshlandi (few minutes kutish kerak)

## 3. Environment variables o'rnatish

Railway dashboard'da **Variables** bo'limiga o'ting va quyidagilarni qo'shing:

```
BOT_TOKEN=123456789:AAExampleTokenHereChangeMe
ADMIN_ID=0
DB_PATH=/tmp/taxi.db
```

**BOT_TOKEN** — @BotFather'dan olingan haqiqiy tokeningiz.

⚠️ **Muhim:** Railway'da `/tmp/` papkasi ishlatiladi, chunki `$HOME` papkasi har bir restart'da o'chiriladi. Baza fayli memory'da saqlanadi yoki qo'shimcha storage service ulash kerak.

## 4. Persistent Storage (SQLite bazani saqlab qolish)

SQLite ham fayl bo'lgani uchun, agar Railway'dan yangilash bo'lsa, `taxi.db` o'chilib ketadi.
Ikkita yechim:

### A. Qisqa vaqtli (free): Memory'da saqlay olamiz
Agar data'ningiz ko'p bo'lmasa va har ishga tushishda qayta o'zgarsa, `/tmp/taxi.db` yetarli.
Qayta ishga tushgan vaqt baza yangilanadi (oxirgi safardagi e'lonlar yo'q bo'ladi).

### B. Doimiy: PostgreSQL qo'shish (tavsiya etilgan)
Railway'da Telegram bot uchun **PostgreSQL** bepul service qo'shish mumkin:

1. Railway dashboard'da **"+ Add Service"** ni bosing
2. **PostgreSQL** tanlang
3. U avtomatik `DATABASE_URL` environment variable qo'shadi

Keyin `database.py`'ni SQLite o'rniga PostgreSQL uchun o'zgartirish kerak (v2.0'da).

## 5. Bot ishga tushishini tekshirish

Railway dashboard'da **Logs** bo'limida:
```
Bot ishga tushdi. To'xtatish uchun Ctrl+C bosing.
```

Bu xabarni ko'rsangiz, bot ishlayapti! 🎉

Telegram'da botingizga `/start` yozib tekshiring.

## 6. Muammolar va yechimlar

**Q: "ModuleNotFoundError: No module named 'aiogram'"**
- A: `requirements.txt` bo'rimi repo'da bor? Railway avtomatik unda o'qiydi.

**Q: "Bot to'xtatib ketyapti / 502 error"**
- A: Heroku kabi, Railway ham inactive bo'lsa to'xtatadi. Free tier uchun 500 soatlik limit bor/oyda.
- Bu yuzaki masala, restart qilib bo'ladi.

**Q: Bot baza faylini saqlay olmayapti**
- A: Railway memory'ni refresh qiladi. PostgreSQL qo'shing yoki v2.0'da supabase/Render.com'ga o'ting.

**Q: "Telegramnning bot qabul qilishi** kechiksanguvi bor**"
- A: Railway free tier serf xohllash mumkin. Platformani upgrade qilib, yoki @BotFather'dan `/setwebhook` o'rniga `/deletewebhook` qilib, polling rejimiga qayting.

## 7. Tartibi (Workflow)

```
Siz: Bot kodi yozish
         ↓
GitHub: git push
         ↓
Railway: Avtomatik deploy
         ↓
Telegram: /start bosing
```

## 8. Keyingi qadamlar (maslahatlar)

- **Monitoring:** Railway logger'iga qarang, log-da xatolarni ko'rish mumkin.
- **Qayta ishga tushirish:** Dashboard'dan "Redeploy" ni bosing (GitHub'dan so'nggi commit'ni qayta ishga tushiradi).
- **Domain + Webhook:** Kelganda custom domain'ni Railway orqali ulab, `/setwebhook` bilan polling'ni veb-hookga o'zgartirishingiz mumkin (tezroq).

---

**Savollar:** Railway docs — https://docs.railway.app/

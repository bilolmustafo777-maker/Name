import aiosqlite

import config

DB_PATH = config.DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                tg_id INTEGER PRIMARY KEY,
                role TEXT,                         -- 'driver' yoki 'client'
                full_name TEXT,
                phone TEXT,
                username TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id INTEGER,
                from_city TEXT,
                to_city TEXT,
                trip_date TEXT,
                car_type TEXT,
                total_seats INTEGER,
                available_seats INTEGER,
                status TEXT DEFAULT 'active',      -- active / closed
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                announcement_id INTEGER,
                client_id INTEGER,
                seats INTEGER,
                status TEXT DEFAULT 'pending_payment',
                                                    -- pending_payment / waiting_driver /
                                                    -- confirmed / rejected / cancelled
                deposit_amount INTEGER DEFAULT 35000,
                payment_status TEXT DEFAULT 'unpaid',   -- unpaid / paid
                payment_method TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # Eski bazalarga yangi ustunlarni xavfsiz qo'shish (migratsiya)
        await _ensure_columns(db, "users", {
            "car_brand": "TEXT",
            "car_photo": "TEXT",
            "plate_number": "TEXT",
            "has_luggage": "INTEGER DEFAULT 0",
            "takes_parcel": "INTEGER DEFAULT 0",
            "last_from": "TEXT",
            "last_to": "TEXT",
        })
        await db.commit()


async def _ensure_columns(db, table: str, columns: dict):
    cur = await db.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in await cur.fetchall()}
    for col, decl in columns.items():
        if col not in existing:
            await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")


# ---------------- USERS ----------------

async def get_user(tg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
        return await cur.fetchone()


async def create_or_update_user(
    tg_id, role=None, full_name=None, phone=None, username=None,
    car_brand=None, car_photo=None, plate_number=None,
    has_luggage=None, takes_parcel=None, last_from=None, last_to=None,
):
    user = await get_user(tg_id)
    async with aiosqlite.connect(DB_PATH) as db:
        if user is None:
            await db.execute(
                "INSERT INTO users (tg_id, role, full_name, phone, username) VALUES (?,?,?,?,?)",
                (tg_id, role, full_name, phone, username),
            )
        fields, values = [], []
        for col, val in [
            ("role", role), ("full_name", full_name), ("phone", phone), ("username", username),
            ("car_brand", car_brand), ("car_photo", car_photo), ("plate_number", plate_number),
            ("has_luggage", has_luggage), ("takes_parcel", takes_parcel),
            ("last_from", last_from), ("last_to", last_to),
        ]:
            if val is not None:
                fields.append(f"{col}=?")
                values.append(val)
        if fields and user is not None:
            values.append(tg_id)
            await db.execute(f"UPDATE users SET {', '.join(fields)} WHERE tg_id=?", values)
        await db.commit()


# ------------- ANNOUNCEMENTS (E'LONLAR) -------------

async def create_announcement(driver_id, from_city, to_city, trip_date, car_type, seats):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO announcements
               (driver_id, from_city, to_city, trip_date, car_type, total_seats, available_seats)
               VALUES (?,?,?,?,?,?,?)""",
            (driver_id, from_city, to_city, trip_date, car_type, seats, seats),
        )
        await db.commit()
        return cur.lastrowid


async def get_announcement(ann_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM announcements WHERE id=?", (ann_id,))
        return await cur.fetchone()


async def find_announcements(from_city=None, to_city=None):
    query = "SELECT * FROM announcements WHERE status='active' AND available_seats>0"
    params = []
    if from_city and from_city != "Barchasi":
        query += " AND from_city=?"
        params.append(from_city)
    if to_city and to_city != "Barchasi":
        query += " AND to_city=?"
        params.append(to_city)
    query += " ORDER BY created_at DESC"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(query, params)
        return await cur.fetchall()


async def get_driver_announcements(driver_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM announcements WHERE driver_id=? ORDER BY created_at DESC",
            (driver_id,),
        )
        return await cur.fetchall()


async def decrease_seats(ann_id, seats):
    """Joy band qilinganda bo'sh joylar sonini kamaytiradi.
    Agar 0 ga tushsa, e'lon avtomatik yopiladi (taxtadan olinadi)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE announcements SET available_seats = available_seats - ? WHERE id=?",
            (seats, ann_id),
        )
        cur = await db.execute("SELECT available_seats FROM announcements WHERE id=?", (ann_id,))
        row = await cur.fetchone()
        if row and row[0] <= 0:
            await db.execute("UPDATE announcements SET status='closed' WHERE id=?", (ann_id,))
        await db.commit()


async def close_announcement(ann_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE announcements SET status='closed' WHERE id=?", (ann_id,))
        await db.commit()


# ------------- BOOKINGS (BAND QILISHLAR) -------------

async def create_booking(announcement_id, client_id, seats):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO bookings (announcement_id, client_id, seats) VALUES (?,?,?)",
            (announcement_id, client_id, seats),
        )
        await db.commit()
        return cur.lastrowid


async def get_booking(booking_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
        return await cur.fetchone()


async def set_booking_payment(booking_id, method, status="paid"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE bookings SET payment_method=?, payment_status=?, status='waiting_driver' WHERE id=?",
            (method, status, booking_id),
        )
        await db.commit()


async def set_booking_status(booking_id, status):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
        await db.commit()


async def get_client_bookings(client_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM bookings WHERE client_id=? ORDER BY created_at DESC", (client_id,)
        )
        return await cur.fetchall()


# ------------- REYTING -------------

async def get_top_drivers(limit: int = 10):
    """Yakunlangan (tasdiqlangan) safarlar soni bo'yicha eng faol haydovchilar."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT u.tg_id, u.full_name, u.username, u.phone,
                   COUNT(b.id) AS trips
            FROM bookings b
            JOIN announcements a ON a.id = b.announcement_id
            JOIN users u ON u.tg_id = a.driver_id
            WHERE b.status = 'confirmed'
            GROUP BY a.driver_id
            ORDER BY trips DESC
            LIMIT ?
            """,
            (limit,),
        )
        return await cur.fetchall()

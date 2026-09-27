def user_contact_text(user) -> str:
    """Foydalanuvchi ismi, telefon raqami va (agar bo'lsa) Telegram profil
    havolasini chiroyli matn qilib qaytaradi."""
    lines = [f"👤 {user['full_name']}", f"📞 {user['phone']}"]
    if user["username"]:
        lines.append(f"🔗 Telegram: https://t.me/{user['username']}")
    else:
        lines.append("🔗 Telegram: username o'rnatilmagan (faqat telefon orqali bog'laning)")
    return "\n".join(lines)


def user_link(user) -> str:
    """Faqat havola/raqamni qaytaradi — reyting kabi qisqa joylar uchun."""
    if user["username"]:
        return f"https://t.me/{user['username']}"
    return user["phone"]

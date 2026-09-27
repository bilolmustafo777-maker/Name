"""
v1.0 uchun TEST (mock) to'lov moduli.

Haqiqiy Click va Payme integratsiyasi quyidagilarni talab qiladi:
  - Click:  Merchant ID, Service ID, Secret key va ochiq (public) HTTPS server,
            unda /click/prepare va /click/complete endpointlari bo'lishi kerak
            (Click ularga so'rov yuboradi).
  - Payme:  Merchant ID (Kassa) va ochiq HTTPS server, unda Payme Merchant API
            (CheckPerformTransaction, CreateTransaction, PerformTransaction va h.k.)
            JSON-RPC endpointi bo'lishi kerak.

localhost'da (ya'ni tashqi internetdan ko'rinmaydigan manzilda) bu webhooklarga
Click/Payme serverlari ulana olmaydi, shuning uchun v1.0'da to'lov "test rejimi"da
ishlaydi: foydalanuvchi soxta havolani ko'radi va "To'lovni tasdiqlash" tugmasini
bosib, to'lovni o'zi qo'lda tasdiqlaydi.

Productionga chiqishda bu faylni FastAPI/Flask webhook serveriga ulab,
haqiqiy Click/Payme Merchant API bilan almashtirish kerak bo'ladi
(ngrok yoki domenli server orqali).
"""

import uuid


def generate_payment_link(method: str, amount: int, order_id: int) -> str:
    token = uuid.uuid4().hex[:8]
    if method == "click":
        return f"https://my.click.uz/pay/TEST-MOCK/{order_id}-{token}"
    return f"https://checkout.paycom.uz/pay/TEST-MOCK/{order_id}-{token}"

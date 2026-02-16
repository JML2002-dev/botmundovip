import logging
import os
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIGURACIÓN
# =========================

TOKEN = os.getenv("TOKEN")
VIP_GROUP_ID = -1003665882219
ADMIN_GROUP_ID = -1003773189699

PRECIO_YAPE = "S/ 10"
PRECIO_PAYPAL = "$4 USD"
PAYPAL_LINK = "https://paypal.me/JovaMart"

YAPE_QR = "yape.jpg"
PROMO_IMG = "promo.jpg"

logging.basicConfig(level=logging.INFO)

usuarios_estado = {}

# =========================
# TECLADO
# =========================

def teclado_principal():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇵🇪 Yape", callback_data="yape"),
            InlineKeyboardButton("🌎 PayPal", callback_data="paypal"),
        ]
    ])

# =========================
# START (ENVÍA IMAGEN)
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usuarios_estado[user_id] = "inicio"

    mensaje = (
        "🔥 *Bienvenido a Mundo VIP* 🔥\n\n"
        "Accede a nuestro contenido exclusivo actualizado constantemente.\n\n"
        "💎 Acceso permanente\n"
        "🔒 Grupo privado\n"
        "⚡ Activación rápida\n\n"
        "💷 Pago único\n\n"
        "👇 Selecciona tu método de pago para continuar:"
    )

    with open(PROMO_IMG, "rb") as foto:
        await update.message.reply_photo(
            photo=foto,
            caption=mensaje,
            reply_markup=teclado_principal(),
            parse_mode="Markdown"
        )

# =========================
# BOTONES DE PAGO
# =========================

async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    estado = usuarios_estado.get(user_id)

    # Evita duplicación
    if estado == "esperando_comprobante":
        return

    usuarios_estado[user_id] = "esperando_comprobante"

    if query.data == "yape":
        with open(YAPE_QR, "rb") as qr:
            await query.message.reply_photo(
                photo=qr,
                caption=(
                    f"💚 *Pago con Yape*\n\n"
                    f"Monto: {PRECIO_YAPE}\n\n"
                    "1️⃣ Realiza el pago.\n"
                    "2️⃣ Envía aquí la captura del comprobante.\n\n"
                    "Tu acceso será activado una vez confirmado."
                ),
                parse_mode="Markdown"
            )

    elif query.data == "paypal":
        await query.message.reply_text(
            (
                f"🌎 *Pago con PayPal*\n\n"
                f"Monto: {PRECIO_PAYPAL}\n\n"
                f"Realiza el pago aquí:\n{PAYPAL_LINK}\n\n"
                "Luego envía la captura del comprobante para activar tu acceso."
            ),
            parse_mode="Markdown"
        )

# =========================
# RECIBIR COMPROBANTE
# =========================

async def recibir_comprobante(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id

    if usuarios_estado.get(user_id) != "esperando_comprobante":
        return

    foto = update.message.photo[-1].file_id

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Aprobar", callback_data=f"aprobar_{user_id}"),
            InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{user_id}")
        ]
    ])

    caption_admin = (
        "📥 *Nuevo comprobante recibido*\n\n"
        f"👤 Usuario: @{user.username}\n"
        f"🆔 ID: {user_id}\n\n"
        "Selecciona una acción:"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_GROUP_ID,
        photo=foto,
        caption=caption_admin,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

    usuarios_estado[user_id] = "pendiente"

    await update.message.reply_text(
        "✅ Comprobante recibido.\n\n"
        "Estamos verificando tu pago.\n"
        "Te avisaremos en breve."
    )

# =========================
# APROBACIÓN / RECHAZO
# =========================

async def admin_accion(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    accion, user_id = query.data.split("_")
    user_id = int(user_id)

    if accion == "aprobar":

        enlace = await context.bot.create_chat_invite_link(
            chat_id=VIP_GROUP_ID,
            expire_date=datetime.now() + timedelta(hours=1),
            member_limit=1
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 *Pago confirmado*\n\n"
                "Aquí tienes tu acceso VIP:\n"
                f"{enlace.invite_link}\n\n"
                "⚠️ El enlace expira en 1 hora.\n"
                "El acceso es permanente."
            ),
            parse_mode="Markdown"
        )

        await query.message.reply_text("✅ PAGO APROBADO")

        usuarios_estado[user_id] = "aprobado"
        await query.message.delete()

    elif accion == "rechazar":

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ *Pago rechazado*\n\n"
                "El comprobante no pudo validarse.\n"
                "Por favor envíalo nuevamente."
            ),
            parse_mode="Markdown"
        )

        await query.message.reply_text("❌ PAGO RECHAZADO")

        usuarios_estado[user_id] = "esperando_comprobante"
        await query.message.delete()

# =========================
# MENSAJES
# =========================

async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    texto = update.message.text.lower()

    estado = usuarios_estado.get(user_id)

    if estado in ["esperando_comprobante", "pendiente"]:
        return

    if any(p in texto for p in ["precio", "cuanto", "vale", "costo"]):
        await update.message.reply_text(
            f"💎 Precio actual:\nYape: {PRECIO_YAPE}\nPayPal: {PRECIO_PAYPAL}",
            reply_markup=teclado_principal()
        )
        return

    if any(p in texto for p in ["yape"]):
        usuarios_estado[user_id] = "esperando_comprobante"
        with open(YAPE_QR, "rb") as qr:
            await update.message.reply_photo(
                photo=qr,
                caption=f"Paga {PRECIO_YAPE} vía Yape y envía la captura."
            )
        return

    if any(p in texto for p in ["paypal"]):
        usuarios_estado[user_id] = "esperando_comprobante"
        await update.message.reply_text(
            f"Paga {PRECIO_PAYPAL} vía PayPal:\n{PAYPAL_LINK}\n\nEnvía la captura."
        )
        return

    await update.message.reply_text(
        "Selecciona tu método de pago:",
        reply_markup=teclado_principal()
    )

# =========================
# MAIN
# =========================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(botones, pattern="^(yape|paypal)$"))
    app.add_handler(CallbackQueryHandler(admin_accion, pattern="^(aprobar_|rechazar_)"))
    app.add_handler(MessageHandler(filters.PHOTO, recibir_comprobante))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensajes))

    print("🔥 Bot Mundo VIP PRO funcionando...")
    app.run_polling()

if __name__ == "__main__":
    main()

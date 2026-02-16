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
print("TOKEN CARGADO:", TOKEN)
VIP_GROUP_ID = -1003665882219
ADMIN_GROUP_ID = -1003773189699

PRECIO_YAPE = "S/ 10 soles"
PRECIO_PAYPAL = "$4 USD"
PAYPAL_LINK = "https://paypal.me/TUENLACE"
YAPE_QR = "yape.jpg"

logging.basicConfig(level=logging.INFO)

usuarios_estado = {}

# =========================
# TECLADO PRINCIPAL
# =========================

def teclado_principal():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇵🇪 Yape", callback_data="yape"),
            InlineKeyboardButton("🌎 PayPal", callback_data="paypal"),
        ]
    ])

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usuarios_estado[user_id] = "inicio"

    mensaje = (
        "🔥 *Bienvenido a Mundo VIP* 🔥\n\n"
        "Aquí obtendrás acceso exclusivo con contenido VIP actualizado constantemente.\n\n"
        "💎 Acceso permanente\n"
        "🔒 Grupo privado\n"
        "🔒 100% respaldado y libre de caidas\n"
        "⚠️ Si eres sensible mejor ni ingreses\n\n"
        "💀 El mejor contenido prohibido de todo Telegram solo en nuestro VIP \n\n"
        "✅ Dormidas Reales\n\n"
        "✅ Borrachas\n\n"
        "✅ Violads 100% reales\n\n"
        "✅ Colegialas\n\n"
        "✅ Chibolitas\n\n"
        "✅ Espiadas\n\n"
        "✅ Omegle\n\n"
        "✅ Trios y Cornudos\n\n"
        "✅ Famosas Peruanas\n\n"
        "✅ Streamers e influencers\n\n"
        "✅ OnlyFans\n\n"
        "✅ Sexmex\n\n"
        "✅ Packs Filtrados reales\n\n"
        "✅ Packs Filtrados reales\n\n"
        "Es un unico Pago"
        "Selecciona tu método de pago para continuar:"
    )

    await update.message.reply_text(
        mensaje,
        reply_markup=teclado_principal(),
        parse_mode="Markdown"
    )

# =========================
# BOTONES
# =========================

async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    usuarios_estado[user_id] = "esperando_comprobante"

    if query.data == "yape":
        await query.message.reply_photo(
            photo=open(YAPE_QR, "rb"),
            caption=(
                f"💚 *Pago con Yape*\n\n"
                f"Monto: {PRECIO_YAPE}\n\n"
                "1️⃣ Realiza el pago.\n"
                "2️⃣ Envía aquí la captura del comprobante.\n\n"
                "Una vez confirmado recibirás tu acceso."
            ),
            parse_mode="Markdown"
        )

    if query.data == "paypal":
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
        "✅ Comprobante recibido correctamente.\n\n"
        "Estamos verificando tu pago. Te avisaremos en breve."
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
                "🎉 *Pago confirmado con éxito*\n\n"
                "Aquí tienes tu enlace de acceso al grupo VIP:\n"
                f"{enlace.invite_link}\n\n"
                "⚠️ El enlace expira en 1 hora.\n"
                "El acceso al grupo es permanente."
            ),
            parse_mode="Markdown"
        )

        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=(
                "✅ *PAGO APROBADO*\n\n"
                f"🆔 Usuario ID: {user_id}\n"
                "Enlace enviado correctamente."
            ),
            parse_mode="Markdown"
        )

        usuarios_estado[user_id] = "aprobado"
        await query.message.delete()

    if accion == "rechazar":

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ *Pago rechazado*\n\n"
                "El comprobante no pudo ser validado.\n"
                "Por favor envíalo nuevamente."
            ),
            parse_mode="Markdown"
        )

        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=f"❌ PAGO RECHAZADO\n🆔 Usuario ID: {user_id}"
        )

        usuarios_estado[user_id] = "esperando_comprobante"
        await query.message.delete()

# =========================
# MENSAJES INTELIGENTES
# =========================

async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    texto = update.message.text.lower()

    if usuarios_estado.get(user_id) in ["esperando_comprobante", "pendiente"]:
        return

    palabras_yape = ["yape", "pagar yape", "quiero yape"]
    palabras_paypal = ["paypal", "pagar paypal"]
    palabras_precio = ["precio", "cuanto", "vale", "costo"]
    palabras_info = ["info", "información", "acceso", "grupo", "vip", "entrar"]

    if any(p in texto for p in palabras_yape):
        usuarios_estado[user_id] = "esperando_comprobante"
        await update.message.reply_photo(
            photo=open(YAPE_QR, "rb"),
            caption=f"Paga {PRECIO_YAPE} vía Yape y envía la captura aquí."
        )
        return

    if any(p in texto for p in palabras_paypal):
        usuarios_estado[user_id] = "esperando_comprobante"
        await update.message.reply_text(
            f"Paga {PRECIO_PAYPAL} vía PayPal:\n{PAYPAL_LINK}\n\nEnvía la captura aquí."
        )
        return

    if any(p in texto for p in palabras_precio):
        await update.message.reply_text(
            f"💎 Precio actual:\nYape: {PRECIO_YAPE}\nPayPal: {PRECIO_PAYPAL}",
            reply_markup=teclado_principal()
        )
        return

    if any(p in texto for p in palabras_info):
        await update.message.reply_text(
            "🔥 Acceso VIP disponible.\nSelecciona método de pago:",
            reply_markup=teclado_principal()
        )
        return

    await update.message.reply_text(
        "Para acceder al grupo VIP selecciona un método de pago:",
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

    print("Bot Mundo VIP PRO 3.0 funcionando...")
    app.run_polling()

if __name__ == "__main__":
    main()



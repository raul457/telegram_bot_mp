from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user, save_pending_payment
from mercadopago_integration import create_pix_payment
from config import PLANS, GROUP_ID
import logging
from io import BytesIO
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra os planos disponíveis"""
    keyboard = [
        [InlineKeyboardButton("📅 Semanal - R$5,00", callback_data="plan_weekly")],
        [InlineKeyboardButton("📆 Mensal - R$15,00", callback_data="plan_monthly")],
        [InlineKeyboardButton("🎯 Anual - R$120,00", callback_data="plan_yearly")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "💰 *Escolha seu plano:*\n\n"
        "✅ Semanal: 7 dias de acesso\n"
        "✅ Mensal: 30 dias de acesso\n"
        "✅ Anual: 365 dias de acesso + desconto!\n\n"
        "Clique no plano desejado para gerar o QR Code PIX.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a escolha do plano e gera PIX"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    plan_type = query.data.split("_")[1]
    plan = PLANS[plan_type]
    
    # Mensagem de "processando"
    await query.edit_message_text(
        f"🔄 Gerando QR Code PIX para o plano *{plan['name']}*...\n"
        f"💰 Valor: R$ {plan['price']/100:.2f}\n\n"
        f"⏳ Aguarde alguns segundos...",
        parse_mode="Markdown"
    )
    
    try:
        # Cria pagamento PIX no Mercado Pago
        payment_id, qr_code, qr_base64, ticket_url = create_pix_payment(
            user_id, 
            plan_type,
            query.from_user.username
        )
        
        if payment_id:
            # Salva no banco
            save_pending_payment(
                str(payment_id), 
                user_id, 
                plan_type, 
                plan['price'],
                {
                    "qr_code": qr_code,
                    "qr_code_base64": qr_base64,
                    "ticket_url": ticket_url
                }
            )
            
            # Decodifica base64 da imagem do QR Code
            qr_image_data = base64.b64decode(qr_base64.split(",")[1] if "," in qr_base64 else qr_base64)
            
            # Envia a imagem do QR Code
            await query.message.reply_photo(
                photo=BytesIO(qr_image_data),
                caption=f"💳 *Pagamento PIX - Plano {plan['name']}*\n\n"
                       f"💰 *Valor:* R$ {plan['price']/100:.2f}\n"
                       f"📋 *Código PIX:*\n`{qr_code}`\n\n"
                       f"⏱️ *Este QR Code expira em 30 minutos*\n\n"
                       f"✅ Após pagar, o acesso será liberado automaticamente em até 2 minutos.\n\n"
                       f"🔗 *Alternativa:* [Clique aqui para pagar pelo link]({ticket_url})",
                parse_mode="Markdown"
            )
            
            # Botão para verificar status manualmente
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Verificar pagamento", callback_data=f"check_{payment_id}")]
            ])
            
            await query.message.reply_text(
                "💡 *Dica:* Após realizar o pagamento, clique no botão abaixo para verificar o status.",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
        else:
            await query.message.reply_text(
                "❌ *Erro ao gerar pagamento*\n\n"
                "Tente novamente em alguns minutos ou contate o suporte.",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Erro ao gerar PIX: {str(e)}")
        await query.message.reply_text(
            "❌ *Erro inesperado*\n\n"
            "Por favor, tente novamente mais tarde.",
            parse_mode="Markdown"
        )

async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verifica manualmente o status do pagamento"""
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.split("_")[1]
    
    from mercadopago_integration import check_payment_status
    status, payment_data = check_payment_status(payment_id)
    
    if status == "approved":
        await query.edit_message_text(
            "✅ *Pagamento confirmado!*\n\n"
            "Sua assinatura já está ativa. Use o link do grupo VIP que foi enviado.\n\n"
            "Caso não tenha recebido o link, aguarde alguns segundos ou contate o suporte.",
            parse_mode="Markdown"
        )
    elif status == "pending":
        await query.edit_message_text(
            "⏳ *Pagamento pendente*\n\n"
            "Aguardando confirmação do PIX. O processo pode levar alguns minutos.\n\n"
            "Assim que for confirmado, você receberá uma mensagem automática.",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "❌ *Pagamento não encontrado ou expirado*\n\n"
            "Por favor, gere um novo QR Code em /planos.",
            parse_mode="Markdown"
        )
from telegram import Update
from telegram.ext import ContextTypes
from database import get_all_users, get_active_users, get_expired_users, activate_subscription
from config import ADMIN_IDS
from datetime import datetime

async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Acesso negado.")
        return
    
    users = get_all_users()
    if not users:
        await update.message.reply_text("📋 Nenhum usuário encontrado.")
        return
    
    msg = "📋 *LISTA COMPLETA DE USUÁRIOS*\n\n"
    for user in users:
        exp_date = datetime.fromisoformat(user["expiration_date"]).strftime("%d/%m/%Y") if user["expiration_date"] else "N/A"
        msg += f"👤 *ID:* `{user['telegram_id']}`\n"
        msg += f"📛 *Nome:* {user['name']}\n"
        msg += f"🆔 *Username:* @{user['username'] if user['username'] else 'N/A'}\n"
        msg += f"📅 *Cadastro:* {user['signup_date'][:10]}\n"
        msg += f"✅ *Status:* {user['status']}\n"
        msg += f"📆 *Expira:* {exp_date}\n"
        msg += f"🎫 *Plano:* {user['plan_type'] if user['plan_type'] else 'N/A'}\n"
        msg += "─" * 20 + "\n"
    
    # Divide em mensagens de 4000 caracteres
    for i in range(0, len(msg), 4000):
        await update.message.reply_text(msg[i:i+4000], parse_mode="Markdown")

async def admin_ativos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    users = get_active_users()
    msg = f"✅ *USUÁRIOS ATIVOS:* {len(users)}\n\n"
    for user in users:
        exp_date = datetime.fromisoformat(user["expiration_date"]).strftime("%d/%m/%Y")
        msg += f"• `{user['telegram_id']}` - {user['name']} - Expira: {exp_date} - Plano: {user['plan_type']}\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def admin_expirados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    users = get_expired_users()
    msg = f"❌ *USUÁRIOS EXPIRADOS:* {len(users)}\n\n"
    for user in users:
        msg += f"• `{user['telegram_id']}` - {user['name']} - Expirou em: {user['expiration_date'][:10]}\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def add_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
        plan_type = context.args[2] if len(context.args) > 2 else "monthly"
        
        activate_subscription(user_id, days, plan_type, "manual_admin")
        
        await update.message.reply_text(
            f"✅ *Tempo adicionado com sucesso!*\n\n"
            f"👤 Usuário: `{user_id}`\n"
            f"📆 Dias adicionados: {days}\n"
            f"🎫 Plano: {plan_type}",
            parse_mode="Markdown"
        )
    except:
        await update.message.reply_text(
            "❌ *Uso correto:*\n"
            "`/addtempo <user_id> <dias> <plano>`\n\n"
            "Exemplo: `/addtempo 123456789 30 monthly`",
            parse_mode="Markdown"
        )
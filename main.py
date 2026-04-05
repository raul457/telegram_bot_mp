from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import TOKEN, ADMIN_IDS, WEBHOOK_URL
from database import init_db, register_user
from subscriptions import plans, plan_callback, check_payment
from admin import admin_list, admin_ativos, admin_expirados, add_time
from scheduler_jobs import start_scheduler
from webhook_server import start_webhook_server
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Comando /start - Registra o usuário"""
    user = update.effective_user
    register_user(user.id, user.full_name, user.username)
    
    from config import WELCOME_MSG
    await update.message.reply_text(WELCOME_MSG, parse_mode="Markdown")

async def help_command(update, context):
    """Comando /help"""
    help_text = """
🤖 *Comandos disponíveis:*

📌 /start - Iniciar o bot
💰 /planos - Ver planos de assinatura
🆘 /help - Esta mensagem de ajuda

*Comandos de Admin:*
👥 /usuarios - Listar todos usuários
✅ /ativos - Listar usuários ativos
❌ /expirados - Listar usuários expirados
⏰ /addtempo <id> <dias> - Adicionar tempo
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

def main():
    # Inicializa banco de dados
    init_db()
    logger.info("✅ Banco de dados inicializado")
    
    # Inicia servidor webhook
    start_webhook_server()
    
    # Cria aplicação do bot
    app = Application.builder().token(TOKEN).build()
    
    # Handlers de comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("planos", plans))
    
    # Comandos de admin (com verificação)
    for admin_id in ADMIN_IDS:
        app.add_handler(CommandHandler("usuarios", admin_list, filters=filters.User(user_id=admin_id)))
        app.add_handler(CommandHandler("ativos", admin_ativos, filters=filters.User(user_id=admin_id)))
        app.add_handler(CommandHandler("expirados", admin_expirados, filters=filters.User(user_id=admin_id)))
        app.add_handler(CommandHandler("addtempo", add_time, filters=filters.User(user_id=admin_id)))
    
    # Handlers de callback
    app.add_handler(CallbackQueryHandler(plan_callback, pattern="plan_"))
    app.add_handler(CallbackQueryHandler(check_payment, pattern="check_"))
    
    # Inicia scheduler para expiração automática
    start_scheduler(app)
    
    # Configura webhook do Telegram (opcional - descomente se quiser)
    # app.bot.set_webhook(f"{WEBHOOK_URL}/telegram")
    
    logger.info("🚀 Bot iniciado!")
    app.run_polling()

if __name__ == "__main__":
    main()
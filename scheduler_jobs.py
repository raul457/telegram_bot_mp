from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from telegram.ext import Application
from database import get_expired_users, update_status
from config import GROUP_ID
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def check_and_remove_expired(app: Application):
    """Verifica usuários expirados e remove do grupo"""
    logger.info("🔄 Verificando assinaturas expiradas...")
    
    expired_users = get_expired_users()
    
    for user in expired_users:
        telegram_id = user["telegram_id"]
        name = user["name"]
        
        try:
            # Remove do grupo
            await app.bot.ban_chat_member(GROUP_ID, telegram_id)
            await app.bot.unban_chat_member(GROUP_ID, telegram_id)
            
            # Atualiza status no banco
            update_status(telegram_id, "inactive")
            
            # Envia mensagem de aviso
            from config import EXPIRED_MSG
            await app.bot.send_message(telegram_id, EXPIRED_MSG, parse_mode="Markdown")
            
            logger.info(f"✅ Usuário {telegram_id} ({name}) removido por expiração")
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover {telegram_id}: {str(e)}")

async def check_near_expiration(app: Application):
    """Avisa usuários com assinatura perto de expirar (1 dia)"""
    from database import get_all_users
    from datetime import timedelta
    from config import RENEW_MSG
    
    users = get_all_users()
    now = datetime.now()
    
    for user in users:
        if user["status"] == "active" and user["expiration_date"]:
            exp_date = datetime.fromisoformat(user["expiration_date"])
            days_left = (exp_date - now).days
            
            if days_left == 1:
                try:
                    await app.bot.send_message(
                        user["telegram_id"], 
                        RENEW_MSG.format(days=days_left),
                        parse_mode="Markdown"
                    )
                    logger.info(f"📧 Aviso enviado para {user['telegram_id']} - expira em 1 dia")
                except Exception as e:
                    logger.error(f"Erro ao enviar aviso: {e}")

def start_scheduler(app: Application):
    """Inicia o scheduler com as tarefas periódicas"""
    
    # Verifica expirados a cada hora
    scheduler.add_job(
        check_and_remove_expired,
        trigger=IntervalTrigger(hours=1),
        args=[app],
        id="check_expired"
    )
    
    # Verifica expiração próxima a cada 6 horas
    scheduler.add_job(
        check_near_expiration,
        trigger=IntervalTrigger(hours=6),
        args=[app],
        id="check_near_exp"
    )
    
    scheduler.start()
    logger.info("⏰ Scheduler iniciado com sucesso!")
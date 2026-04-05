import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS").split(",")]
GROUP_ID = int(os.getenv("GROUP_ID"))

# Mercado Pago
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
MP_PUBLIC_KEY = os.getenv("MP_PUBLIC_KEY")

# Webhook
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

# Planos (em dias e valor em centavos - REAL)
PLANS = {
    "weekly": {"name": "Semanal", "days": 7, "price": 500},
    "monthly": {"name": "Mensal", "days": 30, "price": 1500},
    "yearly": {"name": "Anual", "days": 365, "price": 12000}
}

# URLs das imagens dos planos (opcional)
PLAN_IMAGES = {
    "weekly": "https://i.imgur.com/xxx1.jpg",
    "monthly": "https://i.imgur.com/xxx2.jpg",
    "yearly": "https://i.imgur.com/xxx3.jpg"
}

# Mensagens
WELCOME_MSG = """
🎉 *Bem-vindo ao Clube VIP!*

Acesse conteúdos exclusivos com nossos planos:

📅 *Semanal* - R$ 5,00
📆 *Mensal* - R$ 15,00  
🎯 *Anual* - R$ 120,00

Clique em /planos para assinar agora mesmo!
"""

PAYMENT_RECEIVED_MSG = """
✅ *Pagamento confirmado!*

Sua assinatura {plan} foi ativada com sucesso!
📅 Expira em: {expiration_date}

🔗 Clique abaixo para entrar no grupo VIP:
{invite_link}

Aproveite todo o conteúdo exclusivo! 🚀
"""

EXPIRED_MSG = """
❌ *Sua assinatura EXPIRU!*

Para continuar acessando o conteúdo VIP, renove sua assinatura agora mesmo:

Clique em /planos e escolha o melhor plano para você! 💰
"""
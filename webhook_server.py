from flask import Flask, request, jsonify
import threading
import logging
from database import update_payment_status, activate_subscription, get_pending_payment
from config import PLANS, GROUP_ID, TOKEN
from mercadopago_integration import sdk
import telegram

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = telegram.Bot(token=TOKEN)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook do Mercado Pago para notificações de pagamento"""
    try:
        data = request.json
        logger.info(f"Webhook recebido: {data}")
        
        # Extrai o ID do pagamento
        if data.get("type") == "payment":
            payment_id = data.get("data", {}).get("id")
            
            if payment_id:
                # Verifica status no Mercado Pago
                result = sdk.payment().get(payment_id)
                payment = result["response"]
                
                if payment["status"] == "approved":
                    # Atualiza no banco
                    update_payment_status(str(payment_id), "approved")
                    
                    # Busca dados do pagamento pendente
                    pending = get_pending_payment(str(payment_id))
                    
                    if pending:
                        telegram_id = pending["telegram_id"]
                        plan_type = pending["plan_type"]
                        days = PLANS[plan_type]["days"]
                        
                        # Ativa assinatura
                        activate_subscription(telegram_id, days, plan_type, str(payment_id))
                        
                        # Envia mensagem de confirmação
                        try:
                            # Gera link do grupo
                            invite_link = bot.create_chat_invite_link(GROUP_ID, member_limit=1)
                            
                            expiration_date = (datetime.now() + timedelta(days=days)).strftime("%d/%m/%Y")
                            
                            msg = f"""
✅ *Pagamento confirmado!*

Sua assinatura {PLANS[plan_type]['name']} foi ativada com sucesso!
📅 Expira em: {expiration_date}

🔗 Clique abaixo para entrar no grupo VIP:
{invite_link.invite_link}

Aproveite todo o conteúdo exclusivo! 🚀
"""
                            bot.send_message(telegram_id, msg, parse_mode="Markdown")
                            
                        except Exception as e:
                            logger.error(f"Erro ao enviar confirmação: {e}")
                            
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}")
        return jsonify({"status": "error"}), 500

def start_webhook_server():
    """Inicia o servidor Flask em uma thread separada"""
    from config import PORT
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False)).start()
    logger.info(f"🚀 Webhook server rodando na porta {PORT}")
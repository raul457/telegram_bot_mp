import mercadopago
from config import MP_ACCESS_TOKEN, PLANS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa SDK do Mercado Pago
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

def create_pix_payment(telegram_id, plan_type, email=None):
    """
    Cria um pagamento PIX no Mercado Pago
    Retorna: (payment_id, qr_code, qr_code_base64, ticket_url)
    """
    try:
        plan = PLANS[plan_type]
        amount = plan["price"] / 100  # Converte centavos para reais
        
        # Dados do pagamento
        payment_data = {
            "transaction_amount": amount,
            "description": f"Assinatura {plan['name']} - Telegram Bot",
            "payment_method_id": "pix",
            "payer": {
                "email": email or f"user_{telegram_id}@temp.com",
                "first_name": f"Usuario_{telegram_id}",
                "identification": {
                    "type": "CPF",
                    "number": "00000000000"
                }
            },
            "notification_url": f"{os.getenv('WEBHOOK_URL')}/webhook"
        }
        
        # Cria o pagamento
        result = sdk.payment().create(payment_data)
        payment = result["response"]
        
        if result["status"] == 201:
            payment_id = payment["id"]
            qr_code = payment["point_of_interaction"]["transaction_data"]["qr_code"]
            qr_code_base64 = payment["point_of_interaction"]["transaction_data"]["qr_code_base64"]
            ticket_url = payment["point_of_interaction"]["transaction_data"]["ticket_url"]
            
            logger.info(f"✅ Pagamento PIX criado: {payment_id} para usuário {telegram_id}")
            
            return payment_id, qr_code, qr_code_base64, ticket_url
        else:
            logger.error(f"❌ Erro ao criar pagamento: {result}")
            return None, None, None, None
            
    except Exception as e:
        logger.error(f"❌ Erro no Mercado Pago: {str(e)}")
        return None, None, None, None

def check_payment_status(payment_id):
    """
    Verifica o status de um pagamento no Mercado Pago
    Retorna: (status, payment_data)
    """
    try:
        result = sdk.payment().get(payment_id)
        payment = result["response"]
        
        status = payment["status"]
        logger.info(f"Status do pagamento {payment_id}: {status}")
        
        return status, payment
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar pagamento: {str(e)}")
        return None, None
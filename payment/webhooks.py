import json
import base64
import hashlib
import hmac
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Order
from .tasks import send_order_confirmation

@csrf_exempt
def liqpay_webhook(request):
    if request.method == 'POST':
        data = request.POST.get('data')
        signature = request.POST.get('signature')

        # Перевірка підпису для безпеки
        generated_signature = generate_signature(data)

        if signature != generated_signature:
            return HttpResponse(status=400)  # Неправильний підпис

        decoded_data = json.loads(base64.b64decode(data).decode('utf-8'))

        # Обробка події успішної оплати
        if decoded_data.get('status') == 'success':
            order_id = decoded_data.get('order_id')
            try:
                order = Order.objects.get(id=order_id)
                if not order.paid:
                    order.paid = True
                    order.save()

                    # Надсилаємо підтвердження
                    send_order_confirmation.delay(order_id)

            except Order.DoesNotExist:
                return HttpResponse(status=404)  # Замовлення не знайдено

            return HttpResponse(status=200)  # Успішна відповідь
        else:
            return HttpResponse(status=400)  # Непідтримувана подія або помилка

    return HttpResponse(status=405)  # Метод не дозволений


def generate_signature(data):
    """Генерує підпис для перевірки запиту від LiqPay"""
    sign_string = settings.LIQPAY_PRIVATE_KEY + data + settings.LIQPAY_PRIVATE_KEY
    return base64.b64encode(hashlib.sha1(sign_string.encode('utf-8')).digest()).decode('utf-8')

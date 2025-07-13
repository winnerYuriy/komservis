import requests
import uuid
from decimal import Decimal
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse


from cart.cart import Cart

from .forms import ShippingAddressForm
from .models import Order, OrderItem, ShippingAddress
from django.views.decorators.csrf import csrf_exempt
from .liqpay_service import LiqPayService
import json


liqpay_service = LiqPayService(settings.LIQPAY_PUBLIC_KEY, settings.LIQPAY_PRIVATE_KEY)

def payment(request, order_id):
    amount = 100  # Приклад суми, зазвичай ви її отримуєте з бази даних
    form = liqpay_service.create_payment_data(order_id, amount)
    return render(request, 'payment.html', {'form': form})

@csrf_exempt
def payment_callback(request):
    if request.method == 'POST':
        data = json.loads(request.POST.get('data'))
        signature = request.POST.get('signature')
        if liqpay_service.validate_payment(data, signature):
            # Обробка успішної оплати
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=400)

def payment_success(request):
    # Повідомлення про успішну оплату
    return render(request, 'payment_success.html')


@login_required(login_url='account:login')
def shipping(request):
    try:
        shipping_address = ShippingAddress.objects.get(user=request.user)
    except ShippingAddress.DoesNotExist:
        shipping_address = None
    form = ShippingAddressForm(instance=shipping_address)

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=shipping_address)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.save()
            return redirect('account:dashboard')

    return render(request, 'shipping/shipping.html', {'form': form})


def checkout(request):
    if request.user.is_authenticated:
        shipping_address, _ = ShippingAddress.objects.get_or_create(
            user=request.user)
        return render(request, 'payment/checkout.html', {'shipping_address': shipping_address})
    return render(request, 'payment/checkout.html')


def complete_order(request):
    if request.method == "POST":
        # Отримання даних з форми
        full_name = request.POST.get('name')
        email = request.POST.get('email')
        
        # Збір даних для API
        payment_data = {
            "version": 3,
            "public_key": settings.LIQPAY_PUBLIC_KEY,
            "action": "pay",
            "amount": "100",  # Змінити на фактичну суму
            "currency": "UAH",
            "description": "Payment description",
            "order_id": "order_id",  # Змінити на реальний order_id
            "server_url": "http://your_server_url/payment/callback/",
            "result_url": "http://your_site.com/payment/success/",
        }

        # Надсилання запиту на LiqPay
        try:
            response = requests.post("https://www.liqpay.ua/api/3/checkout", json=payment_data)
            response.raise_for_status()  # Викликає помилку для неуспішного статусу
            
            # Логування тексту відповіді
            print("Текст відповіді від LiqPay:", response.text)
            
            # Спробуйте декодувати JSON
            data = response.json()  
            return JsonResponse(data)
        except requests.exceptions.HTTPError as err:
            print("Помилка при запиті до LiqPay:", err)
            print("Текст відповіді:", response.text)  # Логування тексту відповіді
            return JsonResponse({'error': 'Помилка при запиті до LiqPay'}, status=500)
        except ValueError as e:
            print("Помилка декодування JSON:", e)
            print("Текст відповіді:", response.text)  # Логування тексту відповіді
            return JsonResponse({'error': 'Не вдалося декодувати відповідь API'}, status=500)

    return render(request, 'payment/checkout.html')


def payment_success(request):
    for key in list(request.session.keys()):
        if key == 'session_key':
            del request.session[key]
    return render(request, 'payment/payment-success.html')


def payment_failed(request):
    return render(request, 'payment/payment-failed.html')

@staff_member_required
def admin_order_pdf(request, order_id):
    try:
        order = Order.objects.select_related('user', 'shipping_address').get(id=order_id)
    except Order.DoesNotExist:
        raise Http404('Заказ не найден')
    html = render_to_string('payment/order/pdf/pdf_invoice.html',
                            {'order': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=order_{order.id}.pdf'
    css_path = static('payment/css/pdf.css').lstrip('/')
    # css_path = 'static/payment/css/pdf.css'
  #  stylesheets = [weasyprint.CSS(css_path)]
  #  weasyprint.HTML(string=html).write_pdf(response, stylesheets=stylesheets)
    return response

import hashlib
import base64
import json
import requests

class LiqPayService:
    def __init__(self, public_key, private_key):
        self.public_key = public_key
        self.private_key = private_key
        self.api_url = 'https://www.liqpay.ua/api/request'

    def create_signature(self, data):
        json_data = json.dumps(data)
        encoded_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
        signature = base64.b64encode(hashlib.sha1(self.private_key.encode('utf-8') + encoded_data.encode('utf-8') + self.private_key.encode('utf-8')).digest()).decode('utf-8')
        return signature, encoded_data

    def make_payment(self, order_id, amount, currency, description):
        data = {
            'version': 3,
            'public_key': self.public_key,
            'action': 'pay',
            'amount': str(amount),
            'currency': currency,
            'description': description,
            'order_id': order_id,
            'sandbox': 1  # 1 для тестування, 0 для реальних транзакцій
        }
        signature, encoded_data = self.create_signature(data)
        payload = {
            'data': encoded_data,
            'signature': signature
        }
        response = requests.post(self.api_url, data=payload)
        return response.json()

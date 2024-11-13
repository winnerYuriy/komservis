import os
import json
import logging
import requests
import pandas as pd
from hashlib import md5
from pyexpat.errors import messages
from bs4 import BeautifulSoup
from django.http import HttpResponse, JsonResponse
from dotenv import load_dotenv
from main.settings import BASE_DIR
from django.core.files.base import ContentFile
from googleapiclient.discovery import build


logger = logging.getLogger('shop.utils')

load_dotenv()
HOST = os.getenv('HOST') 
API_KEY = os.getenv('API_KEY') # 'your_api_key'
CSE_ID = os.getenv('CSE_ID') # 'your_search_engine_id'
MEDIA_ROOT = os.getenv('MEDIA_ROOT') # 'your_media_root'

         
                
def download_excel_file(url):
    response = requests.get(url)
    response.raise_for_status()  # Видає виключення для статусів 4xx і 5xx

    # Повертаємо файл у відповідь
    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response_file = HttpResponse(response.content, content_type=content_type)
    response_file['Content-Disposition'] = 'attachment; filename="pricelist.xlsx"'
    return response_file


def get_token(url):
    password = os.getenv('PASSWORD')
    r = requests.post(f'{HOST}/auth', data={'login': os.getenv('LOGIN'), 'password': md5(password.encode()).hexdigest()})
    res = json.loads(r.text)
    logging.info(f'Get token Brain : {res.get("result", None)}')

    return res.get('result', None)  # Повертає None, якщо ключ не існує


#token_brain = get_token(f'{HOST}/auth')

def save_product_image(product, image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        product.main_image.save(f"{product.code}.jpg", ContentFile(response.content), save=True)
    else:
        logging.info(f"Failed to save image: {image_url}")


def download_product_images(product_id, token_brain):
    url = f'{HOST}/product_pictures/{product_id}/{token_brain}'
    response = requests.get(url)
    logging.info(f'Запит до {url} - Статус код: {response.status_code}, Відповідь: {response.text}')
    return response.json()


def fetch_product_details(product_id, sid, lang='ua'):
        """
        Функція для отримання деталей продукту з API
        """
        url = f"{HOST}/product/{product_id}/{sid}"
        params = {'lang': lang}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Перевірка на статус код
            data = response.json()

            if data.get("status") == 1 and "result" in data:
                product_data = data["result"]
                description = product_data.get("brief_description")
                full_description = product_data.get("description")
                attribute = product_data.get("options", [])

                return {
                    "description": description,
                    "full_description": full_description,
                    "attribute": attribute
                }
            else:
                print(f"Не вдалося отримати дані для productID {product_id}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Помилка при отриманні даних для productID {product_id}: {e}")
            return None

# Налаштуйте ваш ключ API та CX (Search Engine ID) Google Custom Search API



# Функція для завантаження логотипів брендів
def download_brand_logos(modeladmin, request, queryset):
    # Перевіряємо, чи існує папка для збереження логотипів
   
    logo_folder = os.path.join(BASE_DIR, '/brand_logos')
    if not os.path.exists(logo_folder):
        os.makedirs(logo_folder)

    # Обробка вибраних брендів з queryset
    for brand in queryset:
        try:
            # Викликаємо функцію для пошуку логотипу
            logo_url = search_brand_logo(brand.name)
            if logo_url:
                # Завантажуємо логотип
                download_image(logo_url, brand.name, logo_folder)
            else:
                print(f"Логотип для бренду {brand.name} не знайдено.")
        except Exception as e:
            print(f"Помилка при обробці бренду {brand.name}: {str(e)}")

    # Повідомлення про завершення процесу
    modeladmin.message_user(request, "Логотипи для вибраних брендів успішно завантажено!")

download_brand_logos.short_description = "Завантажити логотипи для вибраних брендів"
# Функція для пошуку логотипу бренду в Інтернеті через Google API
def search_brand_logo(brand_name):
    service = build("customsearch", "v1", developerKey=API_KEY)
    res = service.cse().list(q=f"{brand_name} logo", cx=CSE_ID, searchType='image', fileType='png', num=1).execute()
    
    if 'items' in res:
        first_item = res['items'][0]
        return first_item['link']  # Повертаємо перший знайдений логотип
    return None

# Функція для завантаження зображення
def download_image(image_url, brand_name, save_folder):
    # Отримуємо зображення
    response = requests.get(image_url)
    if response.status_code == 200:
        # Визначаємо шлях для збереження зображення
        image_path = os.path.join(save_folder, f"{brand_name}.png")
        
        # Записуємо зображення в файл
        with open(image_path, 'wb') as f:
            f.write(response.content)
        print(f"Логотип {brand_name} успішно завантажено.")
    else:
        print(f"Не вдалося завантажити зображення для бренду {brand_name}.")
        

def get_image_upload_path(instance, filename):
    # Отримуємо назву батьківської категорії
    parent_category_name = instance.product.category.name if instance.category.parent else 'Без категорії'
    # Формуємо шлях збереження
    return os.path.join('images/products/main', parent_category_name, filename)


def clean_html(self, text):
        """
        Очищає HTML-теги з тексту.
        """
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text()
    

def get_discounted_price(self):
        """
        Calculates the discounted price based on the product's price and discount.
        
        Returns:
            decimal.Decimal: The discounted price.
        """
        discounted_price = self.retail_price - (self.retail_price * self.discount / 100)
        return round(discounted_price, 2)
    
    


   

import io
import pandas as pd
from .models import Product

def get_available_products():
    """Отримує всі доступні товари з бази даних."""
    return Product.objects.filter(available=True).values(
        'title', 'category__name', 'brand', 'retail_price', 'quantity', 'discount'
    )

def generate_excel_file(products):
    headers = ['Назва', 'Категорія', 'Бренд', 'Ціна', 'Кількість', 'Знижка(%)' ]
    
    """Генерує Excel-файл зі списком товарів."""
    df = pd.DataFrame(products)
    df.columns = headers
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Прайс товарів')
    # Отримуємо доступ до книги та аркуша
    workbook = writer.book
    worksheet = writer.sheets['Прайс товарів']
    
    # Автоматичне розширення ширини колонок
    for i, col in enumerate(df.columns):
        max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2  # Додаємо 2 для відступу
        worksheet.set_column(i, i, max_length)
    writer.close()  # Закриваємо запис
    output.seek(0)
    return output.getvalue()


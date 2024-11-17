import json
import plotly.express as px
import pandas as pd
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, TemplateView
from .forms import ExcelUploadForm
from .models import Category, Product, Brand, VisitLog
from django.http import HttpResponse
from .price_generator import get_available_products, generate_excel_file
from datetime import datetime
from .managers import ProductProxy
from .filters import ProductFilter
from django.db.models import Count

"""class CategoryDetailView(ListView):
    model = Product
    template_name = 'shop/category_detail.html'
    context_object_name = 'products'

    def get_queryset(self):
        category = Category.objects.get(slug=self.kwargs['slug'])
        return Product.objects.filter(category=category)
"""

def product_list(request):
    product_filter = ProductFilter(request.GET, queryset=Product.objects.all())
    return render(request, 'іshop/product_list.html', {'filter': product_filter})

class CategoryDetailView(ListView):
    model = Product
    template_name = 'shop/category_detail.html'
    context_object_name = 'products'

    def get_queryset(self):
        # Отримуємо категорію за slug
        self.category = Category.objects.get(slug=self.kwargs['slug'])
        # Отримуємо всі дочірні категорії, включаючи саму категорію
        subcategories = self.category.get_descendants(include_self=True)
        # Повертаємо товари, які належать до будь-якої з цих категорій
        return Product.objects.filter(category__in=subcategories)

    def get_context_data(self, **kwargs):
        # Отримуємо контекст базового класу
        context = super().get_context_data(**kwargs)
        # Додаємо вибрану категорію до контексту
        context['category'] = self.category
        return context
    
class ProductListView(ListView):
    model = ProductProxy
    context_object_name = "products"
    paginate_by = 20

    def get_template_names(self):
        if self.request.htmx:
            return "shop/components/product_list.html"
        return "shop/products.html"


class PriceListView(TemplateView):
    template_name = "shop/price_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = get_available_products()  # Передаємо товари у шаблон
        return context


    def get_queryset(self):
        return Product.objects.filter(brand__slug=self.kwargs['brand_slug'])


def products_detail_view(request, slug):
    product = get_object_or_404(ProductProxy.objects.select_related("category"), slug=slug)
    max_quantity = product.quantity
    max_quantity = int(max_quantity)
    # Конвертація JSON-атрибутів у список Python (якщо атрибути збережені у форматі JSON-рядка)
    try:
        #attributes = json.loads(product.attributes) if isinstance(product.attributes, str) else product.attributes
        attributes = json.loads(product.attributes) if isinstance(product.attributes, str) else product.attributes
        if attributes is None:
            attributes = []
    except json.JSONDecodeError:
        attributes = []  # Якщо дані JSON некоректні, встановлюємо порожній список
    
    # Обробка повторюваних опцій
    formatted_attributes = {}
    for attribute in attributes:
        name = attribute.get('name')
        value = attribute.get('value')
        
        # Якщо значення вже існує для цієї назви, додаємо нове через ", "
        if name in formatted_attributes:
            formatted_attributes[name] += f", {value}"
        else:
            formatted_attributes[name] = value
    
    # Переміщаємо "Виробник", "Модель", "Артикул", "Гарантія" в кінець
    specific_attributes = ["Виробник", "Модель", "Артикул", "Гарантія"]
    bottom_attributes = {}
    
    for key in specific_attributes:
        if key in formatted_attributes:
            bottom_attributes[key] = formatted_attributes.pop(key)
    
    # Об'єднуємо решту атрибутів з цими внизу
    formatted_attributes.update(bottom_attributes)
        
    # Обробка відгуків
    if request.method == "POST":
        if request.user.is_authenticated:
            if product.reviews.filter(created_by=request.user).exists():
                messages.error(request, "You have already made a review for this product.")
            else:
                rating = request.POST.get("rating", 3)
                content = request.POST.get("content", "")
                if content:
                    product.reviews.create(
                        rating=rating,
                        content=content,
                        created_by=request.user,
                        product=product,
                    )
                    return redirect(request.path)
        else:
            messages.error(request, "You need to be logged in to make a review.")
            
     # Отримуємо схожі товари (за тією ж категорією, але не сам товар)
    similar_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]        
    
    context = {
        "similar_products": similar_products,
        "product": product,
        "attributes": formatted_attributes, 
        "max_quantity": range(1, max_quantity + 1)  # Передаємо відформатовані атрибути
    }
    return render(request, "shop/product_detail.html", context)


def category_list(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = ProductProxy.objects.select_related("category").filter(category=category)
    context = {"category": category, "products": products}
    return render(request, "shop/category_list.html", context)


def search_products(request):
    query = request.GET.get("q")
    products = ProductProxy.objects.filter(title__icontains=query).distinct()
    context = {"products": products}
    if not query or not products:
        return redirect("shop:products")
    return render(request, "shop/products.html", context)


def price_list_view(request):
    """Відображення списку товарів у вигляді таблиці."""
    products = get_available_products()
    return render(request, "shop/price_list.html", {"products": products})


def download_price_excel(request):
    """Генерує та надсилає Excel-файл із прайсом товарів з динамічною назвою файлу."""
    products = get_available_products()
    excel_file = generate_excel_file(products)

    # Формування назви файлу
    # current_date = datetime.now().strftime("%m.%Y")  # Формат дд.мм.рррр
    # file_name = f"Прайс на {current_date}.xlsx"
    current_date = datetime.now().strftime("%d.%m.%y")  # Формат дд.мм.рр
    file_name = f"Прайс на {current_date}.xlsx"
    # Повернення файлу з відповідним іменем
    response = HttpResponse(
        excel_file,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{file_name}'
    return response


def import_products_view(request):
    if request.method == "POST":
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES["file"]

            # Тимчасове зберігання файлу або передача в функцію для обробки
            # TODO: додати функцію для обробки Excel-файлу

            messages.success(request, "Файл успішно завантажено!")
            return redirect("import-products")
        else:
            messages.error(request, "Файл не вдалося завантажити. Перевірте формат.")

    else:
        form = ExcelUploadForm()
    return render(request, "upload_products.html", {"form": form})



def product_list(request, category_slug=None):
    category = None
    products = Product.objects.all()
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(request, 'shop/product_list.html', {'category': category, 'products': products})

def sidebar_view(request):
    categories = Category.objects.all()
    return render(request, 'shop/sidebar.html', {'categories': categories})


def brands_list(request):
    brands = Brand.objects.all().order_by('name')  # Сортуємо бренди за назвою
    return render(request, 'shop/brands_list.html', {'brands': brands})

def brand_products(request, brand_slug):
    brand = Brand.objects.get(slug=brand_slug)
    # Отримуємо бренд за slug або кидаємо 404, якщо не знайдений
    #brand = get_object_or_404(Brand, brand_slug=brand_slug)
    
     # Фільтруємо продукти цього бренду, які є в наявності
    products = Product.objects.filter(brand__slug=brand_slug, available=True)
    
    # Отримуємо всі товари цього бренду
    #products = brand.products.all()
    
    # Повертаємо дані в шаблон
    return render(request, 'shop/brand_products.html', {'brand': brand, 'products': products})

def visit_statistics_view(request):
    # Отримуємо фільтровані дані по датах
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    visits = VisitLog.objects.all()
    if start_date:
        visits = visits.filter(date__gte=start_date)
    if end_date:
        visits = visits.filter(date__lte=end_date)
    
    # Групуємо по датах і підраховуємо кількість відвідувань
    visit_data = visits.values('date__date').annotate(visits=Count('id')).order_by('date__date')

    # Створення DataFrame на основі даних з запиту
    if visit_data.exists():  # Перевіряємо, чи є дані
        df = pd.DataFrame(list(visit_data))
        df.rename(columns={'date__date': 'date', 'visits': 'visit_count'}, inplace=True)

        # Створення графіка
        fig = px.line(data_frame=df, x='date', y='visit_count', title='Visit Statistics')

        # Перетворюємо графік в HTML
        graph_html = fig.to_html()
    else:
        graph_html = "<p>No data available for the selected date range.</p>"

    # Повертаємо дані в шаблон
    return render(request, 'shop/visit_statistics.html', {
        'graph': graph_html,
        'visits': visits
    })
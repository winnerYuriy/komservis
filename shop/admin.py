from django.contrib import admin, messages
from django.http import JsonResponse
from django.urls import path, reverse
from mptt.admin import MPTTModelAdmin
from main.settings import BASE_DIR
from .models import *
from .utils import *
from django import forms
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.shortcuts import redirect, render
import json
from .forms import ExcelUploadForm, ChangeCategoryForm
import pandas as pd
import os
import logging
from dotenv import load_dotenv
from django.db import transaction
from transliterate import translit
from django.core.exceptions import PermissionDenied
from .utils import download_brand_logos  # Імпортуємо вашу функцію


@admin.action(description='Завантажити логотипи брендів')
def download_logos(modeladmin, request, queryset):
    # Перевірка прав доступу, якщо необхідно
    if not request.user.is_superuser:
        raise PermissionDenied

    # Викликаємо функцію для завантаження логотипів
    download_brand_logos()
    
    # Повертаємо повідомлення про успішне виконання
    modeladmin.message_user(request, "Логотипи брендів успішно завантажено!")
    return HttpResponse("Логотипи брендів завантажено!")

@admin.action(description="Оновити описи товарів з API")
@transaction.atomic
def update_descriptions(modeladmin, request, queryset):
    sid = get_token(f"{HOST}/auth")
    updated_count = 0

    for product in queryset:
        description, full_description, attributes = get_product_descriptions(product.product_id, sid)

        if description or full_description or attributes:
            product.description = description
            product.full_description = full_description
            product.attributes = attributes
            product.save()
            updated_count += 1
        else:
            messages.warning(request, f"Не вдалося оновити товар з ID {product.product_id}")

    messages.success(request, f"Оновлено {updated_count} товарів.")


@admin.action(description="Є в наявності")
def make_available(modeladmin, request, queryset):
    # Змінює статус 'available' для обраних товарів на True
    queryset.update(available=True)


@admin.action(description="Немає в наявності")
def make_unavailable(modeladmin, request, queryset):
    # Змінює статус 'available' для обраних товарів на False
    queryset.update(available=False)


@admin.action(description="Змінити категорію")
def change_category(modeladmin, request, queryset):
    # Якщо форму було надіслано, обробляємо її
    if "apply" in request.POST:
        form = ChangeCategoryForm(request.POST)
        if form.is_valid():
            new_category = form.cleaned_data["category"]
            queryset.update(category=new_category)
            modeladmin.message_user(
                request, f"Категорію змінено для {queryset.count()} товарів."
            )
            return redirect(request.get_full_path())

    # Якщо форму не надіслано, показуємо форму для вибору категорії
    else:
        form = ChangeCategoryForm()

    # Відображаємо форму
    return render(
        request, "admin/change_category.html", {"form": form, "products": queryset}
    )


load_dotenv()
HOST = os.getenv("HOST")

# Налаштування логування
logging.basicConfig(
    filename="product_import.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
   
# Кастомний фільтр для фільтрації товарів без основного зображення
class HasMainImageFilter(admin.SimpleListFilter):
    title = "Наявність основного зображення"
    parameter_name = "has_main_image"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Зображення присутнє"),
            ("no", "Зображення відсутнє"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(main_image__isnull=False)
        elif self.value() == "no":
            return queryset.filter(main_image__isnull=True)
        return queryset


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class UploadProductsForm(forms.Form):
    file = forms.FileField(label="Виберіть файл Excel")


class ProductAdminForm(forms.ModelForm):
    attributes_table = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        attributes = self.get_attributes_as_dict(self.instance.additional_attributes)
        table_html = self.generate_table_html(attributes)
        self.fields["attributes_table"].widget = forms.Textarea(
            attrs={"readonly": "readonly"}
        )
        self.fields["attributes_table"].initial = table_html

    def get_attributes_as_dict(self, json_data):
        try:
            return json.loads(json_data) if json_data else {}
        except json.JSONDecodeError:
            return {}

    def generate_table_html(self, attributes):
        rows = "".join(
            f'<tr><td>{key}</td><td><input type="text" name="attr_{key}" value="{value}" /></td></tr>'
            for key, value in attributes.items()
        )
        return mark_safe(f"<table>{rows}</table>")

    def clean(self):
        cleaned_data = super().clean()
        attributes = {}
        for key, value in self.data.items():
            if key.startswith("attr_"):
                attr_key = key.replace("attr_", "")
                attributes[attr_key] = value
        cleaned_data["additional_attributes"] = json.dumps(attributes)
        return cleaned_data


@admin.register(Category)
class CategoryMPTTAdmin(MPTTModelAdmin):
    list_display = ("name", "parent", "slug")
    ordering = ["name", "lft", "level"]
    #list_editable = ("",)
    list_filter = ("name", "parent")
    prepopulate_from = ('name', 'parent')
    class Media:
        js = ('admin/js/category_slug.js',)
        
    def save_model(self, request, obj, form, change):
        if not obj.slug:
            obj.slug = slugify(obj.name)
        super().save_model(request, obj, form, change)
            

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'promotion_type', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('promotion_type', 'is_active', 'start_date', 'end_date')
    ordering = ["name", "start_date", "end_date"]
    search_fields = ('name',)
    list_filter = ("name", "start_date", "end_date")
    prepopulate_from = ('name',)
    # Додайте можливість вибору типу акції
    def promotion_type_label(self, obj):
        return obj.get_promotion_type_display()
    promotion_type_label.short_description = 'Тип акції'
    
    class Media:
        js = ('admin/js/promotion_slug.js',)

    def save_model(self, request, obj, form, change):
        if not obj.slug:
            obj.slug = slugify(obj.name)
        super().save_model(request, obj, form, change)

class PropertyValueInline(admin.TabularInline):
    model = PropertyValue
    extra = 1  # Кількість порожніх форм для додавання властивостей     
        
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category_list')
    list_filter = ('category',)
    inlines = [PropertyValueInline]

    def get_categories(self, obj):
        return ", ".join([cat.name for cat in obj.category.all()])
    get_categories.short_description = 'Категорії'


@admin.register(PropertyValue)
class PropertyValueAdmin(admin.ModelAdmin):
    # Ваші налаштування для PropertyValueAdmin (наприклад, list_display, search_fields тощо)
    list_display = ('value', 'property')
    search_fields = ('value',)
    list_filter = ('property', 'value')

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "image_show")
    list_filter = ("name",)
    ordering = ["name"]
    actions = [download_brand_logos]

    def image_show(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="width: 50px; height: auto;" />'
            )
        return "Немає зображення"
        
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    change_list_template = "admin/shop/product/change_list.html"
    list_display = ("image_show", "title", "retail_price", "quantity", "available" )
    list_filter = ("available", "category", "brand", HasMainImageFilter, "created_at")
    ordering = ("title",)
    inlines = [ProductImageInline,]  
    readonly_fields = ("created_at", "updated_at")
    actions = [make_available, make_unavailable, change_category, update_descriptions]

    fieldsets = (
        ("Основна інформація", {
            "fields": (
                "title", "slug", "product_id", "category", "code", "article","main_image",
                "brand", "price", "retail_price", "quantity", "discount", 
                "available", "attributes", "additional_attributes", "description", "full_description", 
                "warranty", "country",
            )
        }),
        ("Акції та знижки", {"fields": ("promotions",)}),
        ("Дати", {"fields": ("created_at", "updated_at")}),
    )

    def get_prepopulated_fields(self, request, obj=None):
        return {"slug": ("title",)}

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import_products/", self.admin_site.admin_view(self.import_products), name="import-products"),
            path("import_images/", self.admin_site.admin_view(self.import_images), name="import-images"),
            path("change_category/", self.admin_site.admin_view(change_category), name="change-category"),
            path("get_pricelist/", self.admin_site.admin_view(self.get_pricelist), name="get-pricelist"),
          #  path("update-products/", self.admin_site.admin_view(self.update_products), name="update-products"),
        ]
        return custom_urls + urls

    def get_pricelist(self, request):
        target_id = 48
        format = "xlsx"
        sid = get_token(f"{HOST}/auth")
        lang = "ua"
        full = 3
        url = f"{HOST}/pricelists/{target_id}/{format}/{sid}?lang={lang}&full={full}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 1 and "url" in data:
                url_to_download = data["url"]
                return download_excel_file(url_to_download)
            else:
                return JsonResponse({"status": "error", "message": "Не вдалося отримати посилання на прайс."})

        except requests.exceptions.RequestException as e:
            return JsonResponse({"status": "error", "message": f"Помилка запиту до API: {e}"})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Не вдалося декодувати відповідь сервера."})
   
   
    def import_products(self, request):
        if request.method == 'POST':
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                df = pd.read_excel(file)
                # Заміна всіх NaN на None для коректного збереження
                df = df.where(pd.notnull(df), 0)

                self.log_to_file("Стовпці в Excel: " + str(df.columns.tolist()))

                column_mapping = {
                    'Name': 'title',
                    'PriceUAH': 'price',
                    'RetailPrice': 'retail_price',
                    'CategoryName': 'category',
                    'Available': 'quantity',
                    'Stock': 'available',
                    'Warranty': 'warranty',
                    'Country': 'country',
                    'Vendor': 'brand',
                    'Code': 'code',
                    'Article': 'article',
                    'ProductID': 'product_id',
                }

                created_count = 0
                updated_count = 0   

                for index, row in df.iterrows():
                    product_data = {}
                    category_name = row.get('CategoryName').upper()                 
                      
                    if category_name:
                        # Транслітеруємо назву категорії в латиницю
                        category_name_lat = translit(category_name, language_code='uk', reversed=True)
                        
                        # Генеруємо slug на основі латинської транслітерації
                        slug = category_name_lat.lower().replace(' ', '-').replace('(', '').replace(')', '').replace(',', '').replace('`', '').replace('\'', '').replace("'", '')
                        
                        # Використовуємо get_or_create, щоб не оновлювати категорії
                        category, created = Category.objects.get_or_create(
                            name=category_name,
                            defaults={
                                'slug': slug,
                                'parent': None,  # Якщо є батьківська категорія, вкажіть тут
                            }
                        )
                        product_data['category'] = category

                         # Додаємо логіку для створення бренду
                        brand_name = row.get('Vendor')
                        if brand_name:
                            brand, created = Brand.objects.get_or_create(
                                name=brand_name
                            )
                            product_data['brand'] = brand  # Заміщаємо назву бренду на об'єкт бренду
                        else:
                            self.log_to_file(f'Не вдалося знайти бренд для продукту на рядку {index}.')
                                 
                    for excel_column, model_field in column_mapping.items():
                        if excel_column in df.columns:  
                            if model_field != 'category' and model_field != 'brand':  # Не працюємо з категорією та брендом тут
                                product_data[model_field] = row[excel_column]
                        else:
                            self.log_to_file(f'Стовпець "{excel_column}" не знайдено в Excel. Будь ласка, перевірте файл.')

                    # Додаємо логіку для створення продукту                    
                    if 'title' in product_data:
                        product, created = Product.objects.update_or_create(
                            title=product_data['title'],
                            defaults=product_data
                        )
                        product.slug = slugify(product_data['title'])
                        product.save()  # Зберігаємо продукт з новим slug

                        if created:
                            created_count += 1
                            self.log_to_file(f'Створено продукт: {product.title}')
                        else:
                            updated_count += 1
                            self.log_to_file(f'Оновлено продукт: {product.title}')
                    else:
                        self.log_to_file(f'Не вдалося створити продукт, оскільки заголовок не знайдено в рядку {index}.')
                self.log_to_file(f'Товари імпортовані успішно! Імпортовано: {created_count}, Оновлено: {updated_count}.')
                messages.success(request, f'Товари імпортовані успішно! Імпортовано: {created_count}, Оновлено: {updated_count}.')
                return redirect(reverse('admin:shop_product_changelist'))
        else:
            form = ExcelUploadForm()
        return render(request, 'admin/import_products.html', {'form': form})


    def log_to_file(self, message):
        log_file_path = os.path.join(BASE_DIR, 'log.txt')
        with open(log_file_path, 'a', encoding='utf-8') as file:
            file.write(message + '\n')


    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = "Завантаження товарів"
        extra_context["update_button"] = True
        return super().changelist_view(request, extra_context=extra_context)


    def import_images(self, request):
        session_id = get_token(f"{HOST}/auth")
        logging.info(f"Отримані дані сесії: {session_id}")
        if not session_id:
            self.message_user(
                request, "Не вдалося отримати SID для імпорту зображень", messages.ERROR
            )
            logging.error("Не вдалося отримати SID для імпорту зображень.")
            return redirect("admin:shop_product_changelist")

        products = Product.objects.filter(
            main_image=""
        )  # Знайти продукти без головного зображення
        logging.info(f"Знайдено {products.count()} продуктів без головного зображення.")
        imported_images_count = 0

        for product in products:
            logging.info(f"Завантаження зображень для продукту {product.product_id}")
            image_data = download_product_images(product.product_id, session_id)
            logging.info(
                f"Спроба імпорту зображення для продукту: {product.product_id}"
            )
            if image_data.get("status") == 1 and image_data.get("result"):
                main_image_url = image_data["result"][0]["full_image"]
                save_product_image(product, main_image_url)
                imported_images_count += 1
                logging.info(f"Зображення для товару {product.product_id} завантажено.")
            else:
                logging.error(
                    f"Не вдалося отримати зображення для продукту {product.product_id}."
                )

        messages.success(
            request, f"Зображення імпортовані для {imported_images_count} продуктів."
        )
        logging.info(
            f"Імпорт зображень завершено, імпортовано: {imported_images_count} зображень."
        )
        return redirect("admin:shop_product_changelist")

    def image_show(self, obj):
        if obj.main_image:
            return mark_safe(
                f'<img src="{obj.main_image.url}" style="width: 50px; height: auto;" />'
            )
        return "Немає зображення"  # Або можна повертати пустий рядок

    image_show.short_description = "Зображення"


    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        logging.info(f"Модель {obj} збережено.")


def get_product_descriptions(product_id, sid, lang='ua'):
    url = f"{HOST}/product/{product_id}/{sid}"
   
    params = {'lang': lang}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 1:
                result = data['result']
                brief_description = result.get('brief_description', '')
                description = result.get('description', '')
                options = result.get('options', [])
                return brief_description, description, options
        else:
            print(f"Помилка запиту: статус {response.status_code}")
    except requests.RequestException as e:
        print(f"Помилка під час запиту: {e}")
    return None, None, None

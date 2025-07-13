from bs4 import BeautifulSoup
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey
from .utils import get_image_upload_path
from django.contrib.auth.models import User



"""class Category(MPTTModel):
    """
    #Model representing a category.
"""
    name = models.CharField("Категорія", max_length=50, unique=True)
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, 
        related_name='children', verbose_name='Батьківська категорія'
    )
    slug = models.SlugField('URL', max_length=50, unique=True, null=False, blank=True)
    image = models.ImageField(upload_to='images/category_images/', null=True, blank=True)
    
    class MPTTMeta:
        order_insertion_by = ['parent', 'name']
    
    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
    
    def save(self, *args, **kwargs):
        # Перетворюємо назву на заголовні літери
        #self.name = self.name.title()  # або self.name.capitalize() для першої літери всього слова
        # Якщо slug порожній, створюємо його автоматично
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)   
        
    def __str__(self):
        return self.name
"""

class Category(MPTTModel):
    """
    Модель, що представляє категорію з використанням MPTT для ієрархічних структур.
    """
    name = models.CharField("Категорія", max_length=50, unique=True)
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, 
        related_name='children', verbose_name='Батьківська категорія'
    )
    slug = models.SlugField('URL', max_length=50, unique=True, blank=True)
    image = models.ImageField(upload_to='images/category_images/', null=True, blank=True)

    class MPTTMeta:
        order_insertion_by = ['name']  # Підкатегорії сортуються за іменем

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        ordering = ['tree_id', 'lft']  # Сортування для відображення за ієрархією

    def save(self, *args, **kwargs):
        # Автоматичне створення `slug`, якщо він не заданий
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Promotion(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва акції")
    description = models.TextField(blank=True, null=True, verbose_name="Опис акції")
    discount_percentage = models.PositiveIntegerField(default=0, verbose_name="Знижка в %")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    start_date = models.DateTimeField(verbose_name="Дата початку акції")
    end_date = models.DateTimeField(verbose_name="Дата закінчення акції")
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="ЧПУ акції")
    # Нове поле для типу акції
    PROMOTION_TYPES = [
        ('sale', 'Акція'),
        ('new', 'Новинка'),
        ('best_seller', 'Хіт продажів'),
        ('discount', 'Знижка'),
        ('hot', 'Товар дня'),
        ('week', 'Товар тижня'),
        ('month', 'Товар місяця'),
        ('year', 'Товар року'),
        ('season', 'Товар сезону'),
        ('new_year', 'Новий рік'),
        ('summer', 'Літній сезон'),
        ('winter', 'Зимовий сезон'),
        ('autumn', 'Осінній сезон'),
        ('spring', 'Весняний сезон'),
        ('valentine', 'Валентинка'),
        ('new_year_gift', 'Новорічний подарунок'),
        ('birthday', 'День народження'),
        ('black_friday', 'Чорна п\'ятниця'),
        ('recommended', 'Рекомендуємо'),
    ]
    
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPES)
        
    class Meta:
        verbose_name = 'Акція'
        verbose_name_plural = 'Акції'
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)    
    
    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='brand_logos', null=True, blank=True)
  #  image = models.ImageField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренди'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name        

   
class Product(models.Model):
    """
    A model representing a product.

    """
    id = models.AutoField(primary_key=True, verbose_name="ID товару", null=False, blank=False, auto_created=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Категорія")
    title = models.CharField("Назва", max_length=250)
    product_id = models.IntegerField("ID товару", default=0)
    #brand = models.CharField("Бренд", max_length=250)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products', verbose_name="Бренд")
    promotions = models.ManyToManyField(Promotion, related_name='products', blank=True, verbose_name="Акції")
    article = models.CharField("Артикул", max_length=50, blank=True, null=True)
    code = models.CharField("Код товару", max_length=50, blank=True, null=True)
    description = models.TextField("Короткий опис", blank=True)
    full_description = models.TextField("Повний опис", blank=True)
    slug = models.SlugField('URL', max_length=250)
    price = models.DecimalField("Ціна закупки", max_digits=12, decimal_places=2, default=0)
    retail_price = models.DecimalField("Роздрібна ціна", max_digits=12, decimal_places=0, default=0)  
    quantity = models.IntegerField("Кількість на складі", default=1)
    warranty = models.IntegerField("Гарантія, місяців", default=0)
    country = models.CharField("Країна виробництва", max_length=50, blank=True, null=True)
    #main_image = models.ImageField("Основне зображення", upload_to='images/products/{category.slug}', null=True, blank=True)
    main_image = models.ImageField(upload_to=get_image_upload_path)
    images = models.ManyToManyField('ProductImage', blank=True, related_name='product_images')
    available = models.BooleanField("Наявність", default=True)
    created_at = models.DateTimeField('Дата створення', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Дата оновлення', auto_now=True)
    discount = models.IntegerField('Знижка, %', default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    attributes = models.JSONField('Характеристики', blank=True, null=True)
    additional_attributes = models.JSONField('Додаткові характеристики', blank=True, null=True)
    
    def get_promotion_labels(self):
        labels = []
        for promotion in self.promotions.all():
            if promotion.is_active:
                if promotion.promotion_type == 'week':
                    labels.append('Товар тижня')
                elif promotion.promotion_type == 'black_friday':
                    labels.append('Чорна п\'ятниця')
                elif promotion.promotion_type == 'recommended':
                    labels.append('Рекомендуємо')
                elif promotion.promotion_type == 'sale':
                    labels.append('Акція')
                elif promotion.promotion_type == 'new':
                    labels.append('Новинка')
                elif promotion.promotion_type == 'best_seller':
                    labels.append('Хіт продажів')       
        return labels


    def clean_html(self, text):
        """
        Очищає HTML-теги з тексту.
        """
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text()

    def save(self, *args, **kwargs):
        # Очищаємо повний опис від HTML-тегів перед збереженням
        if self.full_description:
            self.full_description = self.clean_html(self.full_description)  # Виклик через self
        super(Product, self).save(*args, **kwargs)


    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товари'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("shop:product-detail", args=[str(self.slug)])
    
    def is_available(self):
        return self.available and self.quantity > 0 

    # функція, щоб відображати "Товар недоступний", навіть якщо товар існує, але його немає в наявності.
    def availability_text(self):
        if self.is_available():
            return None  # Ціна відображається, якщо товар доступний
        else:
            return "Товар недоступний"
    
    @property
    def full_image_url(self):
        """
        Returns:
            str: The full image URL.
        """
        return self.main_image.url if self.main_image else ''

class Property(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    category = models.ManyToManyField(Category, related_name='properties', blank=True)
       
    class Meta:
        verbose_name = 'Властивість'    
        verbose_name_plural = 'Властивості'
        
    def category_list(self):
        return ", ".join([category.name for category in self.category.all()])
    category_list.short_description = 'Категорії'

    def __str__(self):
        return self.name
    
    
class PropertyValue(models.Model):
    property = models.ForeignKey(Property, related_name='values', on_delete=models.CASCADE)
    value = models.CharField(max_length=255)
    
    class Meta:
        verbose_name = 'Значення властивості'
        verbose_name_plural = 'Значення властивостей'

    def __str__(self):
        return self.value
    
class ProductImage(models.Model):
    """
    Модель для додаткових зображень товару.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='images/products/additional/{product.code}')

    class Meta:
        verbose_name = 'Додаткове зображення'
        verbose_name_plural = 'Додаткові зображення'

    def __str__(self):
        return f"{self.product.title} - додаткове зображення"
    
    
class VisitLog(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    page = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.user.username} - {self.page} - {self.date}'
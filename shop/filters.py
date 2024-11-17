import django_filters
from .models import Product, Category

class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label='Назва')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte', label='Мінімальна ціна')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte', label='Максимальна ціна')
    brand = django_filters.CharFilter(lookup_expr='icontains', label='Бренд')
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all(), label='Категорія')

    class Meta:
        model = Product
        fields = ['name', 'price_min', 'price_max', 'brand', 'category']

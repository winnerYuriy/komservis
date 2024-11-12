from django.contrib.sitemaps import Sitemap
from shop.models import Product

class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Product.objects.all()

    def lastmod(self, obj):
        return obj.updated_at  # Замість `updated_at` використовуйте поле, що зберігає дату останнього оновлення
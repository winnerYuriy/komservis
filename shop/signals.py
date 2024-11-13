from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Product

@receiver(pre_save, sender=Product)
def update_category_slug(sender, instance, **kwargs):
    # Перевірка на наявність слагу у категорії
    if instance.product.category and not instance.product.category.slug:
        # Генерація слагу для категорії, якщо його ще немає
        instance.product.category.slug = instance.product.category.name.lower().replace(" ", "-")
        instance.product.category.save()

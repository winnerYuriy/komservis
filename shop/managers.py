from django.db import models
from .models import Product


class ProductManager(models.Manager):
    def get_queryset(self):
        """
        Returns a queryset of products that are available.

        Returns:
            QuerySet: A queryset of products that are available.
        """
        return super(ProductManager, self).get_queryset().filter(available=True)


class ProductProxy(Product):

    objects = ProductManager()

    def __str__(self):
        return self.title   

    def save(self, *args, **kwargs):
        """
        Save the current instance to the database.
        """
        super(ProductProxy, self).save(*args, **kwargs)
    
    class Meta:
        proxy = True

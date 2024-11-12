from django.db import models
from django.contrib.auth.models import User


class Avatar(models.Model):
    image = models.ImageField("Аватар", upload_to='avatars/')
    
    class Meta:
        verbose_name = 'Аватар'
        verbose_name_plural = 'Аватари'

    def __str__(self):
        return f"Avatar {self.id}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=250, blank=True)
    is_subscribed = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    

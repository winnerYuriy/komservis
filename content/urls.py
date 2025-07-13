from django.urls import path
from .views import index, about, article_list

app_name = 'content'

urlpatterns = [
    path('', index, name='content'),
    path('about/', about, name='about'),
    path('articles/', article_list , name='article-list'),
]
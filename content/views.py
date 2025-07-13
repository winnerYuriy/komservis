from django.shortcuts import render
from .models import Article

# Create your views here.

def index(request):
    return render(request, 'content/index.html')


def about(request):
    return render(request, 'content/about.html')


def article_list(request):
    articles = Article.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'content/article_list.html', {'articles': articles})
from .models import Category

def main_menu_categories(request):
    categories = Category.objects.filter(level=0)  # Тільки верхні категорії
    return {'main_menu_categories': categories}

def categories_processor(request):
    categories = Category.objects.all()
    return {'categories': categories}
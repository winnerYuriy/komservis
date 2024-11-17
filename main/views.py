from django.shortcuts import render


def index(request):
    return render(request, 'main/index.html')

def handle_404(request, exception):
    return render(request, 'main/404.html', status=404)
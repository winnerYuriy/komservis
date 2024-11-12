from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django_email_verification import urls as email_urls
from . import views
from django.contrib.sitemaps.views import sitemap
from .sitemaps import ProductSitemap
from django.views.generic import TemplateView



sitemaps = {
    'products': ProductSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('shop/', include('shop.urls', namespace='shop')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('account/', include('account.urls', namespace='account')),
    path('payment/', include('payment.urls', namespace='payment')),
    path("recommend/", include('recommend.urls', namespace='recommend')),
    path('email/', include(email_urls), name='email-verification'),
    path('api/v1/', include('api.urls', namespace='api')),
    path('', views.index, name='index'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]

if settings.DEBUG:
    
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
admin.site.site_header = 'Адміністративна панель'
admin.site.index_title = 'Інтернет-магазин "КОМСЕРВІС"'
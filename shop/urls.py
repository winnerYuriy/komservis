from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import *

app_name = 'shop'

urlpatterns = [
    path('', ProductListView.as_view(), name='products'),
    path("search_products/", search_products, name="search-products"),
    path('category/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),
    path('price_list/', PriceListView.as_view(), name='price-list'),
    path('download_price_excel/', download_price_excel, name='download-price-excel'),
    path('import_products/', import_products_view, name='import-products'),
    path('product/<slug:slug>/', products_detail_view, name='product-detail'),
    path('sidebar/', sidebar_view, name='sidebar-view'),
    path('brands/', brands_list, name='brands_list'),
    path('brands/<slug:brand_slug>/', brand_products, name='brand_products'),
    path('products/', product_list, name='product_list'),
    path('visit_statistics/', visit_statistics_view, name='visit-statistics'),
   # path('admin/shop/product/update_products_with_api/', update_products_with_api_data, name='update_products_with_api_data'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # This line sends any web request starting with 'api/' to your inventory_api app
    path('api/', include('inventory_api.urls')), 
]
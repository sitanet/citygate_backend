from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('api/', include('api.urls')),
    path('content/', include('content.urls')),
    path('banner/', include('banner.urls')),
    path('', include('content.urls')),  # Default to content home
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
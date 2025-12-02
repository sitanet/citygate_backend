from django.urls import path
from . import views

app_name = 'media'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Media URLs - following existing content URL pattern
    path('media/', views.media_list, name='media_list'),
    path('media/create/', views.media_create, name='media_create'),
    path('media/<int:pk>/', views.media_detail, name='media_detail'),
    path('media/<int:pk>/edit/', views.media_update, name='media_update'),
    path('media/<int:pk>/delete/', views.media_delete, name='media_delete'),
    path('media/<int:pk>/toggle-live/', views.toggle_live_status, name='toggle_live'),
]
from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Content URLs
    path('content/', views.content_list, name='content_list'),
    path('content/create/', views.content_create, name='content_create'),
    path('content/<int:pk>/edit/', views.content_update, name='content_update'),
    path('content/<int:pk>/delete/', views.content_delete, name='content_delete'),
    
    # Event URLs
    path('events/', views.event_list, name='event_list'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:pk>/edit/', views.event_update, name='event_update'),
    path('events/<int:pk>/delete/', views.event_delete, name='event_delete'),
    
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]
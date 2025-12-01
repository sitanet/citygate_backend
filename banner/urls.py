from django.urls import path
from . import views

app_name = 'banner'

urlpatterns = [
    path('', views.banner_list, name='banner_list'),
    path('create/', views.banner_create, name='banner_create'),
    path('<int:pk>/edit/', views.banner_update, name='banner_update'),
    path('<int:pk>/delete/', views.banner_delete, name='banner_delete'),
]
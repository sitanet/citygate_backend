from django.urls import path
from . import views

app_name = 'streaming'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('chat/', views.chat_moderation, name='chat_moderation'),
    path('chat/<int:pk>/moderate/', views.moderate_message, name='moderate_message'),
    path('analytics/', views.analytics, name='analytics'),
]
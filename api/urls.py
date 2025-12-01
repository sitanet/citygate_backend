from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.login_view, name='api_login'),
    path('auth/logout/', views.logout_view, name='api_logout'),
    path('auth/signup/', views.signup_view, name='api_signup'),
    path('auth/current-user/', views.current_user_view, name='api_current_user'),
    
    # Content endpoints
    path('content/', views.ContentListView.as_view(), name='api_content'),
    path('content/live/', views.LiveContentView.as_view(), name='api_live_content'),
    path('content/recent/', views.RecentContentView.as_view(), name='api_recent_content'),
    
    # Event endpoints
    path('events/', views.EventListView.as_view(), name='api_events'),
    path('events/upcoming/', views.UpcomingEventsView.as_view(), name='api_upcoming_events'),
    
    # Category endpoints
    path('categories/', views.ServiceCategoryListView.as_view(), name='api_categories'),
    
    # Banner endpoints
    path('banners/', views.BannerListView.as_view(), name='api_banners'),
    
    # Statistics endpoint
    path('statistics/', views.statistics_view, name='api_statistics'),
]
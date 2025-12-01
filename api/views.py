from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from content.models import Content, Event, ServiceCategory
from banner.models import Banner
from .serializers import (
    UserSerializer, ContentSerializer, EventSerializer,
    ServiceCategorySerializer, BannerSerializer, AuthTokenSerializer,
    UserRegistrationSerializer
)

User = get_user_model()

# Authentication Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    serializer = AuthTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    
    # Update user online status
    user.is_online = True
    user.save()
    
    token, created = Token.objects.get_or_create(user=user)
    
    return Response({
        'token': token.key,
        'user': UserSerializer(user).data
    })

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def signup_view(request):
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Create the user
            user = serializer.save()
            
            # Create authentication token
            token, created = Token.objects.get_or_create(user=user)
            
            # Set user as online
            user.is_online = True
            user.save()
            
            # Return user data and token
            return Response({
                'message': 'User created successfully',
                'user': UserSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to create user: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'error': 'Invalid data provided',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout_view(request):
    if request.user.is_authenticated:
        request.user.is_online = False
        request.user.save()
        
        # Delete the token
        try:
            request.user.auth_token.delete()
        except:
            pass
    
    return Response({'message': 'Logged out successfully'})

@api_view(['GET'])
def current_user_view(request):
    if request.user.is_authenticated:
        return Response(UserSerializer(request.user).data)
    return Response({'error': 'Not authenticated'}, status=401)

# Content Views
class ContentListView(generics.ListAPIView):
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Content.objects.filter(status='published')
        
        content_type = self.request.query_params.get('type', None)
        category = self.request.query_params.get('category', None)
        search = self.request.query_params.get('search', None)
        
        if content_type:
            queryset = queryset.filter(type=content_type)
        if category:
            queryset = queryset.filter(category__name=category)
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        return queryset

class LiveContentView(generics.ListAPIView):
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Content.objects.filter(is_live=True, status='published')

class RecentContentView(generics.ListAPIView):
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Content.objects.filter(status='published')[:10]

# Event Views
class EventListView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Event.objects.all()

class UpcomingEventsView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Event.objects.filter(date_time__gte=timezone.now())[:10]

# Category Views
class ServiceCategoryListView(generics.ListAPIView):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

# Banner Views
class BannerListView(generics.ListAPIView):
    serializer_class = BannerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        now = timezone.now()
        return Banner.objects.filter(
            status='active',
            start_date__lte=now
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
        )

# Statistics View
@api_view(['GET'])
def statistics_view(request):
    stats = {
        'total_users': User.objects.count(),
        'online_users': User.objects.filter(is_online=True).count(),
        'total_content': Content.objects.filter(status='published').count(),
        'live_content': Content.objects.filter(is_live=True, status='published').count(),
        'upcoming_events': Event.objects.filter(date_time__gte=timezone.now()).count(),
        'active_banners': Banner.objects.filter(status='active').count(),
    }
    return Response(stats)
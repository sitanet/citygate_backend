from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from content.models import Content, Event, ServiceCategory
from banner.models import Banner

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()  # Combine first_name + last_name
    
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'profile_image_url', 'is_online']
        
    def get_name(self, obj):
        return obj.full_name or obj.username

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'confirm_password']
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value
    
    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs
    
    def create(self, validated_data):
        # Remove confirm_password from validated_data
        validated_data.pop('confirm_password', None)
        
        # Extract password
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=password
        )
        
        return user

class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'display_name', 'color']

class ContentSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', allow_null=True)
    duration = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Content
        fields = [
            'id', 'title', 'description', 'thumbnail_url', 'video_url', 'audio_url',
            'type', 'category', 'created_at', 'duration', 'is_live', 
            'pastor', 'scripture', 'time_ago'
        ]
    
    def get_duration(self, obj):
        if obj.duration_seconds:
            hours = obj.duration_seconds // 3600
            minutes = (obj.duration_seconds % 3600) // 60
            seconds = obj.duration_seconds % 60
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        return None
    
    def get_time_ago(self, obj):
        from django.utils import timezone
        import math
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} {'day' if diff.days == 1 else 'days'} ago"
        elif diff.seconds > 3600:
            hours = math.floor(diff.seconds / 3600)
            return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
        elif diff.seconds > 60:
            minutes = math.floor(diff.seconds / 60)
            return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
        else:
            return "Just now"

class EventSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', allow_null=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'thumbnail_url', 
            'date_time', 'is_live', 'category'
        ]

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = [
            'id', 'title', 'description', 'banner_type', 'position',
            'image', 'mobile_image', 'link_url', 'link_text',
            'start_date', 'end_date', 'is_featured'
        ]

class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            
            if user:
                if not user.is_active:
                    msg = 'User account is disabled.'
                    raise serializers.ValidationError(msg, code='authorization')
            else:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "username" and "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
# content/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ServiceCategory(models.Model):
    # Matching your Flutter ServiceCategory enum
    CATEGORY_CHOICES = [
        ('morningDew', 'The Morning Dew'),
        ('feastOfGlory', 'Feast of Glory'),
        ('wordAndPrayer', 'Word & Prayer'),
        ('schoolOfChrist', 'The School of Christ'),
        ('kingdomBusiness', 'Kingdom Business'),
        ('sundayService', 'Sunday Service'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#D4AF37')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name

    class Meta:
        verbose_name_plural = "Service Categories"
        ordering = ['name']

class Content(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('live', 'Live'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Media fields - matching Flutter field names
    thumbnail_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    audio_url = models.URLField(blank=True, null=True)
    
    # Content metadata
    type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)  # Changed from content_type
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='published')
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, blank=True, null=True)
    
    # Duration in seconds to match Flutter Duration
    duration_seconds = models.IntegerField(blank=True, null=True)
    
    # Content details
    is_live = models.BooleanField(default=False)
    pastor = models.CharField(max_length=100, blank=True, null=True)
    scripture = models.CharField(max_length=200, blank=True, null=True)
    
    # Management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_content')
    created_at = models.DateTimeField(auto_now_add=True)  # Matches Flutter createdAt
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    thumbnail_url = models.URLField(blank=True, null=True)  # Changed to match Flutter
    
    # Event timing - matching Flutter field names
    date_time = models.DateTimeField()  # Changed from start_datetime to match Flutter
    end_date_time = models.DateTimeField(blank=True, null=True)
    is_live = models.BooleanField(default=False)
    
    # Related content
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, blank=True, null=True)
    
    # Management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date_time']  # Changed to match Flutter
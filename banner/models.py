from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Banner(models.Model):
    BANNER_TYPE_CHOICES = [
        ('main', 'Main Banner'),
        ('event', 'Event Banner'),
        ('announcement', 'Announcement'),
        ('promotion', 'Promotion'),
    ]
    
    POSITION_CHOICES = [
        ('top', 'Top'),
        ('middle', 'Middle'),
        ('bottom', 'Bottom'),
        ('sidebar', 'Sidebar'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('scheduled', 'Scheduled'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    banner_type = models.CharField(max_length=20, choices=BANNER_TYPE_CHOICES)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Media - using URLs to match the corrected approach
    image = models.URLField(help_text="Main banner image URL")
    mobile_image = models.URLField(blank=True, null=True, help_text="Mobile optimized image URL")
    
    # Links
    link_url = models.URLField(blank=True, null=True)
    link_text = models.CharField(max_length=100, blank=True)
    
    # Scheduling
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    
    # Display settings
    order = models.IntegerField(default=0, help_text="Lower numbers display first")
    is_featured = models.BooleanField(default=False)
    
    # Management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', '-created_at']
from django.db import models
from django.contrib.auth import get_user_model
from content.models import ServiceCategory
import uuid
from django.utils import timezone

User = get_user_model()

def media_upload_path(instance, filename):
    """Generate upload path for media files"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'media/{instance.content_type}/{filename}'

def thumbnail_upload_path(instance, filename):
    """Generate upload path for thumbnails"""
    ext = filename.split('.')[-1]
    filename = f'thumb_{uuid.uuid4()}.{ext}'
    return f'thumbnails/{filename}'

class MediaContent(models.Model):
    """Media content with YouTube and Waystream integration"""
    
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('live', 'Live Stream'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    # Basic Info
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # YouTube Integration
    youtube_video_id = models.CharField(max_length=50, blank=True, help_text="YouTube Video ID for live streams")
    youtube_channel_id = models.CharField(max_length=50, blank=True, help_text="YouTube Channel ID")
    youtube_thumbnail_url = models.URLField(blank=True)
    
    # Waystream Integration  
    waystream_embed_url = models.URLField(blank=True, help_text="Waystream embed URL for audio")
    waystream_stream_id = models.CharField(max_length=100, blank=True)
    
    # General URLs (fallback for other content)
    video_url = models.URLField(blank=True, help_text="Direct video URL")
    audio_url = models.URLField(blank=True, help_text="Direct audio URL")
    thumbnail_url = models.URLField(blank=True)
    
    # File uploads (optional local storage)
    media_file = models.FileField(upload_to=media_upload_path, blank=True, null=True)
    thumbnail_file = models.ImageField(upload_to=thumbnail_upload_path, blank=True, null=True)
    
    # Content Details
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, blank=True, null=True)
    pastor = models.CharField(max_length=100, blank=True)
    scripture = models.CharField(max_length=200, blank=True)
    duration = models.DurationField(blank=True, null=True)
    
    # Live Stream Status
    is_live = models.BooleanField(default=False)
    scheduled_start = models.DateTimeField(blank=True, null=True)
    actual_start = models.DateTimeField(blank=True, null=True)
    actual_end = models.DateTimeField(blank=True, null=True)
    
    # Management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_media')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Media Content"
        verbose_name_plural = "Media Content"
        
    def __str__(self):
        return f"{self.title} ({self.content_type})"
    
    @property
    def playback_url(self):
        """Get the appropriate playback URL based on content type"""
        if self.content_type == 'live' and self.youtube_video_id:
            return f"https://www.youtube.com/embed/{self.youtube_video_id}"
        elif self.content_type == 'audio' and self.waystream_embed_url:
            return self.waystream_embed_url
        elif self.video_url:
            return self.video_url
        elif self.audio_url:
            return self.audio_url
        elif self.media_file:
            return self.media_file.url
        return None
    
    @property
    def thumbnail_display_url(self):
        """Get thumbnail URL - prioritize uploaded file, then external URLs"""
        if self.thumbnail_file:
            return self.thumbnail_file.url
        elif self.youtube_thumbnail_url:
            return self.youtube_thumbnail_url
        elif self.thumbnail_url:
            return self.thumbnail_url
        return None
    
    @property
    def embed_html(self):
        """Get HTML embed code for the content"""
        if self.content_type == 'live' and self.youtube_video_id:
            return f'''
            <iframe 
                width="100%" 
                height="315" 
                src="https://www.youtube.com/embed/{self.youtube_video_id}?autoplay=1" 
                title="{self.title}"
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
            </iframe>
            '''
        elif self.content_type == 'audio' and self.waystream_embed_url:
            return f'''
            <iframe 
                src="{self.waystream_embed_url}"
                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;"
                title="{self.title}"
                allowfullscreen
                loading="lazy">
            </iframe>
            '''
        return None


class MediaViewer(models.Model):
    """Track viewers for media content and live streams"""
    media_content = models.ForeignKey(MediaContent, on_delete=models.CASCADE, related_name='viewers')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Viewing Session
    session_id = models.UUIDField(default=uuid.uuid4, editable=False)
    started_at = models.DateTimeField(auto_now_add=True)
    last_heartbeat = models.DateTimeField(auto_now=True)
    duration_watched = models.DurationField(default=timezone.timedelta(0))
    
    # Device Info
    device_type = models.CharField(max_length=50, blank=True)  # mobile, web, etc.
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['media_content', 'user', 'session_id']
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} watching {self.media_content.title}"
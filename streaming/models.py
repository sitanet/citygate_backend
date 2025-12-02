from django.db import models
from django.contrib.auth import get_user_model
from media.models import MediaContent
import uuid

User = get_user_model()

class LiveStreamSession(models.Model):
    """Track live streaming sessions"""
    media_content = models.ForeignKey(MediaContent, on_delete=models.CASCADE, related_name='stream_sessions')
    
    # Session Info
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    
    # YouTube Live Status
    youtube_broadcast_status = models.CharField(max_length=20, blank=True)
    youtube_life_cycle_status = models.CharField(max_length=20, blank=True)
    
    # Analytics
    peak_concurrent_viewers = models.IntegerField(default=0)
    total_view_time = models.BigIntegerField(default=0)  # in seconds
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Stream: {self.media_content.title} - {self.started_at}"


class StreamChat(models.Model):
    """Live chat for streams"""
    media_content = models.ForeignKey(MediaContent, on_delete=models.CASCADE, related_name='chat_messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    message = models.TextField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Moderation
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='moderated_messages')
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"


class StreamAnalytics(models.Model):
    """Analytics for completed streams"""
    stream_session = models.OneToOneField(LiveStreamSession, on_delete=models.CASCADE, related_name='analytics')
    
    # Viewer stats
    total_unique_viewers = models.IntegerField(default=0)
    average_watch_duration = models.DurationField(blank=True, null=True)
    
    # Engagement
    total_chat_messages = models.IntegerField(default=0)
    total_reactions = models.IntegerField(default=0)
    
    # Technical
    stream_quality = models.CharField(max_length=10, blank=True)
    total_bandwidth_used = models.BigIntegerField(default=0)  # in bytes
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analytics: {self.stream_session.media_content.title}"
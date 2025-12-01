from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string
from datetime import timedelta
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('finance', 'Finance'),
        ('admin', 'Admin'),
        ('banner', 'Banner Manager'),
        ('content', 'Content Manager'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    profile_image_url = models.URLField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True)
    is_online = models.BooleanField(default=False)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email_verified = models.BooleanField(default=False)  # Add this line

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    class Meta:
        ordering = ['-created_at']

class EmailVerification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_verifications')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)  # 10 minutes expiry
        super().save(*args, **kwargs)
    
    def generate_code(self):
        return ''.join(random.choices(string.digits, k=6))
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired()
    
    class Meta:
        ordering = ['-created_at']
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div
from crispy_forms.bootstrap import Field, InlineRadios
from .models import MediaContent
from content.models import ServiceCategory

class MediaContentForm(forms.ModelForm):
    """Form for creating and updating media content"""
    
    class Meta:
        model = MediaContent
        fields = [
            'title', 'description', 'type', 'status', 'category',
            'youtube_video_id', 'youtube_channel_id', 'youtube_thumbnail_url',
            'waystream_embed_url', 'waystream_stream_id',
            'video_url', 'audio_url', 'thumbnail_url',
            'media_file', 'thumbnail_file',
            'pastor', 'scripture', 'duration_seconds',
            'scheduled_start'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'scheduled_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'duration_seconds': forms.NumberInput(attrs={'step': 1, 'min': 0}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-md-8 mb-0'),
                Column('type', css_class='form-group col-md-4 mb-0'),
            ),
            'description',
            Row(
                Column('status', css_class='form-group col-md-6 mb-0'),
                Column('category', css_class='form-group col-md-6 mb-0'),
            ),
            
            # YouTube Integration
            Div(
                '<h5 class="mt-4 mb-3">YouTube Integration</h5>',
                Row(
                    Column('youtube_video_id', css_class='form-group col-md-6 mb-0'),
                    Column('youtube_channel_id', css_class='form-group col-md-6 mb-0'),
                ),
                'youtube_thumbnail_url',
            ),
            
            # Waystream Integration
            Div(
                '<h5 class="mt-4 mb-3">Waystream Integration</h5>',
                Row(
                    Column('waystream_embed_url', css_class='form-group col-md-8 mb-0'),
                    Column('waystream_stream_id', css_class='form-group col-md-4 mb-0'),
                ),
            ),
            
            # General URLs
            Div(
                '<h5 class="mt-4 mb-3">General URLs</h5>',
                Row(
                    Column('video_url', css_class='form-group col-md-6 mb-0'),
                    Column('audio_url', css_class='form-group col-md-6 mb-0'),
                ),
                'thumbnail_url',
            ),
            
            # File Uploads
            Div(
                '<h5 class="mt-4 mb-3">File Uploads</h5>',
                Row(
                    Column('media_file', css_class='form-group col-md-6 mb-0'),
                    Column('thumbnail_file', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            
            # Content Details
            Div(
                '<h5 class="mt-4 mb-3">Content Details</h5>',
                Row(
                    Column('pastor', css_class='form-group col-md-6 mb-0'),
                    Column('scripture', css_class='form-group col-md-6 mb-0'),
                ),
                Row(
                    Column('duration_seconds', css_class='form-group col-md-6 mb-0'),
                    Column('scheduled_start', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            
            Submit('submit', 'Save Media Content', css_class='btn btn-primary')
        )
        
        # Set help texts
        self.fields['youtube_video_id'].help_text = 'YouTube Video ID for embedding'
        self.fields['waystream_embed_url'].help_text = 'Full Waystream embed URL'
        self.fields['duration_seconds'].help_text = 'Duration in seconds'
    
    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('type')
        
        # Validation based on content type
        if content_type == 'live':
            youtube_video_id = cleaned_data.get('youtube_video_id')
            if not youtube_video_id:
                self.add_error('youtube_video_id', 'YouTube Video ID is required for live streams')
        
        elif content_type == 'audio':
            waystream_url = cleaned_data.get('waystream_embed_url')
            audio_url = cleaned_data.get('audio_url')
            media_file = cleaned_data.get('media_file')
            
            if not any([waystream_url, audio_url, media_file]):
                self.add_error('waystream_embed_url', 'At least one audio source is required')
        
        return cleaned_data
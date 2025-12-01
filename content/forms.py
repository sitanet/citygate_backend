from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Content, Event, ServiceCategory

class CategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'display_name', 'color', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('display_name', css_class='form-group col-md-6 mb-3'),
            ),
            'color',
            'description',
            Submit('submit', 'Save Category', css_class='btn btn-primary')
        )

class ContentForm(forms.ModelForm):
    # Custom duration field to handle time input
    duration_hours = forms.IntegerField(required=False, min_value=0, max_value=23, initial=0, label="Hours")
    duration_minutes = forms.IntegerField(required=False, min_value=0, max_value=59, initial=0, label="Minutes")
    duration_seconds_field = forms.IntegerField(required=False, min_value=0, max_value=59, initial=0, label="Seconds")
    
    class Meta:
        model = Content
        fields = [
            'title', 'description', 'type', 'status', 'category',
            'thumbnail_url', 'video_url', 'audio_url',
            'pastor', 'scripture', 'is_live'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing existing content, populate duration fields
        if self.instance and self.instance.pk and self.instance.duration_seconds:
            total_seconds = self.instance.duration_seconds
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            self.initial['duration_hours'] = hours
            self.initial['duration_minutes'] = minutes
            self.initial['duration_seconds_field'] = seconds
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-md-8 mb-3'),
                Column('type', css_class='form-group col-md-4 mb-3'),
            ),
            'description',
            Row(
                Column('category', css_class='form-group col-md-6 mb-3'),
                Column('status', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('pastor', css_class='form-group col-md-6 mb-3'),
                Column('scripture', css_class='form-group col-md-6 mb-3'),
            ),
            'thumbnail_url',
            Row(
                Column('video_url', css_class='form-group col-md-6 mb-3'),
                Column('audio_url', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('duration_hours', css_class='form-group col-md-4 mb-3'),
                Column('duration_minutes', css_class='form-group col-md-4 mb-3'),
                Column('duration_seconds_field', css_class='form-group col-md-4 mb-3'),
            ),
            'is_live',
            Submit('submit', 'Save Content', css_class='btn btn-primary')
        )

    def clean(self):
        cleaned_data = super().clean()
        
        # Convert duration fields to total seconds
        hours = cleaned_data.get('duration_hours', 0) or 0
        minutes = cleaned_data.get('duration_minutes', 0) or 0
        seconds = cleaned_data.get('duration_seconds_field', 0) or 0
        
        total_seconds = (hours * 3600) + (minutes * 60) + seconds
        
        if total_seconds > 0:
            cleaned_data['duration_seconds'] = total_seconds
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set duration_seconds from cleaned data
        duration_seconds = self.cleaned_data.get('duration_seconds')
        if duration_seconds:
            instance.duration_seconds = duration_seconds
        
        if commit:
            instance.save()
        return instance

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'thumbnail_url', 'date_time', 'end_date_time', 
                 'is_live', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Format datetime for HTML input
        if self.instance and self.instance.pk:
            if self.instance.date_time:
                self.initial['date_time'] = self.instance.date_time.strftime('%Y-%m-%dT%H:%M')
            if self.instance.end_date_time:
                self.initial['end_date_time'] = self.instance.end_date_time.strftime('%Y-%m-%dT%H:%M')
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            'description',
            'thumbnail_url',
            Row(
                Column('date_time', css_class='form-group col-md-6 mb-3'),
                Column('end_date_time', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('category', css_class='form-group col-md-6 mb-3'),
                Column('is_live', css_class='form-group col-md-6 mb-3'),
            ),
            Submit('submit', 'Save Event', css_class='btn btn-primary')
        )
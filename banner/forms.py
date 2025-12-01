from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Banner

class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = [
            'title', 'description', 'banner_type', 'position', 'status',
            'image', 'mobile_image', 'link_url', 'link_text',
            'start_date', 'end_date', 'order', 'is_featured'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-md-8 mb-3'),
                Column('banner_type', css_class='form-group col-md-4 mb-3'),
            ),
            'description',
            Row(
                Column('position', css_class='form-group col-md-6 mb-3'),
                Column('status', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('image', css_class='form-group col-md-6 mb-3'),
                Column('mobile_image', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('link_url', css_class='form-group col-md-8 mb-3'),
                Column('link_text', css_class='form-group col-md-4 mb-3'),
            ),
            Row(
                Column('start_date', css_class='form-group col-md-6 mb-3'),
                Column('end_date', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('order', css_class='form-group col-md-6 mb-3'),
                Column('is_featured', css_class='form-group col-md-6 mb-3'),
            ),
            Submit('submit', 'Save Banner', css_class='btn btn-primary')
        )
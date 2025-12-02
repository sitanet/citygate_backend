from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Content, Event, ServiceCategory
from .forms import ContentForm, EventForm, CategoryForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Content, Event, ServiceCategory
from .forms import ContentForm, EventForm, CategoryForm

def can_manage_content(user):
    """Check if user can manage content"""
    return user.role in ['admin', 'content'] or user.is_superuser

def can_view_content(user):
    """Check if user can view content dashboard"""
    return user.role in ['admin', 'content', 'finance', 'banner'] or user.is_superuser

@login_required
@user_passes_test(can_view_content)
def dashboard(request):
    """Main dashboard for content management - Enhanced with Media & Streaming"""
    # Get recent content (original)
    recent_content = Content.objects.filter(status='published').order_by('-created_at')[:5]
    
    # Get upcoming events (original)
    upcoming_events = Event.objects.filter(
        date_time__gte=timezone.now()
    ).order_by('date_time')[:5]
    
    # Get live content (original)
    live_content = Content.objects.filter(is_live=True, status='published')
    
    # Enhanced statistics with Media & Streaming
    stats = {
        # Original content stats
        'total_content': Content.objects.count(),
        'published_content': Content.objects.filter(status='published').count(),
        'draft_content': Content.objects.filter(status='draft').count(),
        'total_events': Event.objects.count(),
        'live_events': Event.objects.filter(is_live=True).count(),
        'upcoming_events': Event.objects.filter(date_time__gte=timezone.now()).count(),
        'total_categories': ServiceCategory.objects.count(),
        'videos': Content.objects.filter(type='video').count(),
        'audios': Content.objects.filter(type='audio').count(),
        'live_streams': Content.objects.filter(type='live').count(),
    }
    
    # Add media & streaming stats if apps exist
    try:
        from media.models import MediaContent
        from streaming.models import LiveStreamSession, StreamChat
        
        # Media stats
        stats.update({
            'total_media': MediaContent.objects.count(),
            'published_media': MediaContent.objects.filter(status='published').count(),
            'draft_media': MediaContent.objects.filter(status='draft').count(),
            'media_videos': MediaContent.objects.filter(type='video').count(),
            'media_audios': MediaContent.objects.filter(type='audio').count(),
            'media_live_streams': MediaContent.objects.filter(type='live').count(),
            'active_live_streams': MediaContent.objects.filter(type='live', is_live=True).count(),
        })
        
        # Streaming stats
        stats.update({
            'total_stream_sessions': LiveStreamSession.objects.count(),
            'active_sessions': LiveStreamSession.objects.filter(ended_at__isnull=True).count(),
            'total_chat_messages': StreamChat.objects.count(),
        })
        
        # Get recent media content
        recent_media = MediaContent.objects.filter(status='published').order_by('-created_at')[:5]
        
        # Get active live streams
        active_streams = MediaContent.objects.filter(type='live', is_live=True)
        
        # Get recent stream sessions
        recent_sessions = LiveStreamSession.objects.order_by('-started_at')[:5]
        
    except ImportError:
        # Media/streaming apps not installed
        stats.update({
            'total_media': 0,
            'published_media': 0,
            'active_live_streams': 0,
            'total_stream_sessions': 0,
            'active_sessions': 0,
            'media_videos': 0,
            'media_audios': 0,
        })
        recent_media = []
        active_streams = []
        recent_sessions = []
    
    # Get content by category (enhanced)
    content_by_category = ServiceCategory.objects.annotate(
        content_count=Count('content'),
        media_count=Count('mediacontent', distinct=True) if 'recent_media' in locals() else Count('content')
    ).order_by('-content_count')[:5]
    
    context = {
        'recent_content': recent_content,
        'upcoming_events': upcoming_events,
        'live_content': live_content,
        'stats': stats,
        'content_by_category': content_by_category,
        # New media & streaming context
        'recent_media': locals().get('recent_media', []),
        'active_streams': locals().get('active_streams', []),
        'recent_sessions': locals().get('recent_sessions', []),
        'has_media_app': 'recent_media' in locals(),
    }
    
    return render(request, 'content/dashboard.html', context)

# Keep all your existing views below this point...
# (content_list, content_create, event_list, etc. remain unchanged)

# ... rest of existing views remain the same ...
# Content Views

def content_list(request):
    """List all content with search and filtering"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    
    content = Content.objects.all().select_related('category', 'created_by')
    
    # Apply filters
    if search_query:
        content = content.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(pastor__icontains=search_query) |
            Q(scripture__icontains=search_query)
        )
    
    if category_filter:
        content = content.filter(category__id=category_filter)
        
    if type_filter:
        content = content.filter(type=type_filter)  # Fixed field name
        
    if status_filter:
        content = content.filter(status=status_filter)
    
    # Order by creation date (newest first)
    content = content.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(content, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = ServiceCategory.objects.all()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'categories': categories,
        'content_types': Content.CONTENT_TYPE_CHOICES,
        'status_choices': Content.STATUS_CHOICES,
    }
    return render(request, 'content/content_list.html', context)

@login_required
@user_passes_test(can_manage_content)
def content_detail(request, pk):
    """View content details"""
    content = get_object_or_404(Content, pk=pk)
    context = {
        'content': content,
    }
    return render(request, 'content/content_detail.html', context)

@login_required
@user_passes_test(can_manage_content)
def content_create(request):
    """Create new content"""
    if request.method == 'POST':
        form = ContentForm(request.POST)
        if form.is_valid():
            content = form.save(commit=False)
            content.created_by = request.user
            content.save()
            messages.success(request, f'Content "{content.title}" created successfully!')
            return redirect('content:content_detail', pk=content.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContentForm()
    
    context = {
        'form': form,
        'title': 'Create New Content',
        'action': 'Create',
    }
    return render(request, 'content/content_form.html', context)

@login_required
@user_passes_test(can_manage_content)
def content_update(request, pk):
    """Update existing content"""
    content = get_object_or_404(Content, pk=pk)
    
    if request.method == 'POST':
        form = ContentForm(request.POST, instance=content)
        if form.is_valid():
            content = form.save(commit=False)
            content.save()
            messages.success(request, f'Content "{content.title}" updated successfully!')
            return redirect('content:content_detail', pk=content.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContentForm(instance=content)
    
    context = {
        'form': form,
        'content': content,
        'title': 'Update Content',
        'action': 'Update',
    }
    return render(request, 'content/content_form.html', context)

@login_required
@user_passes_test(can_manage_content)
def content_delete(request, pk):
    """Delete content"""
    content = get_object_or_404(Content, pk=pk)
    
    if request.method == 'POST':
        title = content.title
        content.delete()
        messages.success(request, f'Content "{title}" deleted successfully!')
        return redirect('content:content_list')
    
    context = {
        'content': content,
    }
    return render(request, 'content/content_confirm_delete.html', context)

# Event Views - keeping existing structure but fixing field references
@login_required
@user_passes_test(can_manage_content)
def event_list(request):
    """List all events with search and filtering"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    
    events = Event.objects.all().select_related('category', 'created_by')
    
    # Apply filters
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if category_filter:
        events = events.filter(category__id=category_filter)
    
    # Status filtering
    now = timezone.now()
    if status_filter == 'upcoming':
        events = events.filter(date_time__gt=now)  # Fixed field name
    elif status_filter == 'past':
        events = events.filter(date_time__lt=now)   # Fixed field name
    elif status_filter == 'live':
        events = events.filter(is_live=True)
    
    # Order by start datetime
    events = events.order_by('-date_time')  # Fixed field name
    
    # Pagination
    paginator = Paginator(events, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = ServiceCategory.objects.all()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'categories': categories,
        'status_options': [
            ('', 'All Events'),
            ('upcoming', 'Upcoming'),
            ('live', 'Live Now'),
            ('past', 'Past Events'),
        ],
    }
    return render(request, 'content/event_list.html', context)

@login_required
@user_passes_test(can_manage_content)
def event_create(request):
    """Create new event"""
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, f'Event "{event.title}" created successfully!')
            return redirect('content:event_detail', pk=event.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventForm()
    
    context = {
        'form': form,
        'title': 'Create New Event',
        'action': 'Create',
    }
    return render(request, 'content/event_form.html', context)

@login_required
@user_passes_test(can_manage_content)
def event_detail(request, pk):
    """View event details"""
    event = get_object_or_404(Event, pk=pk)
    context = {
        'event': event,
    }
    return render(request, 'content/event_detail.html', context)

@login_required
@user_passes_test(can_manage_content)
def event_update(request, pk):
    """Update existing event"""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save()
            messages.success(request, f'Event "{event.title}" updated successfully!')
            return redirect('content:event_detail', pk=event.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventForm(instance=event)
    
    context = {
        'form': form,
        'event': event,
        'title': 'Update Event',
        'action': 'Update',
    }
    return render(request, 'content/event_form.html', context)

@login_required
@user_passes_test(can_manage_content)
def event_delete(request, pk):
    """Delete event"""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        title = event.title
        event.delete()
        messages.success(request, f'Event "{title}" deleted successfully!')
        return redirect('content:event_list')
    
    context = {
        'event': event,
    }
    return render(request, 'content/event_confirm_delete.html', context)

# Category Views
@login_required
@user_passes_test(can_manage_content)
def category_list(request):
    """List all service categories"""
    search_query = request.GET.get('search', '')
    
    categories = ServiceCategory.objects.annotate(
        content_count=Count('content'),
        event_count=Count('event')
    )
    
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) |
            Q(display_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    categories = categories.order_by('name')
    
    context = {
        'categories': categories,
        'search_query': search_query,
    }
    return render(request, 'content/category_list.html', context)

@login_required
@user_passes_test(can_manage_content)
def category_create(request):
    """Create new service category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.display_name}" created successfully!')
            return redirect('content:category_detail', pk=category.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Create New Category',
        'action': 'Create',
    }
    return render(request, 'content/category_form.html', context)

@login_required
@user_passes_test(can_manage_content)
def category_detail(request, pk):
    """View category details with related content and events"""
    category = get_object_or_404(ServiceCategory, pk=pk)
    
    # Get related content and events
    content_list = Content.objects.filter(category=category).order_by('-created_at')[:10]
    event_list = Event.objects.filter(category=category).order_by('-date_time')[:10]
    
    context = {
        'category': category,
        'content_list': content_list,
        'event_list': event_list,
        'content_count': Content.objects.filter(category=category).count(),
        'event_count': Event.objects.filter(category=category).count(),
    }
    return render(request, 'content/category_detail.html', context)

@login_required
@user_passes_test(can_manage_content)
def category_update(request, pk):
    """Update existing category"""
    category = get_object_or_404(ServiceCategory, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.display_name}" updated successfully!')
            return redirect('content:category_detail', pk=category.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': 'Update Category',
        'action': 'Update',
    }
    return render(request, 'content/category_form.html', context)

@login_required
@user_passes_test(can_manage_content)
def category_delete(request, pk):
    """Delete category"""
    category = get_object_or_404(ServiceCategory, pk=pk)
    
    # Check if category has related content or events
    content_count = Content.objects.filter(category=category).count()
    event_count = Event.objects.filter(category=category).count()
    
    if request.method == 'POST':
        if content_count > 0 or event_count > 0:
            messages.error(
                request, 
                f'Cannot delete category "{category.display_name}" because it has {content_count} content items and {event_count} events. Please reassign or delete them first.'
            )
            return redirect('content:category_detail', pk=category.pk)
        
        display_name = category.display_name
        category.delete()
        messages.success(request, f'Category "{display_name}" deleted successfully!')
        return redirect('content:category_list')
    
    context = {
        'category': category,
        'content_count': content_count,
        'event_count': event_count,
        'can_delete': content_count == 0 and event_count == 0,
    }
    return render(request, 'content/category_confirm_delete.html', context)
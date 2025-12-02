from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import MediaContent, MediaViewer
from content.models import ServiceCategory
from .forms import MediaContentForm
import json

def can_manage_content(user):
    """Check if user can manage content - following existing pattern"""
    return user.role in ['admin', 'content'] or user.is_superuser

def can_view_content(user):
    """Check if user can view content dashboard - following existing pattern"""
    return user.role in ['admin', 'content', 'finance', 'banner'] or user.is_superuser

@login_required
@user_passes_test(can_view_content)
def dashboard(request):
    """Main dashboard for media management"""
    # Get recent media content
    recent_media = MediaContent.objects.filter(status='published').order_by('-created_at')[:5]
    
    # Get live content
    live_media = MediaContent.objects.filter(is_live=True, status='published')
    
    # Get statistics
    stats = {
        'total_media': MediaContent.objects.count(),
        'published_media': MediaContent.objects.filter(status='published').count(),
        'draft_media': MediaContent.objects.filter(status='draft').count(),
        'live_streams': MediaContent.objects.filter(type='live', is_live=True).count(),
        'videos': MediaContent.objects.filter(type='video').count(),
        'audios': MediaContent.objects.filter(type='audio').count(),
    }
    
    # Get media by category
    media_by_category = ServiceCategory.objects.annotate(
        media_count=Count('mediacontent')
    ).order_by('-media_count')[:5]
    
    context = {
        'recent_media': recent_media,
        'live_media': live_media,
        'stats': stats,
        'media_by_category': media_by_category,
    }
    return render(request, 'media/dashboard.html', context)

@login_required
@user_passes_test(can_manage_content)
def media_list(request):
    """List all media content with search and filtering - following existing pattern"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    
    media = MediaContent.objects.all().select_related('category', 'created_by')
    
    # Apply filters - following existing pattern
    if search_query:
        media = media.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(pastor__icontains=search_query) |
            Q(scripture__icontains=search_query)
        )
    
    if category_filter:
        media = media.filter(category__id=category_filter)
        
    if type_filter:
        media = media.filter(type=type_filter)
        
    if status_filter:
        media = media.filter(status=status_filter)
    
    # Order by creation date (newest first)
    media = media.order_by('-created_at')
    
    # Pagination - following existing pattern
    paginator = Paginator(media, 20)
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
        'content_types': MediaContent.CONTENT_TYPE_CHOICES,
        'status_choices': MediaContent.STATUS_CHOICES,
    }
    return render(request, 'media/media_list.html', context)

@login_required
@user_passes_test(can_manage_content)
def media_detail(request, pk):
    """View media details"""
    media = get_object_or_404(MediaContent, pk=pk)
    context = {
        'media': media,
    }
    return render(request, 'media/media_detail.html', context)

@login_required
@user_passes_test(can_manage_content)
def media_create(request):
    """Create new media content - following existing pattern"""
    if request.method == 'POST':
        form = MediaContentForm(request.POST, request.FILES)
        if form.is_valid():
            media = form.save(commit=False)
            media.created_by = request.user
            media.save()
            messages.success(request, f'Media content "{media.title}" created successfully!')
            return redirect('media:media_detail', pk=media.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MediaContentForm()
    
    context = {
        'form': form,
        'title': 'Create New Media Content',
        'action': 'Create',
    }
    return render(request, 'media/media_form.html', context)

@login_required
@user_passes_test(can_manage_content)
def media_update(request, pk):
    """Update existing media content"""
    media = get_object_or_404(MediaContent, pk=pk)
    
    if request.method == 'POST':
        form = MediaContentForm(request.POST, request.FILES, instance=media)
        if form.is_valid():
            media = form.save()
            messages.success(request, f'Media content "{media.title}" updated successfully!')
            return redirect('media:media_detail', pk=media.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MediaContentForm(instance=media)
    
    context = {
        'form': form,
        'media': media,
        'title': 'Update Media Content',
        'action': 'Update',
    }
    return render(request, 'media/media_form.html', context)

@login_required
@user_passes_test(can_manage_content)
def media_delete(request, pk):
    """Delete media content"""
    media = get_object_or_404(MediaContent, pk=pk)
    
    if request.method == 'POST':
        title = media.title
        media.delete()
        messages.success(request, f'Media content "{title}" deleted successfully!')
        return redirect('media:media_list')
    
    context = {
        'media': media,
    }
    return render(request, 'media/media_confirm_delete.html', context)

@csrf_exempt
@login_required
@user_passes_test(can_manage_content)
def toggle_live_status(request, pk):
    """Toggle live status of media content - AJAX endpoint"""
    if request.method == 'POST':
        try:
            media = get_object_or_404(MediaContent, pk=pk, type='live')
            
            if media.is_live:
                # End the stream
                media.is_live = False
                media.actual_end = timezone.now()
                status_message = 'Stream ended successfully'
            else:
                # Start the stream
                media.is_live = True
                media.actual_start = timezone.now()
                media.actual_end = None
                status_message = 'Stream started successfully'
            
            media.save()
            
            return JsonResponse({
                'success': True,
                'is_live': media.is_live,
                'message': status_message
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
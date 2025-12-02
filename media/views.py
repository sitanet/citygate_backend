from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import MediaContent, MediaViewer
from content.models import ServiceCategory
import json

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_staff_user)
def media_management_view(request):
    """Main media management dashboard"""
    media_list = MediaContent.objects.all().order_by('-created_at')
    
    # Filter by content type
    content_type = request.GET.get('type')
    if content_type:
        media_list = media_list.filter(content_type=content_type)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        media_list = media_list.filter(status=status_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        media_list = media_list.filter(title__icontains=search_query)
    
    # Pagination
    paginator = Paginator(media_list, 20)
    page_number = request.GET.get('page')
    media_page = paginator.get_page(page_number)
    
    context = {
        'media_page': media_page,
        'content_types': MediaContent.CONTENT_TYPE_CHOICES,
        'status_choices': MediaContent.STATUS_CHOICES,
        'current_type': content_type,
        'current_status': status_filter,
        'search_query': search_query,
        'total_media': MediaContent.objects.count(),
        'published_media': MediaContent.objects.filter(status='published').count(),
        'live_streams': MediaContent.objects.filter(content_type='live', is_live=True).count(),
    }
    
    return render(request, 'media/management_dashboard.html', context)

@login_required
@user_passes_test(is_staff_user)
def media_create_view(request):
    """Create new media content"""
    if request.method == 'POST':
        try:
            media_content = MediaContent(
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                content_type=request.POST.get('content_type'),
                status=request.POST.get('status', 'draft'),
                youtube_video_id=request.POST.get('youtube_video_id', ''),
                waystream_embed_url=request.POST.get('waystream_embed_url', ''),
                video_url=request.POST.get('video_url', ''),
                audio_url=request.POST.get('audio_url', ''),
                thumbnail_url=request.POST.get('thumbnail_url', ''),
                pastor=request.POST.get('pastor', ''),
                scripture=request.POST.get('scripture', ''),
                created_by=request.user
            )
            
            # Handle category
            category_id = request.POST.get('category')
            if category_id:
                try:
                    media_content.category = ServiceCategory.objects.get(id=category_id)
                except ServiceCategory.DoesNotExist:
                    pass
            
            # Handle scheduled start
            scheduled_start = request.POST.get('scheduled_start')
            if scheduled_start:
                try:
                    media_content.scheduled_start = timezone.datetime.fromisoformat(scheduled_start)
                except:
                    pass
            
            media_content.save()
            
            messages.success(request, f'Media content "{media_content.title}" created successfully!')
            return redirect('media:management')
            
        except Exception as e:
            messages.error(request, f'Error creating media content: {str(e)}')
    
    categories = ServiceCategory.objects.all()
    context = {
        'categories': categories,
        'content_types': MediaContent.CONTENT_TYPE_CHOICES,
        'status_choices': MediaContent.STATUS_CHOICES,
    }
    
    return render(request, 'media/create_media.html', context)

@login_required
@user_passes_test(is_staff_user)
def media_edit_view(request, media_id):
    """Edit existing media content"""
    media_content = get_object_or_404(MediaContent, id=media_id)
    
    if request.method == 'POST':
        try:
            media_content.title = request.POST.get('title')
            media_content.description = request.POST.get('description', '')
            media_content.content_type = request.POST.get('content_type')
            media_content.status = request.POST.get('status', 'draft')
            media_content.youtube_video_id = request.POST.get('youtube_video_id', '')
            media_content.waystream_embed_url = request.POST.get('waystream_embed_url', '')
            media_content.video_url = request.POST.get('video_url', '')
            media_content.audio_url = request.POST.get('audio_url', '')
            media_content.thumbnail_url = request.POST.get('thumbnail_url', '')
            media_content.pastor = request.POST.get('pastor', '')
            media_content.scripture = request.POST.get('scripture', '')
            
            # Handle category
            category_id = request.POST.get('category')
            if category_id:
                try:
                    media_content.category = ServiceCategory.objects.get(id=category_id)
                except ServiceCategory.DoesNotExist:
                    media_content.category = None
            else:
                media_content.category = None
            
            # Handle scheduled start
            scheduled_start = request.POST.get('scheduled_start')
            if scheduled_start:
                try:
                    media_content.scheduled_start = timezone.datetime.fromisoformat(scheduled_start)
                except:
                    media_content.scheduled_start = None
            else:
                media_content.scheduled_start = None
            
            media_content.save()
            
            messages.success(request, f'Media content "{media_content.title}" updated successfully!')
            return redirect('media:management')
            
        except Exception as e:
            messages.error(request, f'Error updating media content: {str(e)}')
    
    categories = ServiceCategory.objects.all()
    context = {
        'media_content': media_content,
        'categories': categories,
        'content_types': MediaContent.CONTENT_TYPE_CHOICES,
        'status_choices': MediaContent.STATUS_CHOICES,
    }
    
    return render(request, 'media/edit_media.html', context)

@login_required
@user_passes_test(is_staff_user)
def media_delete_view(request, media_id):
    """Delete media content"""
    media_content = get_object_or_404(MediaContent, id=media_id)
    
    if request.method == 'POST':
        title = media_content.title
        media_content.delete()
        messages.success(request, f'Media content "{title}" deleted successfully!')
        return redirect('media:management')
    
    context = {
        'media_content': media_content,
    }
    
    return render(request, 'media/delete_confirm.html', context)

@csrf_exempt
@login_required
@user_passes_test(is_staff_user)
def toggle_live_status(request, media_id):
    """Toggle live status of media content"""
    if request.method == 'POST':
        try:
            media_content = get_object_or_404(MediaContent, id=media_id, content_type='live')
            
            if media_content.is_live:
                # End the stream
                media_content.is_live = False
                media_content.actual_end = timezone.now()
                status_message = 'Stream ended successfully'
            else:
                # Start the stream
                media_content.is_live = True
                media_content.actual_start = timezone.now()
                media_content.actual_end = None
                status_message = 'Stream started successfully'
            
            media_content.save()
            
            return JsonResponse({
                'success': True,
                'is_live': media_content.is_live,
                'message': status_message
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_staff_user)
def media_analytics_view(request, media_id):
    """View analytics for specific media content"""
    media_content = get_object_or_404(MediaContent, id=media_id)
    
    # Get viewer statistics
    total_viewers = media_content.viewers.count()
    active_viewers = media_content.viewers.filter(is_active=True).count()
    
    # Get top viewers by duration
    top_viewers = media_content.viewers.order_by('-duration_watched')[:10]
    
    # Get recent activity
    recent_viewers = media_content.viewers.order_by('-started_at')[:20]
    
    context = {
        'media_content': media_content,
        'total_viewers': total_viewers,
        'active_viewers': active_viewers,
        'top_viewers': top_viewers,
        'recent_viewers': recent_viewers,
    }
    
    return render(request, 'media/analytics.html', context)
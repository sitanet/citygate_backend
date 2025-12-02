from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Avg
from .models import LiveStreamSession, StreamChat, StreamAnalytics
from media.models import MediaContent
import json

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_staff_user)
def streaming_dashboard_view(request):
    """Main streaming dashboard"""
    # Get active streams
    active_streams = MediaContent.objects.filter(content_type='live', is_live=True)
    
    # Get recent stream sessions
    recent_sessions = LiveStreamSession.objects.all().order_by('-started_at')[:10]
    
    # Get streaming statistics
    total_sessions = LiveStreamSession.objects.count()
    total_chat_messages = StreamChat.objects.count()
    
    # Current viewers across all streams
    current_viewers = MediaContent.objects.filter(
        content_type='live', 
        is_live=True
    ).aggregate(
        total=Count('viewers', filter=models.Q(viewers__is_active=True))
    )['total'] or 0
    
    context = {
        'active_streams': active_streams,
        'recent_sessions': recent_sessions,
        'total_sessions': total_sessions,
        'total_chat_messages': total_chat_messages,
        'current_viewers': current_viewers,
    }
    
    return render(request, 'streaming/dashboard.html', context)

@login_required
@user_passes_test(is_staff_user)
def stream_sessions_view(request):
    """View all streaming sessions"""
    sessions = LiveStreamSession.objects.all().order_by('-started_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        sessions = sessions.filter(ended_at__isnull=True)
    elif status_filter == 'completed':
        sessions = sessions.filter(ended_at__isnull=False)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        sessions = sessions.filter(media_content__title__icontains=search_query)
    
    # Pagination
    paginator = Paginator(sessions, 20)
    page_number = request.GET.get('page')
    sessions_page = paginator.get_page(page_number)
    
    context = {
        'sessions_page': sessions_page,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'streaming/sessions.html', context)

@login_required
@user_passes_test(is_staff_user)
def stream_session_detail_view(request, session_id):
    """View detailed information about a stream session"""
    session = get_object_or_404(LiveStreamSession, id=session_id)
    
    # Get chat messages for this session
    chat_messages = StreamChat.objects.filter(
        media_content=session.media_content,
        timestamp__gte=session.started_at
    )
    
    if session.ended_at:
        chat_messages = chat_messages.filter(timestamp__lte=session.ended_at)
    
    chat_messages = chat_messages.order_by('-timestamp')[:50]
    
    # Get viewer statistics
    viewers = session.media_content.viewers.filter(
        started_at__gte=session.started_at
    )
    
    if session.ended_at:
        viewers = viewers.filter(started_at__lte=session.ended_at)
    
    context = {
        'session': session,
        'chat_messages': chat_messages,
        'total_viewers': viewers.count(),
        'peak_viewers': session.peak_concurrent_viewers,
        'average_duration': viewers.aggregate(avg=Avg('duration_watched'))['avg'],
    }
    
    return render(request, 'streaming/session_detail.html', context)

@login_required
@user_passes_test(is_staff_user)
def chat_moderation_view(request):
    """Moderate chat messages"""
    messages_list = StreamChat.objects.all().order_by('-timestamp')
    
    # Filter by stream
    stream_id = request.GET.get('stream')
    if stream_id:
        messages_list = messages_list.filter(media_content_id=stream_id)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'deleted':
        messages_list = messages_list.filter(is_deleted=True)
    elif status_filter == 'active':
        messages_list = messages_list.filter(is_deleted=False)
    elif status_filter == 'pinned':
        messages_list = messages_list.filter(is_pinned=True)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        messages_list = messages_list.filter(message__icontains=search_query)
    
    # Pagination
    paginator = Paginator(messages_list, 30)
    page_number = request.GET.get('page')
    messages_page = paginator.get_page(page_number)
    
    # Get available streams for filtering
    streams = MediaContent.objects.filter(content_type='live').order_by('-created_at')
    
    context = {
        'messages_page': messages_page,
        'streams': streams,
        'selected_stream': stream_id,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'streaming/chat_moderation.html', context)

@csrf_exempt
@login_required
@user_passes_test(is_staff_user)
def moderate_chat_message(request, message_id):
    """Moderate a specific chat message"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            message = get_object_or_404(StreamChat, id=message_id)
            
            if action == 'delete':
                message.is_deleted = True
                message.moderated_by = request.user
                status_message = 'Message deleted successfully'
            elif action == 'restore':
                message.is_deleted = False
                message.moderated_by = request.user
                status_message = 'Message restored successfully'
            elif action == 'pin':
                message.is_pinned = True
                message.moderated_by = request.user
                status_message = 'Message pinned successfully'
            elif action == 'unpin':
                message.is_pinned = False
                message.moderated_by = request.user
                status_message = 'Message unpinned successfully'
            else:
                return JsonResponse({'success': False, 'message': 'Invalid action'})
            
            message.save()
            
            return JsonResponse({
                'success': True,
                'message': status_message,
                'is_deleted': message.is_deleted,
                'is_pinned': message.is_pinned,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_staff_user)
def streaming_analytics_view(request):
    """View streaming analytics and statistics"""
    from django.db.models import Sum, Avg, Count
    
    # Overall statistics
    total_sessions = LiveStreamSession.objects.count()
    completed_sessions = LiveStreamSession.objects.filter(ended_at__isnull=False).count()
    active_sessions = LiveStreamSession.objects.filter(ended_at__isnull=True).count()
    
    # Viewer statistics
    total_viewers = MediaContent.objects.filter(content_type='live').aggregate(
        total=Count('viewers')
    )['total'] or 0
    
    # Peak viewers across all sessions
    peak_viewers = LiveStreamSession.objects.aggregate(
        max_peak=models.Max('peak_concurrent_viewers')
    )['max_peak'] or 0
    
    # Chat statistics
    total_messages = StreamChat.objects.count()
    active_messages = StreamChat.objects.filter(is_deleted=False).count()
    
    # Recent activity
    recent_sessions = LiveStreamSession.objects.order_by('-started_at')[:5]
    
    # Top streams by viewers
    top_streams = MediaContent.objects.filter(content_type='live').annotate(
        viewer_count=Count('viewers')
    ).order_by('-viewer_count')[:10]
    
    context = {
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'active_sessions': active_sessions,
        'total_viewers': total_viewers,
        'peak_viewers': peak_viewers,
        'total_messages': total_messages,
        'active_messages': active_messages,
        'recent_sessions': recent_sessions,
        'top_streams': top_streams,
    }
    
    return render(request, 'streaming/analytics.html', context)
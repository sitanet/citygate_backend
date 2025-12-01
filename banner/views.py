from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Banner
from .forms import BannerForm

def can_manage_banners(user):
    return user.role in ['admin', 'banner'] or user.is_superuser

@login_required
@user_passes_test(can_manage_banners)
def banner_list(request):
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    
    banners = Banner.objects.all()
    
    if search_query:
        banners = banners.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if type_filter:
        banners = banners.filter(banner_type=type_filter)
        
    if status_filter:
        banners = banners.filter(status=status_filter)
    
    paginator = Paginator(banners, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'banner_types': Banner.BANNER_TYPE_CHOICES,
        'status_choices': Banner.STATUS_CHOICES,
    }
    return render(request, 'banner/banner_list.html', context)

@login_required
@user_passes_test(can_manage_banners)
def banner_create(request):
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid():
            banner = form.save(commit=False)
            banner.created_by = request.user
            banner.save()
            messages.success(request, 'Banner created successfully!')
            return redirect('banner:banner_list')
    else:
        form = BannerForm()
    
    return render(request, 'banner/banner_form.html', {'form': form, 'title': 'Create Banner'})

@login_required
@user_passes_test(can_manage_banners)
def banner_update(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banner updated successfully!')
            return redirect('banner:banner_list')
    else:
        form = BannerForm(instance=banner)
    
    return render(request, 'banner/banner_form.html', {
        'form': form, 
        'title': 'Update Banner',
        'banner': banner
    })

@login_required
@user_passes_test(can_manage_banners)
def banner_delete(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    
    if request.method == 'POST':
        title = banner.title
        banner.delete()
        messages.success(request, f'Banner "{title}" deleted successfully!')
        return redirect('banner:banner_list')
    
    return render(request, 'banner/banner_confirm_delete.html', {'banner': banner})
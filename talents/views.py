# Django shortcuts and utilities
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from django.views.generic import DetailView

# Django authentication
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

# Django messaging
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import logout as auth_logout

# Django ORM tools
from django.db.models import Q

# Local models
from .models import (
    Profile,
    Review,
    ContactMessage,
    Subscriber,
    BlogPost,
    Notification,
    Skill,
)

# Local forms
from .forms import (
    UserRegisterForm,
    UserUpdateForm,
    ProfileUpdateForm,
    ReviewForm,
)

# --- CORE PAGES ---

def home(request):
    # 1. Get 3 verified talents for the "Featured" section
    talents = Profile.objects.filter(is_verified=True)[:3] 
    
    # If no verified talents yet, just get any 3 (Safety fallback)
    if not talents:
        talents = Profile.objects.all()[:3]

    context = {
        'talents': talents
    }
    return render(request, 'talents/home.html', context)


def browse(request):
    """
    The main directory page with Search and Filtering.
    """
    # 1. Get all profiles initially
    talents = Profile.objects.all()
    skills = Skill.objects.all() # For the filter sidebar

    # 2. Search by Name, Bio, or Skill Name (Global Search)
    query = request.GET.get('q')
    if query:
        talents = talents.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(bio__icontains=query) |
            Q(skills__name__icontains=query)
        ).distinct()

    # 3. Filter by Location (Exact or Partial match)
    location_query = request.GET.get('location')
    if location_query:
        talents = talents.filter(location__icontains=location_query)

    # 4. Filter by Skill (Sidebar Checkbox)
    skill_filter = request.GET.get('skill')
    if skill_filter:
        talents = talents.filter(skills__name=skill_filter)

    context = {
        'talents': talents,
        'skills': skills,
    }
    return render(request, 'talents/browse.html', context)


def profile_detail(request, pk):
    """
    Shows a single talent profile and handles Review submissions.
    """
    talent = get_object_or_404(Profile, pk=pk)
    
    # 1. Handle Review Submission
    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.talent = talent
            review.author = request.user
            review.save()
            
            # Notification for the Talent
            Notification.objects.create(
                user=talent.user,
                message=f"You received a new {review.rating}-star review from {request.user.username}!"
            )
            
            messages.success(request, 'Review submitted successfully!')
            return redirect('profile_detail', pk=pk)
    else:
        form = ReviewForm()

    # 2. Calculate Average Rating
    reviews = talent.reviews.all().order_by('-created_at')
    avg_rating = 0
    if reviews.exists():
        total_stars = sum([r.rating for r in reviews])
        avg_rating = round(total_stars / reviews.count(), 1)

    context = {
        'talent': talent,
        'form': form,
        'reviews': reviews,
        'avg_rating': avg_rating
    }
    return render(request, 'talents/profile_detail.html', context)


# --- AUTHENTICATION & USER DASHBOARD ---

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # 1. Save the User
            user = form.save()
            
            # 2. AUTOMATICALLY Create a Profile for them
            Profile.objects.create(user=user)
            
            messages.success(request, "Account created! You can now login.")
            return redirect('login')
    else:
        form = UserRegisterForm()
    
    return render(request, 'talents/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                auth_login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'talents/login.html', {'form': form})


@login_required
def dashboard(request):
    profile = request.user.profile
    
    # 1. Calculate Profile Completeness (Gamification)
    completeness = 0
    if profile.bio: completeness += 20
    if profile.location: completeness += 20
    if profile.profile_pic and 'default.jpg' not in profile.profile_pic.url: completeness += 20
    if profile.cover_photo: completeness += 20
    if profile.skills.exists(): completeness += 20
    
    # 2. Get Recent Notifications
    notifications = request.user.notifications.all().order_by('-created_at')[:10]
    
    # 3. Get Reviews received by this user
    reviews = profile.reviews.all().order_by('-created_at')

    context = {
        'completeness': completeness,
        'notifications': notifications,
        'reviews': reviews,
    }
    return render(request, 'talents/dashboard.html', context)


@login_required
def profile_update(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            
            # Notification for the user
            Notification.objects.create(
                user=request.user,
                message="You successfully updated your profile details."
            )

            messages.success(request, 'Your profile has been updated!')
            return redirect('profile_detail', pk=request.user.profile.pk) 

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'talents/profile_update.html', context)


@login_required
def mark_notifications_read(request):
    """API endpoint to mark notifications as read via AJAX"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})


# --- COMMUNICATION & MARKETING ---

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        client_email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # 1. Save to DB (Keep this for records)
        ContactMessage.objects.create(name=name, email=client_email, subject=subject, message=message)
        
        # 2. SEND REAL EMAIL
        # This sends an email TO YOU (The Admin) telling you someone contacted the site.
        full_message = f"New message from {name} ({client_email}):\n\n{message}"
        
        try:
            send_mail(
                subject=f"TalentHub Inquiry: {subject}",
                message=full_message,
                from_email=settings.EMAIL_HOST_USER, # From your App Gmail
                recipient_list=[settings.EMAIL_HOST_USER], # To YOUR Gmail
                fail_silently=False,
            )
            messages.success(request, "Email sent successfully! We will contact you soon.")
        except Exception as e:
            messages.error(request, "Error sending email. Please try again later.")
            print(f"Email Error: {e}") # Prints error to your terminal for debugging

        # 3. Notification (Optional, keeps your dashboard logic working)
        if request.user.is_authenticated:
            Notification.objects.create(user=request.user, message="We received your message and will reply via email.")

        return redirect('contact')
        
    return render(request, 'talents/contact.html')


def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Check if already subscribed
            if Subscriber.objects.filter(email=email).exists():
                messages.warning(request, "You are already subscribed!")
            else:
                Subscriber.objects.create(email=email)
                messages.success(request, "Thanks for subscribing to our newsletter!")
                
                # Trigger Notification if user is logged in
                if request.user.is_authenticated:
                    Notification.objects.create(
                        user=request.user,
                        message="You have successfully subscribed to our newsletter."
                    )
    
    # Redirect back to the page the user was on
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# --- BLOG & STATIC PAGES ---

def blog(request):
    # Fetch all posts, newest first
    posts = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'talents/blog.html', {'posts': posts})


def blog_detail(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    # Get 3 other posts for "Related Articles"
    related_posts = BlogPost.objects.exclude(pk=pk).order_by('-created_at')[:3]
    
    context = {
        'post': post,
        'related_posts': related_posts
    }
    return render(request, 'talents/blog_detail.html', context)


def about(request):
    return render(request, 'talents/about.html')

def careers(request):
    return render(request, 'talents/careers.html')

def privacy(request):
    return render(request, 'talents/privacy.html')

def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')
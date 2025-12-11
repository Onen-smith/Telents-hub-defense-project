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



def home(request):
    talents = Profile.objects.filter(is_verified=True)[:3] 
    
    # If no verified talents yet, just get any 3
    if not talents:
        talents = Profile.objects.all()[:3]

    
    # 1. Get the search query from the URL (e.g., /?q=python)
    query = request.GET.get('q')

    # 2. Start with all talents
    talents = Profile.objects.all()

    print("Talents found:", talents)

    # 3. If a query exists, filter the list
    if query:
        talents = talents.filter(
            Q(user__username__icontains=query) |       # Search by Username
            Q(user__first_name__icontains=query) |     # Search by First Name
            Q(skills__name__icontains=query) |         # Search by Skill Name
            Q(location__icontains=query)               # Search by Location
        ).distinct() # distinct() prevents duplicates if multiple fields match

    context = {
        'talents': talents
    }
    
    return render(request, 'talents/home.html', context)


def profile_detail(request, pk):
    talent = get_object_or_404(Profile, pk=pk)
    
    # 1. Handle Review Submission
    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.talent = talent
            review.author = request.user
            review.save()
            messages.success(request, 'Review submitted successfully!')
            return redirect('profile_detail', pk=pk)
    else:
        form = ReviewForm()

    # 2. Calculate Average Rating (Great for Defense logic!)
    reviews = talent.reviews.all()
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

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # 1. Save the User
            user = form.save()
            
            # 2. AUTOMATICALLY Create a Profile for them
            Profile.objects.create(user=user)
            
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
                # This part is technically unreachable if form.is_valid() passes, 
                # but good for safety. The main error usually comes from form.is_valid() failing.
                messages.error(request, "Invalid username or password.")
        else:
            # THIS IS THE KEY PART:
            # If the form is NOT valid (meaning username/pass didn't match), add an error message.
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'talents/login.html', {'form': form})


# --- STATIC PAGES ---
def about(request):
    return render(request, 'talents/about.html')

def careers(request):
    return render(request, 'talents/careers.html')

def blog(request):
    return render(request, 'talents/blog.html')

def privacy(request):
    return render(request, 'talents/privacy.html')

# --- CONTACT PAGE LOGIC ---
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Save to DB
        ContactMessage.objects.create(name=name, email=email, subject=subject, message=message)
        messages.success(request, "Message sent! We'll get back to you shortly.")
        return redirect('contact')
        
    return render(request, 'talents/contact.html')

# --- NEWSLETTER LOGIC (Footer) ---
def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Check if already subscribed to prevent errors
            if Subscriber.objects.filter(email=email).exists():
                messages.warning(request, "You are already subscribed!")
            else:
                Subscriber.objects.create(email=email)
                messages.success(request, "Thanks for subscribing to our newsletter!")
    
    # Redirect back to the page the user was on
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def browse(request):
    # 1. Standard Search Logic (Same as home)
    query = request.GET.get('q')
    talents = Profile.objects.all()

    if query:
        talents = talents.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(skills__name__icontains=query) |
            Q(location__icontains=query)
        ).distinct()

    context = {
        'talents': talents
    }
    # 2. Render a specific 'browse' template
    return render(request, 'talents/browse.html', context)


def blog(request):
    # Fetch all posts, newest first
    posts = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'talents/blog.html', {'posts': posts})

def blog_detail(request, pk):
    # Fetch single post or 404
    post = get_object_or_404(BlogPost, pk=pk)
    
    # Get 3 other posts for "Related Articles" section
    related_posts = BlogPost.objects.exclude(pk=pk).order_by('-created_at')[:3]
    
    context = {
        'post': post,
        'related_posts': related_posts
    }
    return render(request, 'talents/blog_detail.html', context)

def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # ... existing subscription logic ...

        messages.success(request, 'Subscribed successfully!')

        # --- NOTIFICATION TRIGGER ---
        if request.user.is_authenticated:
            Notification.objects.create(
                user=request.user,
                message="You have successfully subscribed to our newsletter."
            )
        # ---------------------------

        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
def contact(request):
    if request.method == 'POST':
        # ... existing contact logic ...

        subject = request.POST.get('subject', '')

        # --- NOTIFICATION TRIGGER ---
        if request.user.is_authenticated:
            # Check if it was a Job Application or General Contact
            if "Job Application" in subject:
                msg = "Application submitted successfully! Our HR team will review it shortly."
            else:
                msg = "We received your message and will get back to you soon."

            Notification.objects.create(user=request.user, message=msg)
        # ---------------------------

        messages.success(request, 'Message sent!')
        return redirect('contact')

    return render(request, 'talents/contact.html')

from django.contrib.auth.decorators import login_required

@login_required
def mark_notifications_read(request):
    # Mark all unread notifications for this user as read
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

# 1. THE PROFILE DETAIL VIEW (Class Based View)
class ProfileDetailView(DetailView):
    model = Profile
    template_name = 'talents/profile_detail.html'
    context_object_name = 'object' 

    def get_object(self):
        # Ensure we fetch the profile by the Primary Key passed in URL
        return Profile.objects.get(pk=self.kwargs['pk'])

# 2. UPDATE YOUR EXISTING 'profile_update' FUNCTION
@login_required
def profile_update(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            
            messages.success(request, 'Your profile has been updated!')
            
            # --- CRITICAL FIX: Redirect to the Detail View ---
            return redirect('profile_detail', pk=request.user.profile.pk) 
            # -------------------------------------------------

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'talents/profile_update.html', context)

def browse(request):
    # 1. Get all profiles initially
    talents = Profile.objects.all()
    skills = Skill.objects.all() # For the filter sidebar

    # 2. Search by Name, Bio, or Skill Name
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

@login_required
def dashboard(request):
    profile = request.user.profile
    
    # 1. Calculate Profile Completeness
    completeness = 0
    if profile.bio: completeness += 20
    if profile.location: completeness += 20
    if profile.profile_pic and 'default.jpg' not in profile.profile_pic.url: completeness += 20
    if profile.cover_photo: completeness += 20
    if profile.skills.exists(): completeness += 20
    
    # 2. Get Recent Notifications (All of them, not just top 5)
    notifications = request.user.notifications.all().order_by('-created_at')[:10]
    
    # 3. Get Reviews received by this user
    reviews = profile.reviews.all().order_by('-created_at')

    context = {
        'completeness': completeness,
        'notifications': notifications,
        'reviews': reviews,
    }
    return render(request, 'talents/dashboard.html', context)
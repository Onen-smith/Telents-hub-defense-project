from datetime import date  # <--- FIXED: Specific import for blog dates

from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils import timezone  # <--- FIXED: Django's timezone for contracts
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Q, Avg, Max
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Sum  
from .models import Transaction
from .forms import DepositForm, WithdrawForm
import secrets # To generate unique references
from django.conf import settings
import requests



# Local Imports
from .models import Profile, Review, ContactMessage, SavedJob, Subscriber, BlogPost, Notification, Skill, Job, Proposal, Contract, Message, Conversation
from .forms import (
    CustomUserCreationForm, 
    UserUpdateForm, 
    ProfileUpdateForm, 
    ReviewForm,
    JobForm,
    ProposalForm
)

# --- CORE PAGES ---

def home(request):
    # Fetch 3 recent jobs
    recent_jobs = Job.objects.filter(is_active=True).order_by('-created_at')[:3]

    # --- CHANGED: Fetch ALL profiles & PRINT them ---
    top_talents = Profile.objects.all().order_by('-id')[:4]

    # DEBUG: This will show up in your terminal (black box)
    print(f"DEBUG: Found {top_talents.count()} profiles.")
    for t in top_talents:
        print(f" - Profile: {t.user.username}")

    # Simple Stats Counter
    stats = {
        'jobs_count': Job.objects.filter(is_active=True).count(),
        'talents_count': Profile.objects.count(),
    }

    context = {
        'recent_jobs': recent_jobs,
        'top_talents': top_talents,  # <--- KEY NAME IS 'top_talents'
        'stats': stats
    }
    return render(request, 'talents/home.html', context)


def browse(request):
    # 1. Fetch profiles (Renamed variable to match template)
    # Removing 'onboarding_complete=True' for now so you can see your test profiles
    profiles = Profile.objects.select_related('user').prefetch_related('skills').filter(role='freelancer').order_by(
        '-created_at')

    skills = Skill.objects.all()

    # 2. Search Logic
    query = request.GET.get('q')
    if query:
        profiles = profiles.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(bio__icontains=query) |
            Q(skills__name__icontains=query) |
            Q(headline__icontains=query)
        ).distinct()

    # 3. Location Filter
    location_query = request.GET.get('location')
    if location_query:
        profiles = profiles.filter(location__icontains=location_query)

    # 4. Skill Filter
    skill_filter = request.GET.get('skill')
    if skill_filter:
        profiles = profiles.filter(skills__name=skill_filter)

    context = {
        'profiles': profiles,  # <--- FIXED: Changed from 'talents' to 'profiles'
        'skills': skills,
        'search_query': query
    }
    return render(request, 'talents/browse.html', context)

def profile_detail(request, slug):
    profile = get_object_or_404(Profile.objects.select_related('user'), slug=slug)
    
    # Handle Review Submission
    if request.method == 'POST' and request.user.is_authenticated:
        if request.user == profile.user:
            messages.error(request, "You cannot review your own profile.")
            return redirect('profile_detail', slug=slug)

        form = ReviewForm(request.POST)
        if form.is_valid():
            try:
                review = form.save(commit=False)
                review.talent = profile
                review.author = request.user
                review.save()
                
                Notification.objects.create(
                    user=profile.user,
                    message=f"New {review.rating}★ review from {request.user.username}!"
                )
                messages.success(request, 'Review submitted successfully!')
            except Exception: 
                messages.error(request, "You have already reviewed this talent.")
            
            return redirect('profile_detail', slug=slug)
    else:
        form = ReviewForm()

    reviews = profile.reviews.select_related('author').order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'profile': profile,
        'form': form,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'review_count': reviews.count()
    }
    return render(request, 'talents/profile_detail.html', context)

# --- AUTHENTICATION ---

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, "That username is taken. Please choose another.")
            return redirect('register')

        try:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Account created! Welcome to the hub.")
            return redirect('dashboard') 

        except Exception as e:
            messages.error(request, "An error occurred during signup.")
            return redirect('register')

    return render(request, 'talents/register.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
    else:
        form = AuthenticationForm()

    return render(request, 'talents/login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

# --- DASHBOARD & PROFILE MANAGEMENT ---

@login_required
def dashboard(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    completeness = 0
    if profile.bio: completeness += 20
    if profile.location: completeness += 20
    if profile.profile_pic and 'default.jpg' not in profile.profile_pic.url: completeness += 20
    if profile.cover_photo: completeness += 10
    if profile.skills.exists(): completeness += 30
    
    notifications = request.user.notifications.all().order_by('-created_at')[:5]
    reviews = profile.reviews.select_related('author').order_by('-created_at')

    context = {
        'profile': profile,
        'completeness': completeness,
        'notifications': notifications,
        'reviews': reviews,
    }
    return render(request, 'talents/dashboard.html', context)

@login_required
def complete_onboarding(request):
    if request.method == 'POST':
        profile = request.user.profile
        
        profile.role = request.POST.get('role', 'freelancer')
        profile.headline = request.POST.get('headline')
        profile.location = request.POST.get('location')
        profile.bio = request.POST.get('bio', '')
        profile.company_name = request.POST.get('company_name', '')
        profile.project_link = request.POST.get('project_link', '')
        
        rate = request.POST.get('hourly_rate')
        if rate and rate.strip():
            profile.hourly_rate = rate
        
        years = request.POST.get('years_experience')
        if years and years.strip():
            profile.years_experience = int(years)

        skills_input = request.POST.get('skills')
        if skills_input:
            profile.skills.clear() 
            for skill_name in skills_input.split(','):
                skill_name = skill_name.strip()
                if skill_name:
                    skill, _ = Skill.objects.get_or_create(name__iexact=skill_name, defaults={'name': skill_name})
                    profile.skills.add(skill)

        profile.onboarding_complete = True
        profile.save()

        dashboard_url = reverse('dashboard')
        return redirect(f"{dashboard_url}?welcome=true")

    return redirect('dashboard')

@login_required
def profile_update(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile_detail', slug=request.user.profile.slug) 
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'talents/profile_update.html', context)

# --- NOTIFICATIONS UTILS ---

@login_required
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

@login_required
def all_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read functionality
    if request.method == "POST" and 'mark_read' in request.POST:
        notifications.update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('notifications')
        
    notifications.update(is_read=True)
    return render(request, 'talents/notifications.html', {'notifications': notifications})

# --- BLOG SECTION ---

BLOG_POSTS = [
    {
        'id': 1,
        'title': "The Future of Freelancing in Nigeria: 2026 Outlook",
        'slug': "future-of-freelancing-nigeria-2026",
        'excerpt': "Explore the emerging trends...",
        'content': """<p class="lead">The freelance landscape is evolving rapidly.</p>""",
        'category': "Industry Trends",
        'author': "Emmanuel Onen",
        'date': date(2026, 1, 15), # <--- FIXED: using date()
        'image': "https://images.unsplash.com/photo-1522071820081-009f0129c71c?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
        'featured': True
    },
    {
        'id': 2,
        'title': "5 Soft Skills Every Remote Developer Needs",
        'slug': "5-soft-skills-remote-developers",
        'excerpt': "Technical skills get you the job, but soft skills keep you there.",
        'content': "<p>Content goes here...</p>",
        'category': "Career Advice",
        'author': "Sarah Jenkins",
        'date': date(2026, 1, 10),
        'image': "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
        'featured': False
    },
    {
        'id': 3,
        'title': "How to Craft a Winning Proposal on TalentHub",
        'slug': "craft-winning-proposal-talenthub",
        'excerpt': "Stop sending generic cover letters.",
        'content': "<p>Content goes here...</p>",
        'category': "Platform Tips",
        'author': "TalentHub Team",
        'date': date(2026, 1, 5),
        'image': "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
        'featured': False
    },
    {
        'id': 4,
        'title': "Setting Your Rates: A Guide for New Freelancers",
        'slug': "setting-your-rates-guide",
        'excerpt': "Undervaluing your work is a common mistake.",
        'content': "<p>Content goes here...</p>",
        'category': "Finance",
        'author': "Michael Adebayo",
        'date': date(2025, 12, 28),
        'image': "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
        'featured': False
    }
]

def blog(request):
    featured_post = next((post for post in BLOG_POSTS if post['featured']), None)
    other_posts = [post for post in BLOG_POSTS if not post['featured']]
    context = {'featured_post': featured_post, 'posts': other_posts}
    return render(request, 'talents/blog.html', context)

def blog_detail(request, pk):
    post = next((item for item in BLOG_POSTS if item["id"] == pk), None)
    if not post:
        return redirect('blog')
    return render(request, 'talents/blog_detail.html', {'post': post})

# --- STATIC PAGES ---

def contact(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name'), 
            email=request.POST.get('email'), 
            subject=request.POST.get('subject'), 
            message=request.POST.get('message')
        )
        messages.success(request, "Message sent! We'll get back to you shortly.")
        return redirect('contact')
    return render(request, 'talents/contact.html')

def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not Subscriber.objects.filter(email=email).exists():
            Subscriber.objects.create(email=email)
            messages.success(request, "Subscribed successfully!")
        else:
            messages.info(request, "You are already subscribed.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def about(request): return render(request, 'talents/about.html')
def careers(request): return render(request, 'talents/careers.html')
def privacy(request): return render(request, 'talents/privacy.html')

# --- JOBS & MARKETPLACE (Consolidated) ---


@login_required
def job_list(request):
    jobs = Job.objects.filter(is_active=True).order_by('-created_at')
    
    # --- UPGRADE: Advanced Search & Filtering ---
    query = request.GET.get('q')
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(skills_required__name__icontains=query) # Search by Skill Name too
        ).distinct()

    # Filter by Job Type (Fixed/Hourly)
    job_type = request.GET.get('type')
    if job_type:
        jobs = jobs.filter(job_type=job_type)

    context = {
        'jobs': jobs, 
        'job_count': jobs.count(),
        'saved_job_ids': request.user.saved_jobs.values_list('job_id', flat=True) # For the bookmark icon
    }
    return render(request, 'talents/job_list.html', context)

def job_detail(request, slug):
    job = get_object_or_404(Job, slug=slug)
    has_applied = False
    if request.user.is_authenticated:
        # Check against both the old M2M and new Proposal model for thoroughness
        has_applied = Proposal.objects.filter(job=job, freelancer=request.user).exists()
    
    context = {'job': job, 'has_applied': has_applied}
    return render(request, 'talents/job_detail.html', context)


def apply_to_job(request, slug):
    job = get_object_or_404(Job, slug=slug)

    if job.client == request.user:
        messages.error(request, "You cannot apply to your own job.")
        return redirect('job_detail', slug=slug)

    # Check if already applied
    if Proposal.objects.filter(job=job, freelancer=request.user).exists():
        messages.warning(request, "You have already sent a proposal.")
        return redirect('job_detail', slug=slug)

    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.job = job
            proposal.freelancer = request.user
            proposal.save()
            
            # Compatibility with legacy field
            job.applicants.add(request.user) 
            
            messages.success(request, "Proposal sent successfully!")
            return redirect('job_detail', slug=slug)
    else:
        form = ProposalForm(initial={'bid_amount': job.budget})

    return render(request, 'talents/apply_job.html', {'form': form, 'job': job})

@login_required
def my_jobs(request):
    # Jobs posted by the user
    posted_jobs = Job.objects.filter(client=request.user).prefetch_related('applicants__profile').order_by('-created_at')
    
    # Jobs user applied to (using Proposal model)
    proposals = Proposal.objects.filter(freelancer=request.user).select_related('job', 'job__client').order_by('-created_at')
    
    context = {
        'posted_jobs': posted_jobs,
        'proposals': proposals # Using proposals instead of 'applied_jobs' for better data
    }
    return render(request, 'talents/my_jobs.html', context)

@login_required
def manage_job(request, slug):
    job = get_object_or_404(Job, slug=slug)
    
    if request.user != job.client:
        return redirect('dashboard')

    # Fetch full proposals
    proposals = Proposal.objects.filter(job=job).select_related('freelancer__profile')

    return render(request, 'talents/manage_job.html', {'job': job, 'proposals': proposals})


@login_required
def create_contract(request, proposal_id):
    # 1. Get the Proposal and Job
    proposal = get_object_or_404(Proposal, id=proposal_id)
    job = proposal.job
    amount = proposal.bid_amount

    # Security: Ensure only the client can hire
    if request.user != job.client:
        messages.error(request, "You do not have permission to hire for this job.")
        return redirect('dashboard')

    # 2. Calculate Wallet Balance
    deposits = Transaction.objects.filter(
        user=request.user,
        transaction_type='deposit',
        status='success'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    withdrawals = Transaction.objects.filter(
        user=request.user,
        transaction_type='withdrawal',
        status='success'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    escrow_holds = Transaction.objects.filter(
        user=request.user,
        transaction_type='escrow_hold',
        status='success'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    current_balance = deposits - withdrawals - escrow_holds

    # 3. Check for Insufficient Funds
    if current_balance < amount:
        messages.error(request, f"Insufficient funds. You need ₦{amount:,.2f} but only have ₦{current_balance:,.2f}.")
        return redirect('wallet')

    # 4. Create the Contract
    contract = Contract.objects.create(
        job=job,
        client=request.user,
        freelancer=proposal.freelancer,
        proposal=proposal,
        agreed_price=amount,
        status='active'
    )

    # 5. Lock the Money (Escrow Hold)
    Transaction.objects.create(
        user=request.user,
        amount=amount,
        transaction_type='escrow_hold',
        status='success',
        contract=contract,
        reference=f"ESCROW-{contract.id}-{secrets.token_hex(4)}"
    )

    # 6. Update Proposal & Job Status
    proposal.status = 'accepted'
    proposal.save()

    # Optional: Close the job so no one else applies
    job.is_active = False
    job.save()

    messages.success(request, f"Hired {proposal.freelancer.username}! Funds have been moved to escrow.")

    # --- FIX: Use 'pk' here to match your urls.py ---
    return redirect('contract_detail', pk=contract.id)
@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    
    if request.user != contract.client and request.user != contract.freelancer:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    if request.method == 'POST' and 'release_funds' in request.POST:
        if request.user == contract.client and contract.status == 'active':
            # 1. Update contract status
            contract.status = 'completed'
            contract.end_date = timezone.now()
            contract.save()

            # 2. Release funds from escrow for the client
            Transaction.objects.create(
                user=contract.client,
                amount=-contract.agreed_price,
                transaction_type='escrow_release',
                status='success',
                contract=contract,
                reference=f"RELEASE-{contract.id}-{secrets.token_hex(4)}"
            )

            # 3. Add funds to the freelancer's wallet
            Transaction.objects.create(
                user=contract.freelancer,
                amount=contract.agreed_price,
                transaction_type='fund_received',
                status='success',
                contract=contract,
                reference=f"PAYOUT-{contract.id}-{secrets.token_hex(4)}"
            )

            messages.success(request, f"Funds released to {contract.freelancer.username} successfully!")
            return redirect('contract_detail', pk=pk)

    return render(request, 'talents/contract_detail.html', {'contract': contract})

@login_required
def notifications(request):
    # Consolidating notifications view (it was defined twice in your file)
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    if request.method == "POST" and 'mark_read' in request.POST:
        notifs.update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('notifications')

    return render(request, 'talents/notifications.html', {'notifications': notifs})

@login_required
def inbox(request):
    # Find all conversations the user is a participant in
    conversations = Conversation.objects.filter(participants=request.user).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')

    context = {
        'conversations': conversations
    }
    return render(request, 'talents/inbox.html', context)

@login_required
def chat_detail(request, username):
    other_user = get_object_or_404(User, username=username)
    
    # Try to find an existing conversation or create a new one
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user).first()
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    # Handle message sending
    if request.method == "POST":
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                recipient=other_user,
                content=content
            )
            return redirect('chat_detail', username=username)

    # Mark messages from the other user as read
    Message.objects.filter(conversation=conversation, sender=other_user, read_at__isnull=True).update(read_at=timezone.now())
    
    # Fetch chat history for this conversation
    messages = Message.objects.filter(conversation=conversation).order_by('created_at')
    
    context = {
        'other_user': other_user,
        'chat_messages': messages,
        'conversation': conversation
    }
    return render(request, 'talents/inbox.html', context)

@login_required
def post_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.client = request.user
            job.save()
            
            # --- UPGRADE: Handle comma-separated skills input ---
            # If your form has a text field named 'skills_required' (or similar)
            skills_input = request.POST.get('skills_required') 
            if skills_input:
                job.skills_required.clear()
                for skill_name in skills_input.split(','):
                    skill_name = skill_name.strip()
                    if skill_name:
                        # Get or Create the skill instantly
                        skill, _ = Skill.objects.get_or_create(name__iexact=skill_name, defaults={'name': skill_name})
                        job.skills_required.add(skill)
            else:
                form.save_m2m() # Fallback to standard handling

            messages.success(request, "Job updated successfully!")
            return redirect('job_list')
    else:
        form = JobForm()
    return render(request, 'talents/post_job.html', {'form': form})


@login_required
def wallet(request):
    # --- 1. HANDLE POST REQUESTS (Forms) ---
    if request.method == 'POST':
        # --- Handle Deposit (Redirects to Paystack) ---
        if 'deposit_btn' in request.POST:
            deposit_form = DepositForm(request.POST)
            if deposit_form.is_valid():
                transaction = deposit_form.save(commit=False)
                transaction.user = request.user
                transaction.transaction_type = 'deposit'
                transaction.status = 'pending'  # Waiting for Paystack

                # Generate unique reference
                ref = secrets.token_urlsafe(10)
                transaction.reference = ref
                transaction.save()

                return redirect('payment_checkout', reference=ref)

        # --- Handle Withdrawal ---
        elif 'withdraw_btn' in request.POST:
            withdraw_form = WithdrawForm(request.POST)
            if withdraw_form.is_valid():
                amount = withdraw_form.cleaned_data['amount']

                # Calculate real available balance (must exclude escrow money)
                deposits = \
                Transaction.objects.filter(user=request.user, transaction_type='deposit', status='success').aggregate(
                    Sum('amount'))['amount__sum'] or 0
                withdrawals = Transaction.objects.filter(user=request.user, transaction_type='withdrawal',
                                                         status='success').aggregate(Sum('amount'))['amount__sum'] or 0
                escrow_holds = Transaction.objects.filter(user=request.user, transaction_type='escrow_hold',
                                                          status='success').aggregate(Sum('amount'))['amount__sum'] or 0

                current_balance = deposits - withdrawals - escrow_holds

                if amount > current_balance:
                    messages.error(request, "Insufficient Funds! You cannot withdraw money that is held in escrow.")
                else:
                    transaction = withdraw_form.save(commit=False)
                    transaction.user = request.user
                    transaction.transaction_type = 'withdrawal'
                    transaction.status = 'success'
                    transaction.save()
                    messages.success(request, f"Successfully withdrew ₦{amount:,.2f}")
                    return redirect('wallet')

    # --- 2. PREPARE DATA FOR GET REQUEST (Display) ---
    deposits = Transaction.objects.filter(user=request.user, transaction_type='deposit', status='success').aggregate(
        Sum('amount'))['amount__sum'] or 0
    withdrawals = \
    Transaction.objects.filter(user=request.user, transaction_type='withdrawal', status='success').aggregate(
        Sum('amount'))['amount__sum'] or 0
    escrow_holds = \
    Transaction.objects.filter(user=request.user, transaction_type='escrow_hold', status='success').aggregate(
        Sum('amount'))['amount__sum'] or 0

    # The TRUE balance available to the user
    available_balance = deposits - withdrawals - escrow_holds

    # Get History
    history = Transaction.objects.filter(user=request.user).order_by('-created_at')[:10]

    # Initialize Forms
    deposit_form = DepositForm()
    withdraw_form = WithdrawForm()

    context = {
        'balance': available_balance,
        'transactions': history,
        'deposit_form': deposit_form,
        'withdraw_form': withdraw_form
    }
    return render(request, 'talents/wallet.html', context)

@login_required
def verify_identity(request):
    return render(request, 'talents/verify_identity.html')

@login_required
def leave_review(request):
    if request.method == 'POST':
        # Here you would save the Review model
        messages.success(request, "Review submitted successfully!")
        return redirect('dashboard')
        
    # Mock data for the preview
    context = {
        'freelancer_name': 'Sarah Jenkins',
        'job_title': 'E-Commerce Website Redesign'
    }
    return render(request, 'talents/leave_review.html', context)

def public_profile(request, username):
    # Get the user by username (or 404 if not found)
    profile_user = get_object_or_404(User, username=username)
    return render(request, 'talents/public_profile.html', {'profile_user': profile_user})


@login_required
def toggle_save_job(request, slug):
    job = get_object_or_404(Job, slug=slug)
    saved_job = SavedJob.objects.filter(user=request.user, job=job).first()
    
    if saved_job:
        saved_job.delete()
        messages.info(request, "Job removed from saved items.")
    else:
        SavedJob.objects.create(user=request.user, job=job)
        messages.success(request, "Job saved successfully!")
        
    return redirect(request.META.get('HTTP_REFERER', 'job_list'))

@login_required
def settings_view(request):
    return render(request, 'talents/settings.html')

@login_required
def payment_checkout(request, reference):
    transaction = get_object_or_404(Transaction, reference=reference, user=request.user)
    
    context = {
        'transaction': transaction,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        'amount_value': int(transaction.amount * 100), # Paystack expects Kobo (Naira * 100)
        'email': request.user.email
    }
    return render(request, 'talents/payment_checkout.html', context)

@login_required
def verify_payment(request, reference):
    transaction = get_object_or_404(Transaction, reference=reference, user=request.user)
    
    # 1. Check if already verified
    if transaction.status == 'success':
        return redirect('wallet')
    
    # 2. Call Paystack API to verify status
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(url, headers=headers)
        response_data = response.json()
        
        if response_data['status'] is True and response_data['data']['status'] == 'success':
            # Payment Verified!
            transaction.status = 'success'
            transaction.save()
            messages.success(request, f"Payment Verified! ₦{transaction.amount} added to your wallet.")
        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, "Payment verification failed.")
            
    except requests.exceptions.RequestException:
        messages.error(request, "Network error verifying payment.")

    return redirect('wallet')

@login_required
def edit_job(request, slug):
    # 1. Get the job (Security: Ensure only the owner can edit)
    job = get_object_or_404(Job, slug=slug, client=request.user)

    if request.method == 'POST':
        # 2. Load the form with existing data (instance=job)
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()

            # If you are using the tag system I gave you earlier:
            skills_input = request.POST.get('skills_required')
            if skills_input:
                job.skills_required.clear()
                for skill_name in skills_input.split(','):
                    skill_name = skill_name.strip()
                    if skill_name:
                        # Get or Create the skill instantly
                        skill, _ = Skill.objects.get_or_create(name__iexact=skill_name, defaults={'name': skill_name})
                        job.skills_required.add(skill)
            else:
                form.save_m2m() # Fallback to standard handling

            messages.success(request, "Job updated successfully!")
            return redirect('job_detail', slug=job.slug)
    else:
        # 3. Pre-fill the form with the job's current details
        form = JobForm(instance=job)

    # 4. Reuse the 'post_job.html' template
    return render(request, 'talents/post_job.html', {
        'form': form,
        'title': 'Edit Job'  # Pass a title variable
    })

@login_required
def hire_freelancer(request, freelancer_id):
    freelancer = get_object_or_404(User, id=freelancer_id)
    client_jobs = Job.objects.filter(client=request.user, is_active=True)

    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        job = get_object_or_404(Job, id=job_id, client=request.user)
        
        # Create a proposal on behalf of the client
        proposal, created = Proposal.objects.get_or_create(
            job=job,
            freelancer=freelancer,
            defaults={'bid_amount': job.budget, 'cover_letter': 'Hired directly by client.'}
        )
        
        return redirect('create_contract', proposal_id=proposal.id)

    context = {
        'freelancer': freelancer,
        'client_jobs': client_jobs,
    }
    return render(request, 'talents/hire_freelancer.html', context)
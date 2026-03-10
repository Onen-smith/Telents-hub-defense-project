from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.utils import timezone
import uuid 

# 1. Abstract Base Model (Professional Standard)
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# 2. Skill Model
class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    
    def __str__(self):
        return self.name

# 3. Profile Model (UPDATED)
class Profile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # Identity & SEO
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    # --- Role Selection ---
    ROLE_CHOICES = [
        ('freelancer', 'Freelancer'), 
        ('client', 'Client')
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='freelancer', db_index=True)

    # Basic Info
    headline = models.CharField(max_length=200, blank=True, null=True, help_text="e.g. Senior Python Developer") # <--- ADDED THIS FIELD
    phone_number = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, help_text="City, State", db_index=True)
    
    bio = models.TextField(blank=True, help_text="Describe your services")
    
    # Visuals
    profile_pic = models.ImageField(upload_to='profile_pics/', default='default.jpg')
    cover_photo = models.ImageField(upload_to='cover_photos/', blank=True, null=True)
    
    AVAILABILITY_CHOICES = [
        ('available', 'Available for work'),
        ('open', 'Open to offers'),
        ('busy', 'Currently busy'),
    ]
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='available')

    ENGLISH_CHOICES = [
        ('basic', 'Basic'),
        ('conversational', 'Conversational'),
        ('fluent', 'Fluent'),
        ('native', 'Native/Bilingual'),
    ]
    english_level = models.CharField(max_length=20, choices=ENGLISH_CHOICES, default='fluent')
    
    # --- EXPERIENCE ---
    years_experience = models.PositiveIntegerField(default=0)
    company_name = models.CharField(max_length=100, blank=True)
    project_link = models.URLField(blank=True)
    
    # --- EXPERTISE ---
    tools = models.CharField(max_length=255, blank=True, help_text="Comma separated tools (e.g. Jira, Figma)")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name='profiles')
    
    # Status
    is_verified = models.BooleanField(default=False)
    onboarding_complete = models.BooleanField(default=False)

    # Helper method to check if profile is "Complete"
    def is_complete(self):
        # Returns True if essential fields are filled
        return all([self.headline, self.location, self.user.email, self.skills.exists()])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.user.username)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('profile_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.role})"

# 4. Review Model
class Review(TimeStampedModel):
    talent = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    rating = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()

    class Meta:
        unique_together = ('talent', 'author')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating} Stars for {self.talent} by {self.author}"

# 5. Contact Message
class ContactMessage(TimeStampedModel):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()

    def __str__(self):
        return f"Message from {self.name}"

# 6. Newsletter Subscriber
class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

# 7. Blog Post
class BlogPost(TimeStampedModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.CharField(max_length=50, default='News', db_index=True)
    image_url = models.URLField(blank=True, null=True) 
    excerpt = models.TextField(help_text="Short summary for the card")
    content = models.TextField(help_text="Full article content")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

# 8. Notification
class Notification(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}"
    
# 9. Job Listing Model (The Core of the Platform)
class Job(TimeStampedModel):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    
    # Job Details
    JOB_TYPE_CHOICES = [
        ('fixed', 'Fixed Price'),
        ('hourly', 'Hourly Rate'),
    ]
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='fixed')
    budget = models.DecimalField(max_digits=10, decimal_places=2, help_text="Budget or Hourly Rate")
    
    # Requirements
    skills_required = models.ManyToManyField(Skill, related_name='jobs')
    experience_level = models.CharField(max_length=20, choices=[
        ('entry', 'Entry Level'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert')
    ], default='intermediate')
    
    # Status
    is_active = models.BooleanField(default=True)
    applicants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='applied_jobs', blank=True)

    # --- THIS IS THE CRITICAL FIX ---
    def save(self, *args, **kwargs):
        if not self.slug:
            # We add a random UUID to ensure the slug is ALWAYS unique and never empty
            # Example: "python-developer-a1b2c3d4"
            self.slug = f"{slugify(self.title)}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
# 10. PROPOSAL (Replaces simple applicants list)
class Proposal(TimeStampedModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='proposals')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='my_proposals')
    cover_letter = models.TextField()
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Proposed price")
    estimated_days = models.PositiveIntegerField(default=7, help_text="Days to complete")
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('job', 'freelancer') # One proposal per job per user

    def __str__(self):
        return f"{self.freelancer.username} -> {self.job.title}"

# 11. CONTRACT (The official agreement)
class Contract(TimeStampedModel):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='contract')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_contracts')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='freelancer_contracts')
    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE)
    
    agreed_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"Contract: {self.job.title}"

class Conversation(TimeStampedModel):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    
    def __str__(self):
        return f"Chat {self.id}"

# Update Message model to link to Conversation
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp'] # Oldest first (like a real chat log)

    def __str__(self):
        return f"From {self.sender} to {self.recipient}"
    
# 12. SAVED JOBS (Bookmarking System) -- [NEW ADDITION]
class SavedJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job') # Prevent saving the same job twice

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"


# Add this to the bottom of talents/models.py

class Transaction(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2) # Supports up to 9,999,999,999.99

    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('escrow_hold', 'Escrow Hold'),  # Money held during project
        ('escrow_release', 'Escrow Release'),  # Money paid to freelancer
        ('refund', 'Refund'),
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    contract = models.ForeignKey('Contract', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='pending') # pending, success, failed
    reference = models.CharField(max_length=100, blank=True, null=True) # For Paystack/Flutterwave Ref IDs

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - ₦{self.amount}"